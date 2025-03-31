import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

class QuizDataManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Quiz Data Manager")
        self.root.geometry("1200x700")
        
        self.data = None
        self.current_path = []
        self.selected_item = None
        
        self.create_gui()
        self.load_data()
    
    def create_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Paned window for tree and details
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left frame with tree
        left_frame = ttk.Frame(paned, width=300)
        paned.add(left_frame, weight=1)
        
        # Tree view
        self.tree = ttk.Treeview(left_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(left_frame, orient="vertical", command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # Right frame for details
        self.right_frame = ttk.Frame(paned, width=700)
        paned.add(self.right_frame, weight=2)
        
        # Bottom frame for buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # Buttons
        ttk.Button(button_frame, text="Load Data", command=self.load_data_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Data", command=self.save_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add Course", command=lambda: self.add_item("course")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add Quiz Set", command=lambda: self.add_item("quiz_set")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Add Question", command=lambda: self.add_item("question")).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Item", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Import Temp JSON", command=self.import_temp_json).pack(side=tk.LEFT, padx=5)
        
        # Bind tree selection
        self.tree.bind("<<TreeviewSelect>>", self.item_selected)
    
    def load_data(self):
        """Load data from the default file path"""
        try:
            file_path = "e:/FE_Learning/data.json"
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.data = json.load(file)
                self.refresh_tree()
                messagebox.showinfo("Success", "Data loaded successfully")
            else:
                messagebox.showerror("Error", f"File not found: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
    
    def load_data_dialog(self):
        """Open file dialog to select and load JSON file"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.data = json.load(file)
                self.refresh_tree()
                messagebox.showinfo("Success", "Data loaded successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data: {str(e)}")
    
    def save_data(self):
        """Save data to the file"""
        if not self.data:
            messagebox.showerror("Error", "No data to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(self.data, file, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", "Data saved successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save data: {str(e)}")
    
    def refresh_tree(self):
        """Refresh the tree view with current data"""
        self.tree.delete(*self.tree.get_children())
        
        if not self.data:
            return
        
        # Add courses
        for i, course in enumerate(self.data.get("course_ID", [])):
            course_id = course.get("course_ID", f"Course {i}")
            course_node = self.tree.insert("", "end", text=course_id, values=("course", i))
            
            # Add quiz sets
            for j, quiz_set in enumerate(course.get("quiz_sets", [])):
                quiz_set_name = quiz_set.get("quiz_set", f"Quiz Set {j}")
                quiz_node = self.tree.insert(course_node, "end", text=quiz_set_name, values=("quiz_set", i, j))
                
                # Add questions
                for k, question in enumerate(quiz_set.get("questions", [])):
                    q_text = question.get("question", "")
                    if len(q_text) > 50:
                        q_text = q_text[:47] + "..."
                    self.tree.insert(quiz_node, "end", text=f"Q{k+1}: {q_text}", values=("question", i, j, k))
    
    def item_selected(self, event):
        """Handle tree item selection"""
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
        selected = self.tree.selection()
        if not selected:
            return
        
        item_id = selected[0]
        item_type = self.tree.item(item_id, "values")[0]
        self.selected_item = self.tree.item(item_id, "values")
        
        if item_type == "course":
            self.show_course_details()
        elif item_type == "quiz_set":
            self.show_quiz_set_details()
        elif item_type == "question":
            self.show_question_details()
    
    def show_course_details(self):
        """Display course details for editing"""
        course_idx = int(self.selected_item[1])
        course = self.data["course_ID"][course_idx]
        
        ttk.Label(self.right_frame, text="Course Details", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        ttk.Label(self.right_frame, text="Course ID:").grid(row=1, column=0, sticky="w", pady=5)
        course_id_var = tk.StringVar(value=course.get("course_ID", ""))
        course_id_entry = ttk.Entry(self.right_frame, textvariable=course_id_var, width=50)
        course_id_entry.grid(row=1, column=1, sticky="w", pady=5)
        
        # Save button
        ttk.Button(self.right_frame, text="Save Changes", 
                   command=lambda: self.save_course_changes(course_idx, course_id_var.get())
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
    
    def save_course_changes(self, course_idx, course_id):
        """Save changes to course details"""
        if not course_id:
            messagebox.showerror("Error", "Course ID cannot be empty")
            return
        
        self.data["course_ID"][course_idx]["course_ID"] = course_id
        self.refresh_tree()
        messagebox.showinfo("Success", "Course updated successfully")
    
    def show_quiz_set_details(self):
        """Display quiz set details for editing"""
        course_idx = int(self.selected_item[1])
        quiz_idx = int(self.selected_item[2])
        quiz_set = self.data["course_ID"][course_idx]["quiz_sets"][quiz_idx]
        
        ttk.Label(self.right_frame, text="Quiz Set Details", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        ttk.Label(self.right_frame, text="Quiz Set Name:").grid(row=1, column=0, sticky="w", pady=5)
        quiz_name_var = tk.StringVar(value=quiz_set.get("quiz_set", ""))
        quiz_name_entry = ttk.Entry(self.right_frame, textvariable=quiz_name_var, width=50)
        quiz_name_entry.grid(row=1, column=1, sticky="w", pady=5)
        
        # Save button
        ttk.Button(self.right_frame, text="Save Changes", 
                   command=lambda: self.save_quiz_set_changes(course_idx, quiz_idx, quiz_name_var.get())
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
    
    def save_quiz_set_changes(self, course_idx, quiz_idx, quiz_name):
        """Save changes to quiz set details"""
        if not quiz_name:
            messagebox.showerror("Error", "Quiz Set name cannot be empty")
            return
        
        self.data["course_ID"][course_idx]["quiz_sets"][quiz_idx]["quiz_set"] = quiz_name
        self.refresh_tree()
        messagebox.showinfo("Success", "Quiz Set updated successfully")
    
    def show_question_details(self):
        """Display question details for editing"""
        course_idx = int(self.selected_item[1])
        quiz_idx = int(self.selected_item[2])
        question_idx = int(self.selected_item[3])
        question = self.data["course_ID"][course_idx]["quiz_sets"][quiz_idx]["questions"][question_idx]
        
        # Create a frame with a scrollbar
        canvas = tk.Canvas(self.right_frame)
        scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        ttk.Label(scrollable_frame, text="Question Details", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Question ID
        ttk.Label(scrollable_frame, text="Question ID:").grid(row=1, column=0, sticky="w", pady=5)
        id_var = tk.StringVar(value=str(question.get("id", "")))
        id_entry = ttk.Entry(scrollable_frame, textvariable=id_var, width=50)
        id_entry.grid(row=1, column=1, sticky="w", pady=5)
        
        # Question Text
        ttk.Label(scrollable_frame, text="Question:").grid(row=2, column=0, sticky="w", pady=5)
        question_var = tk.StringVar(value=question.get("question", ""))
        question_entry = ttk.Entry(scrollable_frame, textvariable=question_var, width=50)
        question_entry.grid(row=2, column=1, sticky="w", pady=5)
        
        # Options
        ttk.Label(scrollable_frame, text="Options:", font=("Arial", 12, "bold")).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 5))
        
        options = question.get("options", {})
        option_vars = {}
        
        row_num = 4
        for key in ["A", "B", "C", "D"]:
            ttk.Label(scrollable_frame, text=f"Option {key}:").grid(row=row_num, column=0, sticky="w", pady=5)
            option_vars[key] = tk.StringVar(value=options.get(key, ""))
            option_entry = ttk.Entry(scrollable_frame, textvariable=option_vars[key], width=50)
            option_entry.grid(row=row_num, column=1, sticky="w", pady=5)
            row_num += 1
        
        # Answer
        ttk.Label(scrollable_frame, text="Answer:", font=("Arial", 12, "bold")).grid(row=row_num, column=0, columnspan=2, sticky="w", pady=(10, 5))
        row_num += 1
        
        ttk.Label(scrollable_frame, text="Answer Text:").grid(row=row_num, column=0, sticky="w", pady=5)
        answer_var = tk.StringVar(value=question.get("answer", ""))
        answer_entry = ttk.Entry(scrollable_frame, textvariable=answer_var, width=50)
        answer_entry.grid(row=row_num, column=1, sticky="w", pady=5)
        
        # Answer Letters
        row_num += 1
        ttk.Label(scrollable_frame, text="Answer Letters:").grid(row=row_num, column=0, sticky="w", pady=5)
        
        # Create checkbuttons for answer letters
        answer_letters_frame = ttk.Frame(scrollable_frame)
        answer_letters_frame.grid(row=row_num, column=1, sticky="w", pady=5)
        
        answer_letters = question.get("answer_number", [])
        answer_letter_vars = {}
        
        # Function to update answer text based on selected letters
        def update_answer_text():
            selected_letters = [key for key, var in answer_letter_vars.items() if var.get()]
            if selected_letters:
                # Collect all selected option texts
                selected_texts = [option_vars[letter].get() for letter in selected_letters]
                # Join them with a separator
                answer_var.set(" / ".join(selected_texts))
        
        # Now add the button after the function is defined
        ttk.Button(scrollable_frame, text="Sync from Selected", 
                   command=update_answer_text).grid(row=row_num-1, column=2, sticky="w", pady=5)
        
        for key in ["A", "B", "C", "D"]:
            answer_letter_vars[key] = tk.BooleanVar(value=key in answer_letters)
            # Create a proper callback with correct closure
            def make_callback(k):
                return lambda *args: update_answer_text()
            answer_letter_vars[key].trace_add("write", make_callback(key))
            ttk.Checkbutton(answer_letters_frame, text=key, variable=answer_letter_vars[key]).pack(side=tk.LEFT, padx=10)
        
        row_num += 1
        
        # Save button
        ttk.Button(scrollable_frame, text="Save Changes", 
                   command=lambda: self.save_question_changes(
                       course_idx, quiz_idx, question_idx, 
                       id_var.get(), question_var.get(), 
                       option_vars, answer_var.get(), answer_letter_vars
                   )
        ).grid(row=row_num, column=0, columnspan=2, sticky="w", pady=10)
    
    def save_question_changes(self, course_idx, quiz_idx, question_idx, id_val, question_text, 
                              option_vars, answer_text, answer_letter_vars):
        """Save changes to question details"""
        if not id_val or not question_text or not answer_text:
            messagebox.showerror("Error", "ID, question text, and answer text cannot be empty")
            return
        
        # Update question data
        question = self.data["course_ID"][course_idx]["quiz_sets"][quiz_idx]["questions"][question_idx]
        
        question["id"] = int(id_val)
        question["question"] = question_text
        
        # Update options
        options = {}
        for key, var in option_vars.items():
            options[key] = var.get()
        question["options"] = options
        
        # Update answer
        question["answer"] = answer_text
        
        # Update answer letters
        answer_letters = []
        for key, var in answer_letter_vars.items():
            if var.get():
                answer_letters.append(key)
        question["answer_number"] = answer_letters
        
        self.refresh_tree()
        messagebox.showinfo("Success", "Question updated successfully")
    
    def add_item(self, item_type):
        """Add a new item (course, quiz set, or question)"""
        if item_type == "course":
            self.add_course()
        elif item_type == "quiz_set":
            if not self.selected_item or self.selected_item[0] not in ["course", "quiz_set"]:
                messagebox.showerror("Error", "Please select a course first")
                return
            course_idx = int(self.selected_item[1])
            self.add_quiz_set(course_idx)
        elif item_type == "question":
            if not self.selected_item or self.selected_item[0] not in ["quiz_set", "question"]:
                messagebox.showerror("Error", "Please select a quiz set first")
                return
            course_idx = int(self.selected_item[1])
            quiz_idx = int(self.selected_item[2])
            self.add_question(course_idx, quiz_idx)
    
    def add_course(self):
        """Add a new course"""
        if "course_ID" not in self.data:
            self.data["course_ID"] = []
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Course")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Course ID:").grid(row=0, column=0, sticky="w", pady=5, padx=10)
        course_id_var = tk.StringVar()
        course_id_entry = ttk.Entry(dialog, textvariable=course_id_var, width=30)
        course_id_entry.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        
        def save_course():
            course_id = course_id_var.get()
            if not course_id:
                messagebox.showerror("Error", "Course ID cannot be empty", parent=dialog)
                return
            
            new_course = {
                "course_ID": course_id,
                "quiz_sets": []
            }
            
            self.data["course_ID"].append(new_course)
            self.refresh_tree()
            dialog.destroy()
            messagebox.showinfo("Success", "Course added successfully")
        
        ttk.Button(dialog, text="Save", command=save_course).grid(row=1, column=0, columnspan=2, pady=20)
    
    def add_quiz_set(self, course_idx):
        """Add a new quiz set to a course"""
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Quiz Set")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Quiz Set Name:").grid(row=0, column=0, sticky="w", pady=5, padx=10)
        quiz_name_var = tk.StringVar()
        quiz_name_entry = ttk.Entry(dialog, textvariable=quiz_name_var, width=30)
        quiz_name_entry.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        
        def save_quiz_set():
            quiz_name = quiz_name_var.get()
            if not quiz_name:
                messagebox.showerror("Error", "Quiz Set name cannot be empty", parent=dialog)
                return
            
            new_quiz_set = {
                "quiz_set": quiz_name,
                "questions": []
            }
            
            self.data["course_ID"][course_idx]["quiz_sets"].append(new_quiz_set)
            self.refresh_tree()
            dialog.destroy()
            messagebox.showinfo("Success", "Quiz Set added successfully")
        
        ttk.Button(dialog, text="Save", command=save_quiz_set).grid(row=1, column=0, columnspan=2, pady=20)
    
    def add_question(self, course_idx, quiz_idx):
        """Add a new question to a quiz set"""
        questions = self.data["course_ID"][course_idx]["quiz_sets"][quiz_idx]["questions"]
        
        # Calculate next ID
        next_id = 1
        if questions:
            existing_ids = [q.get("id", 0) for q in questions]
            next_id = max(existing_ids) + 1
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Question")
        dialog.geometry("600x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create a canvas with scrollbar
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Question fields
        ttk.Label(scrollable_frame, text="Question ID:").grid(row=0, column=0, sticky="w", pady=5, padx=10)
        id_var = tk.StringVar(value=str(next_id))
        id_entry = ttk.Entry(scrollable_frame, textvariable=id_var, width=30)
        id_entry.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        
        ttk.Label(scrollable_frame, text="Question:").grid(row=1, column=0, sticky="w", pady=5, padx=10)
        question_var = tk.StringVar()
        question_entry = ttk.Entry(scrollable_frame, textvariable=question_var, width=50)
        question_entry.grid(row=1, column=1, sticky="w", pady=5, padx=10)
        
        # Options
        ttk.Label(scrollable_frame, text="Options:", font=("Arial", 12, "bold")).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=10)
        
        option_vars = {}
        row_num = 3
        
        for key in ["A", "B", "C", "D"]:
            ttk.Label(scrollable_frame, text=f"Option {key}:").grid(row=row_num, column=0, sticky="w", pady=5, padx=10)
            option_vars[key] = tk.StringVar()
            option_entry = ttk.Entry(scrollable_frame, textvariable=option_vars[key], width=50)
            option_entry.grid(row=row_num, column=1, sticky="w", pady=5, padx=10)
            row_num += 1
        
        # Answer
        ttk.Label(scrollable_frame, text="Answer:", font=("Arial", 12, "bold")).grid(row=row_num, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=10)
        row_num += 1
        
        ttk.Label(scrollable_frame, text="Answer Text:").grid(row=row_num, column=0, sticky="w", pady=5, padx=10)
        answer_var = tk.StringVar()
        answer_entry = ttk.Entry(scrollable_frame, textvariable=answer_var, width=50)
        answer_entry.grid(row=row_num, column=1, sticky="w", pady=5, padx=10)
        
        # Function to update answer text based on selected letters
        def update_answer_text():
            selected_letters = [key for key, var in answer_letter_vars.items() if var.get()]
            if selected_letters:
                # Collect all selected option texts
                selected_texts = [option_vars[letter].get() for letter in selected_letters]
                # Join them with a separator
                answer_var.set(" / ".join(selected_texts))

        # Add this button after the answer_var entry, but before creating answer_letter_vars
        ttk.Button(scrollable_frame, text="Sync from Selected", 
                   command=update_answer_text).grid(row=row_num, column=2, sticky="w", pady=5)
        
        # Answer Letters
        row_num += 1
        ttk.Label(scrollable_frame, text="Answer Letters:").grid(row=row_num, column=0, sticky="w", pady=5, padx=10)
        
        answer_letters_frame = ttk.Frame(scrollable_frame)
        answer_letters_frame.grid(row=row_num, column=1, sticky="w", pady=5, padx=10)
        
        answer_letter_vars = {}
        for key in ["A", "B", "C", "D"]:
            answer_letter_vars[key] = tk.BooleanVar(value=False)
            # Add trace to update answer text when checkbox state changes
            answer_letter_vars[key].trace_add("write", lambda *args: update_answer_text())
            ttk.Checkbutton(answer_letters_frame, text=key, variable=answer_letter_vars[key]).pack(side=tk.LEFT, padx=10)
        
        row_num += 1
        
        def save_question():
            # Validate inputs
            if not id_var.get() or not question_var.get() or not answer_var.get():
                messagebox.showerror("Error", "ID, question text, and answer text cannot be empty", parent=dialog)
                return
            
            # Check if at least one option is selected
            any_selected = False
            for var in answer_letter_vars.values():
                if var.get():
                    any_selected = True
                    break
            
            if not any_selected:
                messagebox.showerror("Error", "Please select at least one answer letter", parent=dialog)
                return
            
            # Prepare options
            options = {}
            for key, var in option_vars.items():
                options[key] = var.get()
            
            # Prepare answer letters
            answer_letters = []
            for key, var in answer_letter_vars.items():
                if var.get():
                    answer_letters.append(key)
            
            # Create new question
            new_question = {
                "id": int(id_var.get()),
                "question": question_var.get(),
                "options": options,
                "answer": answer_var.get(),
                "answer_number": answer_letters
            }
            
            # Add to data
            self.data["course_ID"][course_idx]["quiz_sets"][quiz_idx]["questions"].append(new_question)
            self.refresh_tree()
            dialog.destroy()
            messagebox.showinfo("Success", "Question added successfully")
        
        ttk.Button(scrollable_frame, text="Save", command=save_question).grid(row=row_num, column=0, columnspan=2, pady=20)
    
    def delete_selected(self):
        """Delete the selected item"""
        if not self.selected_item:
            messagebox.showerror("Error", "Please select an item to delete")
            return
        
        item_type = self.selected_item[0]
        
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete this {item_type}?"):
            return
        
        if item_type == "course":
            course_idx = int(self.selected_item[1])
            self.data["course_ID"].pop(course_idx)
        
        elif item_type == "quiz_set":
            course_idx = int(self.selected_item[1])
            quiz_idx = int(self.selected_item[2])
            self.data["course_ID"][course_idx]["quiz_sets"].pop(quiz_idx)
        
        elif item_type == "question":
            course_idx = int(self.selected_item[1])
            quiz_idx = int(self.selected_item[2])
            question_idx = int(self.selected_item[3])
            self.data["course_ID"][course_idx]["quiz_sets"][quiz_idx]["questions"].pop(question_idx)
        
        self.refresh_tree()
        messagebox.showinfo("Success", f"{item_type.capitalize()} deleted successfully")

    def import_temp_json(self):
        """Import data from a temporary JSON file"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                temp_data = json.load(file)
            
            # Process the imported data
            if not self.data:
                messagebox.showerror("Error", "Please load a base JSON file first")
                return
            
            # Create dialog to choose import mode
            dialog = tk.Toplevel(self.root)
            dialog.title("Import Options")
            dialog.geometry("500x300")
            dialog.transient(self.root)
            dialog.grab_set()
            
            ttk.Label(dialog, text="Choose import mode:", font=("Arial", 12, "bold")).grid(
                row=0, column=0, columnspan=2, sticky="w", pady=(10, 20), padx=10)
            
            import_mode = tk.StringVar(value="questions")
            ttk.Radiobutton(dialog, text="Import questions into existing course/quiz set", 
                          value="questions", variable=import_mode).grid(
                row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)
            
            ttk.Radiobutton(dialog, text="Import entire course", 
                          value="course", variable=import_mode).grid(
                row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)
            
            # Destination frame - will be shown/hidden based on selection
            dest_frame = ttk.LabelFrame(dialog, text="Import Destination")
            dest_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
            
            # Course selection
            ttk.Label(dest_frame, text="Course:").grid(row=0, column=0, sticky="w", padx=10)
            course_var = tk.StringVar()
            course_combo = ttk.Combobox(dest_frame, textvariable=course_var, width=30)
            course_names = [course.get("course_ID", f"Course {i}") for i, course in enumerate(self.data.get("course_ID", []))]
            course_combo["values"] = course_names
            if course_names:
                course_combo.current(0)
            course_combo.grid(row=0, column=1, sticky="w", padx=10, pady=5)
            
            # Quiz set selection
            ttk.Label(dest_frame, text="Quiz Set:").grid(row=1, column=0, sticky="w", padx=10)
            quiz_var = tk.StringVar()
            quiz_combo = ttk.Combobox(dest_frame, textvariable=quiz_var, width=30)
            
            def update_quiz_sets(*args):
                selected_course_name = course_var.get()
                if not selected_course_name:
                    return
                course_idx = course_names.index(selected_course_name)
                quiz_sets = self.data["course_ID"][course_idx].get("quiz_sets", [])
                quiz_names = [quiz.get("quiz_set", f"Quiz Set {i}") for i, quiz in enumerate(quiz_sets)]
                quiz_combo["values"] = quiz_names
                if quiz_names:
                    quiz_combo.current(0)
            
            course_combo.bind("<<ComboboxSelected>>", update_quiz_sets)
            quiz_combo.grid(row=1, column=1, sticky="w", padx=10, pady=5)
            
            # Update quiz sets initial values
            if course_names:
                update_quiz_sets()
            
            # Summary frame to show import details
            summary_frame = ttk.LabelFrame(dialog, text="Import Summary")
            summary_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
            
            summary_text = tk.StringVar()
            summary_label = ttk.Label(summary_frame, textvariable=summary_text, wraplength=400)
            summary_label.grid(row=0, column=0, padx=10, pady=5)
            
            # Function to update the summary based on the selected mode
            def update_summary(*args):
                mode = import_mode.get()
                if mode == "questions":
                    dest_frame.grid()
                    # Calculate question count
                    question_count = 0
                    if isinstance(temp_data, list):
                        question_count = len(temp_data)
                    elif isinstance(temp_data, dict):
                        if "questions" in temp_data:
                            question_count = len(temp_data["questions"])
                        elif "course_ID" in temp_data:
                            for course in temp_data.get("course_ID", []):
                                for quiz_set in course.get("quiz_sets", []):
                                    question_count += len(quiz_set.get("questions", []))
                    
                    summary_text.set(f"Found approximately {question_count} questions to import into the selected destination.")
                else:
                    dest_frame.grid_remove()
                    # Calculate course count
                    course_count = 0
                    quiz_count = 0
                    question_count = 0
                    
                    if isinstance(temp_data, dict) and "course_ID" in temp_data:
                        course_count = len(temp_data.get("course_ID", []))
                        for course in temp_data.get("course_ID", []):
                            quiz_count += len(course.get("quiz_sets", []))
                            for quiz_set in course.get("quiz_sets", []):
                                question_count += len(quiz_set.get("questions", []))
                    
                    summary_text.set(f"Will import {course_count} courses with {quiz_count} quiz sets containing {question_count} questions.")
            
            import_mode.trace_add("write", update_summary)
            update_summary()
            
            def process_import():
                mode = import_mode.get()
                if mode == "questions":
                    # Original question import functionality
                    if not course_var.get() or not quiz_var.get():
                        messagebox.showerror("Error", "Please select both course and quiz set", parent=dialog)
                        return
                    
                    course_idx = course_names.index(course_var.get())
                    quiz_sets = self.data["course_ID"][course_idx].get("quiz_sets", [])
                    quiz_names = [quiz.get("quiz_set", f"Quiz Set {i}") for i, quiz in enumerate(quiz_sets)]
                    quiz_idx = quiz_names.index(quiz_var.get())
                    
                    # Get current questions
                    current_questions = self.data["course_ID"][course_idx]["quiz_sets"][quiz_idx]["questions"]
                    next_id = max([q.get("id", 0) for q in current_questions], default=0) + 1
                    
                    # Convert and add imported questions
                    imported_count = 0
                    
                    # Determine the format of the imported data
                    if isinstance(temp_data, list):
                        # Assume it's a list of questions
                        for q_data in temp_data:
                            if self._convert_and_add_question(q_data, current_questions, next_id):
                                next_id += 1
                                imported_count += 1
                    elif isinstance(temp_data, dict):
                        # Check if it has a questions field
                        if "questions" in temp_data:
                            for q_data in temp_data["questions"]:
                                if self._convert_and_add_question(q_data, current_questions, next_id):
                                    next_id += 1
                                    imported_count += 1
                        # Check for nested structure
                        elif "course_ID" in temp_data:
                            # Try to find questions in the nested structure
                            found_questions = False
                            for course in temp_data.get("course_ID", []):
                                for quiz_set in course.get("quiz_sets", []):
                                    for q_data in quiz_set.get("questions", []):
                                        if self._convert_and_add_question(q_data, current_questions, next_id):
                                            next_id += 1
                                            imported_count += 1
                                            found_questions = True
                            if not found_questions:
                                messagebox.showerror("Error", "No valid questions found in the imported data", parent=dialog)
                                return
                        else:
                            # Try to convert a single question
                            if self._convert_and_add_question(temp_data, current_questions, next_id):
                                imported_count = 1
                    
                    if imported_count > 0:
                        self.refresh_tree()
                        dialog.destroy()
                        messagebox.showinfo("Success", f"Successfully imported {imported_count} questions")
                    else:
                        messagebox.showerror("Error", "No valid questions were imported", parent=dialog)
                
                else:  # Import entire course
                    # New functionality to import entire course
                    if isinstance(temp_data, dict) and "course_ID" in temp_data:
                        imported_course_count = 0
                        
                        # Append each course in the temp data to the main data
                        for course in temp_data.get("course_ID", []):
                            if "course_ID" in course and "quiz_sets" in course:
                                self.data["course_ID"].append(course)
                                imported_course_count += 1
                        
                        if imported_course_count > 0:
                            self.refresh_tree()
                            dialog.destroy()
                            messagebox.showinfo("Success", f"Successfully imported {imported_course_count} courses")
                        else:
                            messagebox.showerror("Error", "No valid courses found in the imported data", parent=dialog)
                    else:
                        messagebox.showerror("Error", "The JSON file does not contain valid course data", parent=dialog)
            
            ttk.Button(dialog, text="Import", command=process_import).grid(
                row=5, column=0, columnspan=2, pady=20)
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import data: {str(e)}")

    def _convert_and_add_question(self, q_data, current_questions, next_id):
        """Convert question data to the correct format and add it to the questions list"""
        try:
            new_question = {}
            
            # Extract question ID
            if "id" in q_data:
                new_question["id"] = int(q_data["id"])
            else:
                new_question["id"] = next_id
            
            # Extract question text
            if "question" in q_data:
                new_question["question"] = q_data["question"]
            else:
                # Try to find question text in alternative fields
                for field in ["text", "title", "prompt"]:
                    if field in q_data:
                        new_question["question"] = q_data[field]
                        break
                else:
                    return False  # No question text found
            
            # Extract options
            options = {}
            if "options" in q_data and isinstance(q_data["options"], dict):
                # Direct options mapping
                for key in ["A", "B", "C", "D"]:
                    if key in q_data["options"]:
                        options[key] = q_data["options"][key]
            elif "options" in q_data and isinstance(q_data["options"], list):
                # Options as a list
                for i, opt in enumerate(q_data["options"]):
                    if i < 4:
                        key = chr(65 + i)  # A, B, C, D
                        if isinstance(opt, dict) and "text" in opt:
                            options[key] = opt["text"]
                        else:
                            options[key] = str(opt)
            else:
                # Look for individual option fields
                for key in ["A", "B", "C", "D"]:
                    option_key = f"option_{key.lower()}"
                    if option_key in q_data:
                        options[key] = q_data[option_key]
            
            if not options:
                return False  # No options found
            
            new_question["options"] = options
            
            # Extract answer
            if "answer" in q_data:
                new_question["answer"] = q_data["answer"]
            else:
                # Try to find answer in alternative fields
                for field in ["correct_answer", "solution", "correct"]:
                    if field in q_data:
                        new_question["answer"] = q_data[field]
                        break
                else:
                    # If no answer text is found, use the text of the correct option
                    if "answer_number" in q_data or "correct_option" in q_data:
                        answer_key = q_data.get("answer_number", q_data.get("correct_option", []))[0]
                        if answer_key in options:
                            new_question["answer"] = options[answer_key]
                        else:
                            new_question["answer"] = f"Option {answer_key}"
                    else:
                        return False  # No answer found
            
            # Extract answer number (letter)
            if "answer_number" in q_data:
                if isinstance(q_data["answer_number"], list):
                    new_question["answer_number"] = q_data["answer_number"]
                else:
                    new_question["answer_number"] = [q_data["answer_number"]]
            else:
                # Try to find answer letter in alternative fields
                for field in ["correct_option", "correct_letter", "answer_key"]:
                    if field in q_data:
                        if isinstance(q_data[field], list):
                            new_question["answer_number"] = q_data[field]
                        else:
                            new_question["answer_number"] = [q_data[field]]
                        break
                else:
                    # If we have the answer text, try to match it to an option
                    if "answer" in new_question:
                        answer_text = new_question["answer"]
                        for key, text in options.items():
                            if text == answer_text:
                                new_question["answer_number"] = [key]
                                break
                        else:
                            # Default to A if we can't determine
                            new_question["answer_number"] = ["A"]
                    else:
                        new_question["answer_number"] = ["A"]  # Default
            
            # Add the converted question to the list
            current_questions.append(new_question)
            return True
        
        except Exception as e:
            print(f"Error converting question: {str(e)}")
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizDataManager(root)
    root.mainloop()