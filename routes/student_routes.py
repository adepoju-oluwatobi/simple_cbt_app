from flask import Flask, render_template, flash, request, redirect, url_for, session
from . import *  # Import the student_routes blueprint


@student_routes.route('/login', methods=['GET', 'POST'])
def student_login():
    user_authenticated = True
    user_role = "student"

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Received username: {username}, password: {password}")

        # Simplified authentication (replace with your authentication logic)
        if username in students and students[username]['password'] == password:
            session['username'] = username

            student_class = students[username]['class']
            assigned_teacher = get_teacher_for_class(student_class)

            if assigned_teacher:
                session['assigned_teacher'] = assigned_teacher

            return redirect(url_for('student_routes.student_dashboard'))

        return render_template('student/login.html',
                               error="Invalid credentials, check your login details and try again.",
                               user_authenticated=user_authenticated, user_role=user_role)

    return render_template('student/login.html', user_authenticated=user_authenticated, user_role=user_role)


def get_teacher_for_class(student_class):
    for teacher, teacher_data in teachers.items():
        if 'class' in teacher_data and teacher_data['class'] == student_class:
            return teacher
    return None


@student_routes.route('/dashboard')
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


@student_routes.route('/available_tests')
def available_tests():
    if 'username' in session:
        username = session['username']
        student_data = students.get(username, {})
        student_class = student_data.get('class', '')

        # Load your questions JSON data
        all_questions = load_questions()

        # Filter questions based on the student's class
        class_questions = all_questions.get(student_class, {})

        # Extract the test data (date, time, duration) for each subject
        test_data = {
            subject: {
                "date": subject_data.get("date"),
                "time": subject_data.get("time"),
                "duration": subject_data.get("duration")
            }
            for subject, subject_data in class_questions.items()
        }

        return render_template('student/available_tests.html', subjects=class_questions.keys(), test_data=test_data,
                               student_class=student_class)

    return redirect(url_for('student/login'))


# Load questions from the JSON file
def load_questions():
    with open(questions_json_path, 'r') as questions_data:
        question = json.load(questions_data)
    return question


@student_routes.route('/start_exam/<class_name>/<subject>')
def start_exam(class_name, subject):
    if 'username' in session:
        student_username = session['username']
        student_data = students.get(student_username, {})
        student_class = student_data.get('class', '')

        # Check if the student's class matches the specified class_name
        if student_class == class_name:
            # Load questions from the JSON file
            all_questions = load_questions()

            # Check if the subject exists in the questions data
            if class_name in all_questions and subject in all_questions[class_name]:
                subject_data = all_questions[class_name][subject]

                # Extract test data: date, time, duration, and questions
                test_date = subject_data.get("date")
                test_time = subject_data.get("time")
                test_duration = subject_data.get("duration")
                questions_for_class_subject = subject_data.get("questions")

                if questions_for_class_subject:
                    return render_template('student/exam.html', questions=questions_for_class_subject, subject=subject,
                                           test_date=test_date, test_time=test_time, test_duration=test_duration)
                else:
                    return "No questions found for the specified subject"
            else:
                return "Subject not found in questions data."
        else:
            return "Unauthorized access to this subject"
    else:
        return redirect(url_for('student/login'))


@student_routes.route('/submit_exam', methods=['POST'])
def submit_exam():
    if 'username' in session:
        if request.method == 'POST':
            if 'exam_submission' in request.form and request.form['exam_submission'] == '1':
                subject = request.form['subject']
                user_answers = request.form.to_dict(flat=False)

                # Calculate the score for the exam
                score = calculate_score(user_answers, subject)

                # Save the score to the session
                session['score'] = score

                # Save the score to the JSON file
                save_score(session['username'], subject, score)

                return redirect(url_for('student_routes.show_score', subject=subject))
            else:
                return "Invalid exam submission. Please try again."

    # Redirect to the login page if the user is not logged in
    return redirect(url_for('student_routes.student_login'))


# Load student data from student.json file
def load_student_data():
    with open('student_data/student.json', 'r') as student_file:
        student_data = json.load(student_file)
    return student_data


def calculate_score(user_answers, subject):
    student = load_student_data()
    username = session.get('username')
    score = 0  # Initialize the score

    if username in student:
        student_data = student[username]
        student_scores = student_data.get('scores', {})

        # Load the questions for the specified subject from your JSON data
        subject_data = load_questions().get(student_data['class'], {}).get(subject, {})

        for question_id, question_data in subject_data.get("questions", {}).items():
            user_answer = user_answers.get(f'answer_{question_id}')
            correct_answer = question_data.get('correct_answer')

            print(f"Question {question_id}: User's answer - {user_answer}, Correct answer - {correct_answer}")

            if user_answer and user_answer[0] == correct_answer:
                score += 1

        print(f"Total score for {username} in {subject}: {score}")

        student_scores[subject] = score
        student_data['scores'] = student_scores
        student[username] = student_data

        with open(students_json_path, 'w') as students_data_file:
            json.dump(student, students_data_file, indent=4)

    return score



@student_routes.route('/show_score/<subject>')
def show_score(subject):
    if 'username' in session:
        username = session['username']
        score = get_student_score(username, subject)
        if score is not None:
            return render_template('student/score.html', subject=subject, score=score)
        else:
            return "No score found for the specified subject"
    return redirect(url_for('student_routes.student_login'))


def get_student_score(username, subject):
    # Load the student data from the JSON file
    with open(students_json_path, 'r') as students_data_file:
        student_data = json.load(students_data_file)

    # Get the user's data
    user_data = student_data.get(username, {})
    if 'scores' in user_data:
        scores = user_data['scores']
        return scores.get(subject, 'N/A')  # Return the score for the specified subject
    return 'N/A'


def save_score(username, subject, score):
    # Load the existing student data from the JSON file
    with open(students_json_path, 'r') as students_data_file:
        student = json.load(students_data_file)

    # Update the user's score for the specific subject
    if username in student:
        if 'scores' not in student[username]:
            student[username]['scores'] = {}

        student[username]['scores'][subject] = score

    # Write the updated data back to the JSON file
    with open(students_json_path, 'w') as students_data_file:
        json.dump(student, students_data_file, indent=4)

    print(f"Saved score for {username} in {subject}: {score}")  # Add this line


@student_routes.route('/logout')
def student_logout():
    session.pop('username', None)
    return redirect(url_for('student_routes.student_login'))
