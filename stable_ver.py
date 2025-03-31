import streamlit as st
import json
import os
import random
import datetime
import time
import google.generativeai as genai
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# File paths
DATA_FILE = "data.json"
HISTORY_FILE = "quiz_history.json"
EXPLANATIONS_FILE = "explanations.json"

# Function to load quiz data
def load_quiz_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        st.error(f"Error loading quiz data: {e}")
        return None

# Function to load quiz history
def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"history": []}
    except Exception as e:
        st.warning(f"Error loading history: {e}")
        return {"history": []}

# Function to save quiz history
def save_history(history):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error saving history: {e}")

# Function to load explanations
def load_explanations():
    try:
        if os.path.exists(EXPLANATIONS_FILE):
            with open(EXPLANATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        st.warning(f"Error loading explanations: {e}")
        return {}

# Function to save explanations
def save_explanations(explanations):
    try:
        with open(EXPLANATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(explanations, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error saving explanations: {e}")

# Function to get explanation with caching
def get_explanation(question, answer, options, question_id, course_id, quiz_set):
    # Create a unique key for this explanation
    explanation_key = f"{course_id}_{quiz_set}_{question_id}"
    
    # Try to load from saved explanations first
    explanations = load_explanations()
    
    if explanation_key in explanations:
        return explanations[explanation_key]
    
    # If not found, generate with API
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""Giải thích khái niệm sau chi tiết bằng tiếng việt:
        
Question: {question}
Options:
{options}
Correct Answer: {answer}

Provide a comprehensive explanation of why this answer is correct, including relevant theories, definitions, 
and examples if applicable. If this is a math problem, please explain the solution step by step.
"""
        response = model.generate_content(prompt)
        explanation = response.text
        
        # Save to file for future use
        explanations[explanation_key] = explanation
        save_explanations(explanations)
        
        return explanation
    except Exception as e:
        st.error(f"Error generating explanation: {e}")
        return "Sorry, could not generate explanation. Please try again later."

# Function to format duration
def format_duration(seconds):
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes}m {remaining_seconds}s"

# Function to shuffle options while maintaining A, B, C, D labels
def shuffle_options(questions):
    shuffled_questions = []
    
    for question in questions:
        # Create a copy of the question to avoid modifying the original
        q_copy = question.copy()
        
        # Get original options and their keys
        options = list(question["options"].items())
        
        # Shuffle the option values (content)
        option_values = [value for _, value in options]
        random.shuffle(option_values)
        
        # Map original option keys (A, B, C, D) to shuffled values
        shuffled_options = {}
        original_to_shuffled = {}
        
        for i, (key, _) in enumerate(options):
            shuffled_options[key] = option_values[i]
            # Find which original key this value came from
            for orig_key, orig_value in question["options"].items():
                if option_values[i] == orig_value:
                    original_to_shuffled[orig_key] = key
                    break
        
        # Update the options
        q_copy["options"] = shuffled_options
        
        # Update the answer_number based on the shuffled positions
        shuffled_answer_number = [original_to_shuffled[ans] for ans in question["answer_number"]]
        q_copy["answer_number"] = shuffled_answer_number
        
        shuffled_questions.append(q_copy)
    
    return shuffled_questions

# Initialize session state
def init_session_state():
    # All possible routes
    routes = ['quiz', 'result', 'history', 'history_view']
    
    if 'route' not in st.session_state:
        st.session_state.route = 'quiz'
    
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = load_quiz_data()
    
    if 'history' not in st.session_state:
        st.session_state.history = load_history()
    
    if 'current_course' not in st.session_state:
        st.session_state.current_course = None
    
    if 'current_quiz_set' not in st.session_state:
        st.session_state.current_quiz_set = None
    
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    
    if 'score' not in st.session_state:
        st.session_state.score = 0
    
    if 'shuffled_questions' not in st.session_state:
        st.session_state.shuffled_questions = None
    
    if 'quiz_start_time' not in st.session_state:
        st.session_state.quiz_start_time = time.time()
    
    if 'history_view_index' not in st.session_state:
        st.session_state.history_view_index = None

# Function to change route
def navigate_to(route):
    st.session_state.route = route
    st.rerun()

# Main function
def main():
    # Set up the page
    st.set_page_config(page_title="FE Learning", page_icon="📝", layout="wide")
    
    # Initialize session state
    init_session_state()
    
    # Apply CSS styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 1.5rem;
    }
    .correct {
        color: #2E7D32;
        font-weight: bold;
    }
    .incorrect {
        color: #C62828;
        font-weight: bold;
    }
    .unanswered {
        color: #FF8F00;
        font-weight: bold;
    }
    .explanation-header {
        color: #6A1B9A;
        font-weight: bold;
    }
    .score-display {
        font-size: 1.8rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
        background-color: #E3F2FD;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # App header
    st.markdown('<h1 class="main-header">FE Learning</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Main navigation
    selected_page = st.sidebar.radio(
        "Navigation",
        ["Quiz", "History"],
        index=0 if st.session_state.route in ['quiz', 'result'] else 1,
        label_visibility="collapsed"
    )
    
    # Handle navigation selection
    if selected_page == "Quiz" and st.session_state.route not in ['quiz', 'result']:
        navigate_to('quiz')
    elif selected_page == "History" and st.session_state.route not in ['history', 'history_view']:
        navigate_to('history')
    
    # Route handler
    if st.session_state.route == 'quiz':
        quiz_page()
    elif st.session_state.route == 'result':
        result_page()
    elif st.session_state.route == 'history':
        history_page()
    elif st.session_state.route == 'history_view':
        history_view_page()

# Quiz page
def quiz_page():
    st.markdown(
        """
        <script>
            window.scrollTo(0, 0);
        </script>
        """,
        unsafe_allow_html=True
    )
    st.components.v1.html("<script>window.scrollTo(0, 0);</script>", height=0)
    # First check if quiz data is loaded
    if not st.session_state.quiz_data:
        st.info("No quiz data found. Please upload a quiz data file.")
        
        uploaded_file = st.file_uploader("Upload quiz data file", type=["json"])
        
        if uploaded_file is not None:
            try:
                # Save the uploaded file
                with open(DATA_FILE, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Load the quiz data
                st.session_state.quiz_data = load_quiz_data()
                st.success("Successfully uploaded quiz data!")
                st.rerun()
            except Exception as e:
                st.error(f"Error saving quiz file: {e}")
        
        # Show example data structure
        st.markdown('<h2 class="sub-header">Expected Data Structure</h2>', unsafe_allow_html=True)
        st.code('''
{
  "course_ID": [
    {
      "course_ID": "CPV301",
      "quiz_sets": [
        {
          "quiz_set": 1,
          "questions": [
            {
              "id": 1,
              "question": "Sample question?",
              "options": {
                "A": "Option A",
                "B": "Option B",
                "C": "Option C",
                "D": "Option D"
              },
              "answer": "Answer text",
              "answer_number": ["A"]
            }
          ]
        }
      ]
    }
  ]
}
        ''', language="json")
        return
    
    # Show course selection
    courses = [course["course_ID"] for course in st.session_state.quiz_data["course_ID"]]
    
    selected_course = st.sidebar.selectbox(
        "Select Course", 
        options=courses,
        index=courses.index(st.session_state.current_course) if st.session_state.current_course in courses else 0
    )
    
    # Update current course if changed
    if selected_course != st.session_state.current_course:
        st.session_state.current_course = selected_course
        st.session_state.current_quiz_set = None
        st.session_state.user_answers = {}
        st.session_state.shuffled_questions = None
        st.session_state.quiz_start_time = time.time()
        st.rerun()
    
    # Find course data
    course_data = None
    for course in st.session_state.quiz_data["course_ID"]:
        if course["course_ID"] == selected_course:
            course_data = course
            break
    
    if not course_data:
        st.error("Course data not found!")
        return
    
    # Show quiz set selection
    quiz_sets = [quiz["quiz_set"] for quiz in course_data["quiz_sets"]]
    
    selected_quiz_set = st.sidebar.selectbox(
        "Select Quiz Set", 
        options=quiz_sets,
        index=quiz_sets.index(st.session_state.current_quiz_set) if st.session_state.current_quiz_set in quiz_sets else 0
    )
    
    # Update current quiz set if changed
    if selected_quiz_set != st.session_state.current_quiz_set:
        st.session_state.current_quiz_set = selected_quiz_set
        st.session_state.user_answers = {}
        st.session_state.shuffled_questions = None
        st.session_state.quiz_start_time = time.time()
        st.rerun()
    
    # Find quiz data
    quiz_data = None
    for quiz in course_data["quiz_sets"]:
        if quiz["quiz_set"] == selected_quiz_set:
            quiz_data = quiz
            break
    
    if not quiz_data:
        st.error("Quiz data not found!")
        return
    
    # Display quiz information
    st.markdown(f"**Course:** {selected_course}")
    st.markdown(f"**Quiz Set:** {selected_quiz_set}")
    
    # Use original questions without shuffling
    if st.session_state.shuffled_questions is None:
        st.session_state.shuffled_questions = quiz_data["questions"]
    
    questions = st.session_state.shuffled_questions
    
    # Display quiz questions
    st.markdown('<h2 class="sub-header">Questions</h2>', unsafe_allow_html=True)
    
    for question in questions:
        q_id = question["id"]
        st.markdown(f"#### Question {q_id}: {question['question']}")
        
        # Single or multiple choice
        is_multiple = len(question["answer_number"]) > 1
        
        if not is_multiple:
            # Single choice question
            options = list(question["options"].items())
            choice = st.radio(
                f"Options for Question {q_id}",
                options=[f"{key}: {value}" for key, value in options],
                key=f"q_{q_id}",
                index=None,
                label_visibility="collapsed"
            )
            
            # Process selection
            if choice:
                selected_key = choice.split(":")[0].strip()
                st.session_state.user_answers[q_id] = [selected_key]
            else:
                st.session_state.user_answers[q_id] = []
        else:
            # Multiple choice question
            st.write("Select all that apply:")
            options = list(question["options"].items())
            selections = []
            
            for key, value in options:
                if st.checkbox(
                    f"{key}: {value}",
                    key=f"q_{q_id}_{key}"
                ):
                    selections.append(key)
            
            st.session_state.user_answers[q_id] = selections
        
        st.markdown("---")
    
    # Submit button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Submit Quiz", use_container_width=True):
            # Calculate duration
            quiz_end_time = time.time()
            quiz_duration = quiz_end_time - st.session_state.quiz_start_time
            formatted_duration = format_duration(quiz_duration)
            
            # Calculate score
            total_questions = len(questions)
            correct_answers = 0
            
            for question in questions:
                q_id = question["id"]
                if q_id in st.session_state.user_answers:
                    user_answer = sorted(st.session_state.user_answers[q_id])
                    correct_answer = sorted(question["answer_number"])
                    
                    if user_answer == correct_answer:
                        correct_answers += 1
            
            st.session_state.score = (correct_answers / total_questions) * 100
            
            # Prepare for history
            json_user_answers = {str(k): v for k, v in st.session_state.user_answers.items()}
            
            # Save to history
            history_entry = {
                "course_id": selected_course,
                "quiz_set": selected_quiz_set,
                "score": round(st.session_state.score, 2),
                "date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "duration": formatted_duration,
                "user_answers": json_user_answers,
                "questions": questions
            }
            
            st.session_state.history["history"].append(history_entry)
            save_history(st.session_state.history)
            
            # Navigate to results page
            navigate_to('result')

# Result page
def result_page():
    st.components.v1.html("<script>window.scrollTo(0, 0);</script>", height=0)
    st.markdown(
        """
        <script>
            window.scrollTo(0, 0);
        </script>
        """,
        unsafe_allow_html=True
    )
    # Display course and quiz info
    st.markdown(f"**Course:** {st.session_state.current_course}")
    st.markdown(f"**Quiz Set:** {st.session_state.current_quiz_set}")
    
    # Display score
    st.markdown('<h2 class="sub-header">Quiz Results</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="score-display">Your score: {st.session_state.score:.1f}%</div>', unsafe_allow_html=True)
    
    # Display review
    display_quiz_review(
        st.session_state.shuffled_questions,
        st.session_state.user_answers,
        st.session_state.current_course,
        st.session_state.current_quiz_set
    )
    
    # Retake button
    if st.button("Retake Quiz"):
        st.session_state.user_answers = {}
        st.session_state.shuffled_questions = None
        st.session_state.quiz_start_time = time.time()
        navigate_to('quiz')

# Function to display quiz review
def display_quiz_review(questions, user_answers, course_id, quiz_set_id):
    st.markdown('<h2 class="sub-header">Review</h2>', unsafe_allow_html=True)
    
    for question in questions:
        q_id = question["id"]
        
        # Xử lý định dạng user_answers
        if isinstance(user_answers, dict):
            if str(q_id) in user_answers:
                user_answer = user_answers[str(q_id)]
            elif q_id in user_answers:
                user_answer = user_answers[q_id]
            else:
                user_answer = []
        else:
            user_answer = []
        
        correct_answer = question["answer_number"]
        
        was_answered = len(user_answer) > 0
        
        if was_answered:
            is_correct = sorted(user_answer) == sorted(correct_answer)
            status_class = "correct" if is_correct else "incorrect"
            status_text = "Correct" if is_correct else "Incorrect"
        else:
            status_class = "unanswered"
            status_text = "Not answered"
        
        col1, col2 = st.columns([10, 1])
        
        with col1:
            st.markdown(f"#### Question {q_id}: {question['question']}")
            st.markdown(f'<span class="{status_class}">{status_text}</span>', unsafe_allow_html=True)
            
            # Hiển thị các đáp án với xử lý xuống dòng
            for key, value in question["options"].items():
                # Thay thế ký tự xuống dòng để HTML hiểu được
                value_html = value.replace("\n", "<br>")
                is_user_selected = key in user_answer
                is_correct_option = key in correct_answer
                
                if is_user_selected and is_correct_option:
                    option_class = "correct"
                elif is_user_selected and not is_correct_option:
                    option_class = "incorrect"
                elif not is_user_selected and is_correct_option:
                    option_class = "correct"
                else:
                    option_class = ""
                
                if option_class:
                    st.markdown(
                        f'<div class="{option_class}" style="margin:0;">Option {key}: {value_html}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div style="margin:0;">Option {key}: {value_html}</div>',
                        unsafe_allow_html=True
                    )
        
        with col2:
            explanation_key = f"explanation_{course_id}_{quiz_set_id}_{q_id}"
            if st.button("Explain", key=f"explain_{course_id}_{quiz_set_id}_{q_id}"):
                options_text = "\n".join([f"{key}: {value}" for key, value in question["options"].items()])
                with st.spinner("Generating explanation..."):
                    explanation = get_explanation(
                        question["question"],
                        question["answer"],
                        options_text,
                        q_id,
                        course_id,
                        quiz_set_id
                    )
                    st.session_state[explanation_key] = explanation
        
        if explanation_key in st.session_state:
            st.markdown('<p class="explanation-header">Explanation:</p>', unsafe_allow_html=True)
            st.write(st.session_state[explanation_key])
        
        st.markdown("---")

# History page
def history_page():
    # Display history list
    st.markdown('<h2 class="sub-header">Quiz History</h2>', unsafe_allow_html=True)
    
    if not st.session_state.history["history"]:
        st.info("No quiz history available yet.")
        return
    
    # Create a dataframe for the history
    history_data = []
    for i, entry in enumerate(st.session_state.history["history"]):
        history_data.append({
            "Index": i,
            "Course": entry.get("course_id", ""),
            "Quiz Set": entry.get("quiz_set", ""),
            "Score (%)": entry.get("score", 0),
            "Date & Time": entry.get("date_time", ""),
            "Duration": entry.get("duration", "")
        })
    
    history_df = pd.DataFrame(history_data)
    
    # Sort by date/time if present
    if "Date & Time" in history_df.columns and len(history_df) > 0:
        try:
            history_df["Date & Time"] = pd.to_datetime(history_df["Date & Time"])
            history_df = history_df.sort_values("Date & Time", ascending=False)
            history_df["Date & Time"] = history_df["Date & Time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            pass
    
    # Display history as a table with view buttons
    st.write("### Quiz Attempts")
    
    # Headers
    header_cols = st.columns([3, 2, 2, 3, 2, 1])
    header_cols[0].write("**Course**")
    header_cols[1].write("**Quiz Set**")
    header_cols[2].write("**Score (%)**")
    header_cols[3].write("**Date & Time**")
    header_cols[4].write("**Duration**")
    header_cols[5].write("**Action**")
    
    # Rows
    for _, row in history_df.iterrows():
        cols = st.columns([3, 2, 2, 3, 2, 1])
        index = int(row["Index"])
        cols[0].write(row["Course"])
        cols[1].write(row["Quiz Set"])
        cols[2].write(f"{row['Score (%)']: .1f}")
        cols[3].write(row["Date & Time"])
        cols[4].write(row["Duration"])
        
        if cols[5].button("View", key=f"view_{index}"):
            st.session_state.history_view_index = index
            navigate_to('history_view')
    
    # Clear history button
    if st.button("Clear History"):
        st.session_state.history = {"history": []}
        save_history(st.session_state.history)
        st.success("History cleared!")
        st.rerun()

# History view page
def history_view_page():
    # Check if we have a valid history index
    if st.session_state.history_view_index is None or len(st.session_state.history["history"]) <= st.session_state.history_view_index:
        navigate_to('history')
        return
    
    # Get the history entry
    entry = st.session_state.history["history"][st.session_state.history_view_index]
    
    # Back button
    if st.sidebar.button("Back to History"):
        st.session_state.history_view_index = None
        navigate_to('history')
    
    # Display course and quiz info
    st.markdown(f"**Course:** {entry['course_id']}")
    st.markdown(f"**Quiz Set:** {entry['quiz_set']}")
    st.markdown(f"**Date:** {entry['date_time']}")
    st.markdown(f"**Duration:** {entry['duration']}")
    
    # Display score
    st.markdown('<h2 class="sub-header">Quiz Results</h2>', unsafe_allow_html=True)
    st.markdown(f'<div class="score-display">Your score: {entry["score"]:.1f}%</div>', unsafe_allow_html=True)
    
    # Display review
    display_quiz_review(
        entry['questions'],
        entry['user_answers'],
        entry['course_id'],
        entry['quiz_set']
    )

# Run the app
if __name__ == "__main__":
    main()