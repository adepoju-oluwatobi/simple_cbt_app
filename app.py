from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

# Get the current directory of your Python script
current_directory = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'username'  # Replace with your own secret key
print(app.secret_key)

# Specify the full paths to the JSON files
students_json_path = os.path.join(current_directory, 'student.json')
questions_json_path = os.path.join(current_directory, './questions.json')

# Load sample user data (student.json) and question data (questions.json)
with open(students_json_path, 'r') as students_data:
    students = json.load(students_data)

with open(questions_json_path, 'r') as questions_file:
    questions = json.load(questions_file)


@app.route('/*')
def universal(page):
    return render_template('header.html')


@app.route('/')
def homepage():
    return render_template('landingPage.html')


@app.route('/student/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Received username: {username}, password: {password}")

        # Simplified authentication (replace with your authentication logic)
        if username in students and students[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))

        return render_template('student/login.html', error="Invalid credentials")

    return render_template('student/login.html')


@app.route('/student/dashboard')
def dashboard():
    if 'username' in session:
        username = session['username']
        student_data = students.get(username, {})  # Get the user's data
        student_class = student_data.get('class', 'N/A')  # Default to 'N/A' if 'class' data is not present

        return render_template('student/dashboard.html', username=username, student_class=student_class)
    else:
        return redirect(url_for('student/login'))


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
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


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
