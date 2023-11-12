from datetime import datetime

from flask import request, redirect, url_for

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

            # Initialize completed_subjects list
            student_data = students.get(username, {})
            if 'completed_subjects' not in student_data:
                student_data['completed_subjects'] = []

            student_class = student_data['class']
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

        student_class = student_data.get('class', 'N/A')
        student_name = student_data.get('name', 'N/A')
        student_score = student_data.get('score', 'N/A')

        return render_template('student/dashboard.html', username=username, student_class=student_class,
                               student_name=student_name, student_score=student_score)
    else:
        return redirect(url_for('student/login'))


import json


@student_routes.route('/available_tests')
def available_tests():
    if 'username' in session:
        username = session['username']
        student_data = students.get(username, {})
        student_class = student_data.get('class', '')
        progress = student_data.get('progress', {})

        if not isinstance(progress, dict):
            progress = {}  # Initialize as an empty dictionary if it's not already

        # Load your questions JSON data
        all_questions = load_questions()
        # Get class-specific questions and max exams
        class_questions = all_questions.get(student_class, {})

        # Create a dictionary to store progress for each subject
        subject_progress = {
            subject: progress.get(subject, 0)
            for subject in class_questions.keys()
        }

        # Extract the test data (date, time, duration) for each subject
        test_data = {
            subject: {
                "description": subject_data.get("description"),
                "date": subject_data.get("date"),
                "time": subject_data.get("time"),
                "duration": subject_data.get("duration"),
            }
            for subject, subject_data in class_questions.items()
        }

        # Check if the message is not empty, and if so, show the warning message.
        message = ""
        if "message" in session:
            message = session.pop("message")

        return render_template('student/available_tests.html', subjects=class_questions.keys(), test_data=test_data,
                               student_class=student_class, message=message, progress=subject_progress)

    return redirect(url_for('student_routes.student_login'))


def is_subject_completed(student_data, subject, max_exams):
    if max_exams is not None:
        if subject in student_data.get('completed_subjects', []):
            return True
        completed_exams = student_data.get('completed_exams', {}).get(subject, 0)
        return completed_exams >= max_exams
    return False


def get_completed_subjects(student_data, class_questions):
    completed_subjects = []
    for subject, subject_data in class_questions.items():
        description = subject_data.get("description")
        max_exams = 1

        if is_subject_completed(student_data, description, max_exams):
            completed_subjects.append(description)

    return completed_subjects


# Load questions from the JSON file
def load_questions():
    with open(questions_json_path, 'r') as questions_data:
        question = json.load(questions_data)
    return question


@student_routes.route('/instruction')
def instruction():
    if 'username' in session:
        pass

        # Load your questions JSON data
        # Get class-specific questions and max exams

        # Extract the test data (date, time, duration) for each subject

    return render_template('student/instruction.html')


@student_routes.route('/start_exam/<class_name>/<subject>')
def start_exam(class_name, subject):
    if 'username' in session:
        username = session['username']
        student_data = students.get(username, {})
        student_class = student_data.get('class', '')

        # Check if the student's class matches the specified class_name
        if student_class == class_name:
            # Load questions from the JSON file
            all_questions = load_questions()

            # Check if the subject exists in the questions data
            if class_name in all_questions and subject in all_questions[class_name]:
                subject_data = all_questions[class_name][subject]

                # Check if the student has already completed the exam for this subject
                if has_student_completed_exam(student_data, subject):
                    message = "You have already completed this exam. You cannot retake it."
                    return render_template('student/alert.html', message=message)

                # Extract exam date and time
                exam_date_str = subject_data.get("date")
                exam_time_str = subject_data.get("time")

                # Parse exam date and time strings to datetime objects
                exam_datetime = datetime.strptime(f"{exam_date_str} {exam_time_str}", "%Y-%m-%d %H:%M")

                # Get the current date and time
                current_datetime = datetime.now()

                # Check if the current datetime is after the exam datetime
                if current_datetime >= exam_datetime:
                    # Extract test data: date, time, duration, and questions
                    test_date = subject_data.get("date")
                    test_time = subject_data.get("time")
                    test_duration = subject_data.get("duration")

                    # Split the duration string into hours and minutes
                    hours, minutes = map(int, test_duration.split(':'))

                    # Convert hours and minutes to the total duration in minutes
                    duration = hours * 60 + minutes
                    questions_for_class_subject = subject_data.get("questions")

                    if questions_for_class_subject:
                        return render_template('student/exam.html', questions=questions_for_class_subject,
                                               subject=subject,
                                               test_date=test_date, test_time=test_time, duration=duration)
                    else:
                        message = "No questions found for the specified subject"
                        return render_template('student/alert.html', message=message)
                else:
                    message = "The exam is not accessible until the scheduled date and time."
                    return render_template('student/alert.html', message=message)
            else:
                message = "Subject not found in questions data."
                return render_template('student/alert.html', message=message)
        else:
            message = "Unauthorized access to this subject"
            return render_template('student/alert.html', message=message)
    else:
        return redirect(url_for('student/login'))


def has_student_completed_exam(student_data, subject):
    if 'completed_subjects' in student_data:
        return subject in student_data['completed_subjects']
    return False


def get_subject_description(subject):
    all_questions = load_questions()  # Load your questions data
    subject_data = all_questions.get(subject)  # Change this to get the correct subject data
    if subject_data:
        return subject_data.get("description", "Description not available")
    return "Description not available"


# Update the progress and completed subjects in the 'submit_exam' route
@student_routes.route('/submit_exam', methods=['POST'])
def submit_exam():
    if 'username' in session:
        if request.method == 'POST':
            if 'exam_submission' in request.form and request.form['exam_submission'] == '1':
                subject = request.form['subject']
                user_answers = request.form.to_dict(flat=False)

                # Debug prints to check the submitted data
                print(f"User: {session['username']} submitted exam for subject: {subject}")
                print(f"User Answers: {user_answers}")

                # Calculate the score for the exam
                score = calculate_score(user_answers, subject)

                # Load the student's data
                student_data = students.get(session['username'], {})

                # Debug print to check the student's data
                print(f"Student Data: {student_data}")

                # Update the number of completed exams
                if 'completed_exams' not in student_data:
                    student_data['completed_exams'] = {}

                if subject not in student_data['completed_exams']:
                    student_data['completed_exams'][subject] = 1
                else:
                    student_data['completed_exams'][subject] += 1

                # Debug print to check completed exams
                print(f"Completed Exams: {student_data.get('completed_exams')}")

                # Load questions data

                # Update the progress in the student's data
                progress = calculate_progress(student_data, subject)

                if 'progress' not in student_data:
                    student_data['progress'] = {}

                student_data['progress'][subject] = progress

                # Debug print to check the updated progress
                print(f"Updated Progress: {student_data['progress']}")

                # Save the updated student data
                students[session['username']] = student_data

                # Save the score and progress to the JSON file
                save_score(session['username'], subject, score, student_data['progress'])

                session['score'] = score

                return redirect(url_for('student_routes.show_score', subject=subject))
            else:
                return "Invalid exam submission. Please try again."

    # Redirect to the login page if the user is not logged in
    return redirect(url_for('student_routes.student_login'))


def calculate_progress(student_data, subject):
    max_exams = 1
    # Check if 'completed_exams' key is present in student_data
    if 'completed_exams' in student_data:
        completed_exams = student_data['completed_exams'].get(subject, 0)
        if max_exams is not None:
            # Calculate progress as a percentage, clamped between 0% and 100%
            progress = min((completed_exams / max_exams) * 100, 100)
        else:
            # Handle the case where max_exams is None (no maximum limit)
            progress = (completed_exams / 2) * 100  # Replace '2' with the appropriate maximum limit
    else:
        # Handle the case where 'completed_exams' key is not present
        progress = 0  # Set progress to 0 or handle it differently

    return progress


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
        subject_data = load_questions().get(
            student_data['class'], {}).get(subject, {})

        for question_id, question_data in subject_data.get("questions", {}).items():
            user_answer = user_answers.get(f'answer_{question_id}')
            correct_answer = question_data.get('correct_answer')

            print(
                f"Question {question_id}: User's answer - {user_answer}, Correct answer - {correct_answer}")

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
    global subject_data
    if 'username' in session:
        username = session['username']
        student_data = students.get(username, {})
        student_class = student_data.get('class', '')

        # Load your questions JSON data
        all_questions = load_questions()

        if student_class in all_questions and subject in all_questions[student_class]:
            subject_data = all_questions[student_class][subject]

        score = get_student_score(username, subject)
        total_questions = len(subject_data.get("questions", {}))

        if score is not None:
            return render_template('student/score.html', subject=subject, score=score, total_questions=total_questions)
        else:
            return "No score found for the specified subject"
    return redirect(url_for('student_routes.student_login'))


def get_student_score(username, subject):
    # Load the student data from the JSON file
    try:
        with open(students_json_path, 'r') as students_data_file:
            student_data = json.load(students_data_file)
    except Exception as e:
        print(f"Error loading student data from JSON file: {e}")
        return 'N/A'

    # Get the user's data
    user_data = student_data.get(username, {})

    if 'scores' in user_data:
        scores = user_data['scores']

        # Check if the subject score exists
        if subject in scores:
            return scores[subject]

    return 'N/A'


# Save the score and progress to the JSON file
def save_score(username, subject, score, progress):
    # Load the existing student data from the JSON file
    with open(students_json_path, 'r') as students_data_file:
        student = json.load(students_data_file)

    # Update the user's score for the specific subject
    if username in student:
        if 'scores' not in student[username]:
            student[username]['scores'] = {}
        student[username]['scores'][subject] = score

        # Update the progress
        student[username]['progress'] = progress

    # Write the updated data back to the JSON file
    with open(students_json_path, 'w') as students_data_file:
        json.dump(student, students_data_file, indent=4)


@student_routes.route('/logout')
def student_logout():
    session.pop('username', None)
    return redirect(url_for('student_routes.student_login'))
