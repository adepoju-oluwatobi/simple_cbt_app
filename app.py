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


@app.route('/available_tests')
def available_tests():
    if 'username' in session:
        username = session['username']
        student_data = students.get(username, {})
        student_class = student_data.get('class', '')  # Get the student's class from the session

        # Load your questions JSON data
        with open('questions/questions.json', 'r') as questions_file:
            all_questions = json.load(questions_file)

        # Filter questions based on the student's class
        class_questions = all_questions.get(student_class, {})  # Assumes class names match keys in questions.json

        return render_template('student/available_tests.html', subjects=class_questions.keys(),
                               student_class=student_class)

    return redirect(url_for('student/login'))


# Function to get questions for a specific class
def get_questions_for_class(class_name):
    questions = load_questions()
    class_data = questions.get(class_name, {})
    return class_data


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


# Load questions from the JSON file
def load_questions():
    with open(questions_json_path, 'r') as questions_data:
        questions = json.load(questions_data)
    return questions


# Function to get questions for a specific class and subject
def get_questions_for_class_subject(class_name, subject):
    questions = load_questions()
    class_data = questions.get(class_name, {})
    subject_data = class_data.get(subject, {})
    return subject_data


@app.route('/start_exam/<class_name>/<subject>')
def start_exam(class_name, subject):
    if 'username' in session:
        student_username = session['username']
        student_data = students.get(student_username, {})
        student_class = student_data.get('class', '')

        # Check if the student's class matches the specified class_name
        if student_class == class_name:
            questions_for_class_subject = get_questions_for_class_subject(class_name, subject)
            if questions_for_class_subject:
                return render_template('student/exam.html', questions=questions_for_class_subject, subject=subject)
            else:
                return "No questions found for the specified subject"
        else:
            return "Unauthorized access to this subject"
    else:
        return redirect(url_for('student/login'))


@app.route('/student/submit_exam', methods=['POST'])
def submit_exam():
    if 'username' in session:
        if request.method == 'POST':
            if 'exam_submission' in request.form and request.form['exam_submission'] == '1':
                subject = request.form['subject']
                user_answers = request.form.to_dict(flat=False)
                score = calculate_score(user_answers, subject)
                session['score'] = score

                # Save the score to the JSON file
                save_score(session['username'], subject, score)
                print(score)
                return redirect(url_for('show_score', subject=subject)
                                )

    return redirect(url_for('student_login'))


def calculate_score(user_answers, subject):
    # Load the existing student data from the JSON file
    global score
    students = load_student_data()

    # Get the username from the session
    username = session.get('username')

    if username:
        # Check if the username exists in the students data
        if username in students:
            student_data = students[username]
            student_scores = student_data.get('scores', {})

            # Load the questions for the specified subject from your JSON data
            subject_data = questions.get(student_data['class'], {}).get(subject, {})

            # Initialize the score
            score = 0

            for question_id, question_data in subject_data.items():
                user_answer = user_answers.get(f'answer_{question_id}')
                correct_answer = question_data.get('correct_answer')

                if user_answer and user_answer[0] == correct_answer:
                    score += 1

            # Update the user's score for the specific subject
            student_scores[subject] = score

            # Update the student's data with the new scores
            student_data['scores'] = student_scores
            students[username] = student_data

            # Write the updated data back to the JSON file
            with open(students_json_path, 'w') as students_data_file:
                json.dump(students, students_data_file, indent=4)

    return score


@app.route('/show_score/<subject>')
def show_score(subject):
    if 'username' in session:
        username = session['username']
        score = get_student_score(username, subject)
        if score is not None:
            return render_template('student/score.html', subject=subject, score=score)
        else:
            return "No score found for the specified subject"
    return redirect(url_for('student_login'))


def get_student_score(username, subject):
    # Load the student data from the JSON file
    with open(students_json_path, 'r') as students_data_file:
        students_data = json.load(students_data_file)

    # Get the user's data
    user_data = students_data.get(username, {})
    if 'scores' in user_data:
        scores = user_data['scores']
        return scores.get(subject, 'N/A')  # Return the score for the specified subject
    return 'N/A'  # If user data or scores not found, return 'N/A'


def save_score(username, subject, score):
    # Load the existing student data from the JSON file
    with open(students_json_path, 'r') as students_data_file:
        students = json.load(students_data_file)

    # Update the user's score for the specific subject
    if username in students:
        if 'scores' not in students[username]:
            students[username]['scores'] = {}

        students[username]['scores'][subject] = score

    # Write the updated data back to the JSON file
    with open(students_json_path, 'w') as students_data_file:
        json.dump(students, students_data_file, indent=4)


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


# Load student data from student.json file
def load_student_data():
    with open('student_data/student.json', 'r') as student_file:
        student_data = json.load(student_file)
    return student_data


@app.route('/subject_scores/<subject>')
def subject_scores(subject):
    # Get the class information from the request
    class_name = request.args.get('class')

    # Load student data from the JSON file
    students = load_student_data()

    # Create a list to store student data with scores for the selected subject and class
    students_with_scores = []

    for username, student in students.items():
        if student.get('class') == class_name and 'scores' in student and subject in student['scores']:
            students_with_scores.append({
                'username': username,
                'name': student['name'],
                'class': student['class'],
                'score': student['scores'][subject]
            })

    return render_template('teacher/subject_scores.html', subject=subject, students=students_with_scores)


@app.route('/teacher/manage_grades')
def manage_grades():
    # Load student data from the JSON file
    students = load_student_data()

    return render_template('teacher/manage_grades.html', students=students)


import json


@app.route('/submit_question', methods=['GET', 'POST'])
def submit_question():
    if request.method == 'POST':
        # Handle form submission and save the new questions
        class_name = request.form['class']
        subject = request.form['subject']
        num_questions = int(request.form['num_questions'])

        # Load the existing questions from questions.json
        with open(questions_json_path, 'r') as questions_file:
            questions = json.load(questions_file)

        # Create a list to store the new question data
        new_questions_data = []

        for i in range(1, num_questions + 1):
            question = request.form[f'question_{i}']
            options = request.form[f'options_{i}'].split(',')
            correct_answer = request.form[f'correct_answer_{i}']

            # Create new question data
            new_question_data = {
                'question': question,
                'options': options,
                'correct_answer': correct_answer
            }

            # Append the new question data to the appropriate class and subject
            if class_name not in questions:
                questions[class_name] = {}  # Create a new class if it doesn't exist

            if subject not in questions[class_name]:
                questions[class_name][subject] = {}  # Create a new subject if it doesn't exist

            # Find the next question number (e.g., "1", "2", "3")
            question_number = str(len(questions[class_name][subject]) + 1)

            # Add the new question with the next available number
            questions[class_name][subject][question_number] = new_question_data

            # Append the new question data to the list
            new_questions_data.append(new_question_data)

        # Save the updated questions back to questions.json
        with open(questions_json_path, 'w') as questions_file:
            json.dump(questions, questions_file, indent=4)

        return render_template('teacher/create_question.html', new_questions_data=new_questions_data)

    # If it's a GET request, display the create_question.html form
    return render_template('teacher/create_question.html')


def save_questions():
    # Save the updated question data to the JSON file
    with open(questions_json_path, 'w') as questions_file:
        json.dump(questions, questions_file, indent=4)


if __name__ == '__main__':
    app.run(debug=True)
