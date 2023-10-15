from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

# Get the current directory of your Python script
current_directory = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'username'  # Replace with your own secret key
print(app.secret_key)

# Specify the full paths to the JSON files
students_json_path = os.path.join(current_directory, 'student_data/student.json')
teachers_json_path = os.path.join(current_directory, 'teacher_data/teacher.json')
questions_json_path = os.path.join(current_directory, 'questions/questions.json')

# Declare a dictionary to store teacher-student assignments
teacher_student_assignments = {}

# Load sample user data (student.json) and question data (questions.json)
with open(students_json_path, 'r') as students_data:
    students = json.load(students_data)

with open(teachers_json_path, 'r') as teachers_data:
    teachers = json.load(teachers_data)

with open(questions_json_path, 'r') as questions_file:
    questions = json.load(questions_file)


def is_authenticated():
    return 'username' in session  # Return True if 'username' is in the session


@app.route('/')
def homepage():
    return render_template('landingPage.html', user_authenticated=is_authenticated())


@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Received username: {username}, password: {password}")

        # Simplified authentication (replace with your authentication logic)
        if username in students and students[username]['password'] == password:
            session['username'] = username

            # Check for a teacher assigned to the student's class
            student_class = students[username]['class']
            assigned_teacher = get_teacher_for_class(student_class)

            if assigned_teacher:
                session['assigned_teacher'] = assigned_teacher

            return redirect(url_for('student_dashboard'))

        return render_template('student/login.html', error="Invalid credentials", user_authenticated=is_authenticated())

    return render_template('student/login.html')


def get_teacher_for_class(student_class):
    for teacher, teacher_data in teachers.items():
        if 'class' in teacher_data and teacher_data['class'] == student_class:
            return teacher
    return None


@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Received username: {username}, password: {password}")

        # Simplified authentication (replace with your authentication logic)
        if username in teachers and teachers[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('teacher_dashboard'))

        return render_template('teacher/login.html', error="Invalid credentials", user_authenticated=is_authenticated())

    return render_template('teacher/login.html')


@app.route('/student/dashboard')
def student_dashboard():
    if 'username' in session:
        username = session['username']
        student_data = students.get(username, {})  # Get the user's data
        student_class = student_data.get('class', 'N/A')  # Default to 'N/A' if 'class' data is not present
        student_name = student_data.get('name', 'N/A')
        student_score = student_data.get('score', 'N/A')

        return render_template('student/dashboard.html', username=username, student_class=student_class,
                               student_name=student_name, student_score=student_score)
    else:
        return redirect(url_for('student/login'))


@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'username' in session:
        username = session['username']
        teacher_data = teachers.get(username, {})  # Get the user's data
        teacher_class = teacher_data.get('class', 'N/A')  # Default to 'N/A' if 'class' data is not present
        teacher_subject = teacher_data.get('subject', 'N/A')

        return render_template('teacher/dashboard.html', username=username, teacher_class=teacher_class,
                               teacher_subject=teacher_subject)
    else:
        return redirect(url_for('teacher/login'))


@app.route('/teacher/manage_student')
def manage_student():
    if 'username' in session:
        teacher_username = session['username']
        assigned_class = teachers[teacher_username]['class']

        # Filter students based on class
        filtered_students = {username: student_data for username, student_data in students.items() if
                             student_data.get('class') == assigned_class}

        return render_template('teacher/manage_student.html', username=teacher_username, students=filtered_students)
    else:
        return redirect(url_for('teacher_login'))


@app.route('/student/exam_page')
def exam_page():
    return render_template('student/exam_page.html')


@app.route('/student/start_exam')
def start_exam():
    if 'username' in session:
        return render_template('student/exam.html', questions=questions)
    else:
        return redirect(url_for('login'))


@app.route('/student/submit_exam', methods=['POST'])
def submit_exam():
    if 'username' in session:
        if request.form.get('exam_submission') == '1':
            # Calculate the score based on the user's answers
            score = calculate_score(request.form)

            # Store the score in the session
            session['score'] = score

            # Save the score to the JSON file
            save_score(session['username'], score)

            return redirect(url_for('show_score'))
    return redirect(url_for('student/login'))


def calculate_score(form_data):
    # Calculate the score based on the user's answers
    score = 0
    for question_id, question_data in questions.items():
        user_answer = form_data.get('answer_' + question_id)
        correct_answer = question_data['correct_answer']
        if user_answer == correct_answer:
            score += 1
    return score


@app.route('/show_score')
def show_score():
    if 'username' in session:
        score = session.get('score')
        if score is not None:
            return render_template('student/score.html', score=score)
    return redirect(url_for('student_login'))


def save_score(username, score):
    # Load the existing JSON data
    with open(students_json_path, 'r') as students_data:
        students = json.load(students_data)

    # Update the user's score
    if username in students:
        students[username]['score'] = score

    # Write the updated data back to the JSON file
    with open(students_json_path, 'w') as students_data:
        json.dump(students, students_data, indent=4)


@app.route('/student/logout')
def student_logout():
    session.pop('username', None)
    return redirect(url_for('student_login'))


@app.route('/teacher/logout')
def teacher_logout():
    session.pop('username', None)
    return redirect(url_for('teacher_login'))


@app.route('/upload_form')
def upload_form():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'question-file' not in request.files:
        return "No file part"

    file = request.files['question-file']

    if file.filename == '':
        return "No selected file"

    if file:
        # Here, you can process the uploaded file (e.g., parse a CSV file with questions)
        # You can add your logic to store the questions in a database or perform other actions.
        # For simplicity, we'll just print the contents of the file.

        file_contents = file.read()
        print(file_contents.decode())

        return "File uploaded and processed successfully"


if __name__ == '__main__':
    app.run(debug=True)
