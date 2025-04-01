import streamlit as st
import json
import os
import datetime
import time
import google.generativeai as genai
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL") 
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Initialize session state for API key and user info
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
    st.session_state.user_authenticated = False

# File path for quiz data only (this is still needed)
DATA_FILE = "data.json"

# Function to check if tables exist and create them if needed
def create_tables_if_needed():
    """Check if tables exist and create them if needed using the Supabase API"""
    try:
        # First check if the users table exists by trying to query it
        try:
            supabase.table('users').select('*').limit(1).execute()
            users_exists = True
        except Exception:
            users_exists = False
            
        # Check if quiz_history table exists
        try:
            supabase.table('quiz_history').select('*').limit(1).execute()
            history_exists = True
        except Exception:
            history_exists = False
            
        # Check if explanations table exists
        try:
            supabase.table('explanations').select('*').limit(1).execute()
            explanations_exists = True
        except Exception:
            explanations_exists = False
            
        # Create missing tables using Supabase REST API
        if not users_exists:
            st.warning("The 'users' table doesn't exist in your Supabase project. Please create it using the SQL Editor.")
            st.code("""
CREATE TABLE public.users (
    id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
            """, language="sql")
            
        if not history_exists:
            st.warning("The 'quiz_history' table doesn't exist in your Supabase project. Please create it using the SQL Editor.")
            st.code("""
CREATE TABLE public.quiz_history (
    id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    course_id TEXT NOT NULL,
    quiz_set TEXT NOT NULL,
    score FLOAT NOT NULL,
    total_questions INTEGER,
    date_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration TEXT,
    user_answers JSONB,
    questions JSONB
);
            """, language="sql")
            
        if not explanations_exists:
            st.warning("The 'explanations' table doesn't exist in your Supabase project. Please create it using the SQL Editor.")
            st.code("""
CREATE TABLE public.explanations (
    id SERIAL PRIMARY KEY,
    user_name TEXT NOT NULL,
    explanation_key TEXT NOT NULL,
    explanation_text TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_name, explanation_key)
);
            """, language="sql")
            
        # If any table is missing, show error but don't prevent app from running
        if not (users_exists and history_exists and explanations_exists):
            st.info("Some database tables are missing. Please create them using the SQL provided above.")
            
        return True
    except Exception as e:
        st.error(f"Error checking database tables: {e}")
        return False

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

# Update the load_history function to use the correct syntax for ordering

def load_history():
    try:
        if st.session_state.user_authenticated:
            # Get history from Supabase for ALL users
            # Changed from .order("date_time", ascending=False) to .order("date_time", desc=True)
            response = supabase.table("quiz_history").select("*").order("date_time", desc=True).execute()
            return {"history": response.data if response.data else []}
        return {"history": []}
    except Exception as e:
        st.error(f"Error loading history: {e}")
        return {"history": []}

# Function to save quiz history to Supabase
def save_history(history):
    try:
        if st.session_state.user_authenticated:
            for entry in history.get("history", []):
                # Add user name to entry
                if "user_name" not in entry:
                    entry["user_name"] = st.session_state.user_name
                
                # Insert the record to Supabase
                supabase.table("quiz_history").insert(entry).execute()
    except Exception as e:
        st.error(f"Error saving history: {e}")

# Function to load explanations from Supabase
def load_explanations():
    try:
        if st.session_state.user_authenticated:
            # Get explanations from Supabase
            response = supabase.table("explanations").select("*").eq("user_name", st.session_state.user_name).execute()
            if response.data:
                explanations = {}
                for item in response.data:
                    explanations[item["explanation_key"]] = item["explanation_text"]
                return explanations
        return {}
    except Exception as e:
        st.error(f"Error loading explanations: {e}")
        return {}

# Function to save explanations to Supabase
def save_explanations(explanations):
    try:
        if st.session_state.user_authenticated:
            for key, text in explanations.items():
                # Prepare the record
                record = {
                    "explanation_key": key,
                    "explanation_text": text,
                    "user_name": st.session_state.user_name
                }
                
                # Use upsert instead of insert
                supabase.table("explanations").upsert(record).execute()
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
    
    # Check if API key is configured
    if not st.session_state.api_key:
        return "Please enter your Google API key in the sidebar to generate explanations."
    
    # If not found, generate with API
    try:
        # Configure the API with the user's key
        genai.configure(api_key=st.session_state.api_key)
        
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
        
        # Save to database
        explanations[explanation_key] = explanation
        save_explanations(explanations)
        
        return explanation
    except Exception as e:
        error_message = str(e)
        if "API key not available" in error_message or "invalid api key" in error_message.lower():
            return "Invalid API key. Please enter a valid Google API key in the sidebar."
        st.error(f"Error generating explanation: {e}")
        return "Sorry, could not generate explanation. Please check your API key or try again later."

# Format duration function
def format_duration(seconds):
    """Format duration in seconds to a readable string"""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

# Function to initialize or reset session state
def init_session_state():
    if 'route' not in st.session_state:
        st.session_state.route = 'login'  # Start with login screen
    
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = load_quiz_data()
    
    if 'course_data' not in st.session_state:
        st.session_state.course_data = None
    
    if 'current_course' not in st.session_state:
        st.session_state.current_course = None
        
    if 'current_quiz_set' not in st.session_state:
        st.session_state.current_quiz_set = None
    
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
        
    if 'shuffled_questions' not in st.session_state:
        st.session_state.shuffled_questions = None
        
    if 'quiz_start_time' not in st.session_state:
        st.session_state.quiz_start_time = time.time()
    
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    
    if 'score' not in st.session_state:
        st.session_state.score = 0
    
    if 'total_questions' not in st.session_state:
        st.session_state.total_questions = 0
    
    if 'quiz_history' not in st.session_state:
        st.session_state.quiz_history = load_history()
        
    if 'view_history_item' not in st.session_state:
        st.session_state.view_history_item = None
        
    if 'history_view_index' not in st.session_state:
        st.session_state.history_view_index = None
        
    if 'history' not in st.session_state:
        st.session_state.history = load_history()

# Function to navigate to a different route
def navigate_to(route):
    st.session_state.route = route

# Update the login_page function to use button callbacks instead of inline code

def login_callback():
    # This function will be called when the login button is clicked
    user_name = st.session_state.login_name_input
    if user_name:
        st.session_state.user_name = user_name
        st.session_state.user_authenticated = True
        st.session_state.route = 'quiz'
        
        # Store database operations for next run to avoid race conditions
        st.session_state.pending_user_creation = user_name

def login_page():
    st.markdown('<h2 class="sub-header">User Login</h2>', unsafe_allow_html=True)
    
    st.write("Please enter your name to start using the quiz app:")
    
    # Use a session state key for the input
    st.text_input("Your Name", key="login_name_input")
    
    # Use on_click instead of checking button state
    st.button("Start Quiz", on_click=login_callback)

# Update the sidebar navigation to use callbacks

def nav_to_quiz():
    st.session_state.route = 'quiz'

def nav_to_history():
    st.session_state.route = 'history'

# Main function for the entire app
def main():
    # Setup the page
    st.set_page_config(page_title="FE Learning", page_icon="📝", layout="wide")
    
    # Initialize session state
    init_session_state()
    
    # Process any pending actions first
    process_pending_actions()
    
    # Try to verify database tables exist
    create_tables_if_needed()
    
    # Process any pending actions
    process_pending_actions()
    
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
    
    # Only show navigation after login
    if st.session_state.user_authenticated:
        # Sidebar navigation
        st.sidebar.title("Navigation")
        
        # Use columns for navigation buttons
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.button("Quiz", on_click=nav_to_quiz, 
                      use_container_width=True,
                      type="primary" if st.session_state.route in ['quiz', 'result'] else "secondary")
        with col2:
            st.button("History", on_click=nav_to_history,
                      use_container_width=True,
                      type="primary" if st.session_state.route in ['history', 'history_view'] else "secondary")
        
        # Add API Key input in sidebar
        st.sidebar.markdown("---")
        st.sidebar.title("Settings")
        
        # Show logged in user
        st.sidebar.success(f"Logged in as: {st.session_state.user_name}")
        
        # API Key input with password mask
        api_key = st.sidebar.text_input(
            "Enter Google API Key for explanations",
            value=st.session_state.api_key,
            type="password",
            help="Enter your Google API key to enable AI explanations for quiz answers"
        )
        
        # Save API key to session state if changed
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            st.sidebar.success("API key updated!")
        
        # Add help text
        st.sidebar.info(
            "You need a Google API key with Gemini access to use the explanation feature. "
            "Get it from [Google AI Studio](https://makersuite.google.com/app/apikey)."
        )
    
    # Route handler
    if st.session_state.route == 'login':
        login_page()
    elif st.session_state.route == 'quiz':
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
            handle_button_action(
                "submit_quiz",
                questions=questions,
                course=selected_course,
                quiz_set=selected_quiz_set,
                route='result',
                rerun=True
            )

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
        handle_button_action("retake_quiz", route='quiz', rerun=True)

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
                if not st.session_state.api_key:
                    st.warning("Please enter your Google API key in the sidebar to use the explanation feature.")
                else:
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

# Update the history_page function to include filtering options

def history_page():
    # Display history list
    st.markdown('<h2 class="sub-header">Quiz History</h2>', unsafe_allow_html=True)
    
    # Reload history to get fresh data
    st.session_state.history = load_history()
    
    if not st.session_state.history["history"]:
        st.info("No quiz history available yet.")
        return
    
    # Create a dataframe for the history
    history_data = []
    for i, entry in enumerate(st.session_state.history["history"]):
        history_data.append({
            "Index": i,
            "User": entry.get("user_name", "Unknown"),
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
    
    # Add filtering options
    st.write("### Filter Quiz Attempts")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if "User" in history_df.columns and not history_df.empty:
            users = ["All Users"] + sorted(history_df["User"].unique().tolist())
            selected_user = st.selectbox("User", users)
    
    with col2:
        if "Course" in history_df.columns and not history_df.empty:
            courses = ["All Courses"] + sorted(history_df["Course"].unique().tolist())
            selected_course = st.selectbox("Course", courses)
    
    with col3:
        if "Quiz Set" in history_df.columns and not history_df.empty:
            quiz_sets = ["All Quiz Sets"] + sorted(history_df["Quiz Set"].unique().tolist())
            selected_quiz_set = st.selectbox("Quiz Set", quiz_sets)
    
    # Apply filters
    filtered_df = history_df.copy()
    
    if "User" in history_df.columns and selected_user != "All Users":
        filtered_df = filtered_df[filtered_df["User"] == selected_user]
    
    if "Course" in history_df.columns and selected_course != "All Courses":
        filtered_df = filtered_df[filtered_df["Course"] == selected_course]
    
    if "Quiz Set" in history_df.columns and selected_quiz_set != "All Quiz Sets":
        filtered_df = filtered_df[filtered_df["Quiz Set"] == selected_quiz_set]
    
    # Display history as a table with view buttons
    st.write("### Quiz Attempts")
    
    if filtered_df.empty:
        st.info("No records match the selected filters.")
        return
    
    # Headers - adjusted column widths to include user
    header_cols = st.columns([2, 3, 2, 2, 3, 2, 1])
    header_cols[0].write("**User**")
    header_cols[1].write("**Course**")
    header_cols[2].write("**Quiz Set**")
    header_cols[3].write("**Score (%)**")
    header_cols[4].write("**Date & Time**")
    header_cols[5].write("**Duration**")
    header_cols[6].write("**Action**")
    
    # Rows - updated to include user
    for _, row in filtered_df.iterrows():
        cols = st.columns([2, 3, 2, 2, 3, 2, 1])
        index = int(row["Index"])
        cols[0].write(row["User"])
        cols[1].write(row["Course"])
        cols[2].write(row["Quiz Set"])
        cols[3].write(f"{row['Score (%)']: .1f}")
        cols[4].write(row["Date & Time"])
        cols[5].write(row["Duration"])
        
        if cols[6].button("View", key=f"view_{index}"):
            handle_button_action("view_history", index=index, route='history_view', rerun=True)
    
    # Add clear history button only for the current user
    st.markdown("---")
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Clear My History"):
            handle_button_action("clear_history", route="history", rerun=True)
    with col2:
        st.caption("This will only clear your own quiz history, not others'.")

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
        handle_button_action("back_to_history", route='history', rerun=True)
    
    # Display user and quiz info
    st.markdown(f"**User:** {entry.get('user_name', st.session_state.user_name)}")
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

# Replace the current handle_button_action function with this improved version:

def handle_button_action(action_type, **kwargs):
    """
    Simplified function to handle button actions
    """
    try:
        # Handle different types of actions
        if action_type == "clear_history":
            # Store action in session state for next run
            st.session_state.pending_action = "clear_history"
            st.session_state.route = "history"
            st.rerun()
            
        elif action_type == "view_history":
            # Store index and change route immediately
            history_index = kwargs.get("index")
            st.session_state.history_view_index = history_index
            st.session_state.route = "history_view"
            st.rerun()
            
        elif action_type == "back_to_history":
            st.session_state.history_view_index = None
            st.session_state.route = "history"
            st.rerun()
            
        elif action_type == "submit_quiz":
            # Store parameters for processing on next run
            st.session_state.pending_action = "submit_quiz"
            st.session_state.pending_questions = kwargs.get("questions")
            st.session_state.pending_course = kwargs.get("course")
            st.session_state.pending_quiz_set = kwargs.get("quiz_set")
            st.session_state.route = "result"
            st.rerun()
        
        elif action_type == "retake_quiz":
            st.session_state.user_answers = {}
            st.session_state.shuffled_questions = None
            st.session_state.quiz_start_time = time.time()
            st.session_state.route = "quiz"
            st.rerun()
            
        # If a route is specified, navigate to it (fallback)
        elif "route" in kwargs:
            st.session_state.route = kwargs["route"]
            st.rerun()
            
    except Exception as e:
        st.error(f"Error in {action_type}: {e}")

# Add this function and call it at the start of the main function

def process_pending_actions():
    """Process any pending actions stored in session state"""
    
    # Process user creation if needed
    if "pending_user_creation" in st.session_state:
        user_name = st.session_state.pending_user_creation
        try:
            # Check if user exists in Supabase
            response = supabase.table("users").select("*").eq("user_name", user_name).execute()
            
            if not response.data:
                # Create the user
                supabase.table("users").insert({"user_name": user_name}).execute()
        except Exception as e:
            st.warning(f"Database error: {e}")
            st.warning("User authentication failed. Some features may not work properly.")
        
        # Clear the pending flag
        del st.session_state.pending_user_creation
    
    # Process other pending actions...
    if "pending_action" in st.session_state:
        if "pending_action" in st.session_state:
            action = st.session_state.pending_action
            
            if action == "clear_history":
                # Execute the actual deletion
                if st.session_state.user_authenticated:
                    try:
                        supabase.table("quiz_history").delete().eq("user_name", st.session_state.user_name).execute()
                        # Reload history after clearing
                        st.session_state.history = load_history()
                        st.success("Your history has been cleared!")
                    except Exception as e:
                        st.error(f"Error clearing history: {e}")
            
            elif action == "submit_quiz":
                # Process quiz submission
                try:
                    questions = st.session_state.pending_questions
                    selected_course = st.session_state.pending_course
                    selected_quiz_set = st.session_state.pending_quiz_set
                    
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
                    
                    score = (correct_answers / total_questions) * 100
                    st.session_state.score = score
                    
                    # Prepare for history
                    json_user_answers = {str(k): v for k, v in st.session_state.user_answers.items()}
                    
                    # Create history entry
                    history_entry = {
                        "user_name": st.session_state.user_name,  # Make sure user name is included
                        "course_id": selected_course,
                        "quiz_set": selected_quiz_set,
                        "score": round(score, 2),
                        "total_questions": total_questions,
                        "date_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "duration": formatted_duration,
                        "user_answers": json_user_answers,
                        "questions": questions
                    }
                    
                    # Save to Supabase
                    save_history({"history": [history_entry]})
                    
                    # Also update local session state
                    if "history" not in st.session_state.history:
                        st.session_state.history = {"history": []}
                    st.session_state.history["history"].append(history_entry)
                    
                except Exception as e:
                    st.error(f"Error processing quiz submission: {e}")
            
            # Clear pending actions to prevent reprocessing
            del st.session_state.pending_action
            if "pending_questions" in st.session_state:
                del st.session_state.pending_questions
            if "pending_course" in st.session_state:
                del st.session_state.pending_course
            if "pending_quiz_set" in st.session_state:
                del st.session_state.pending_quiz_set

# Run the app
if __name__ == "__main__":
    main()