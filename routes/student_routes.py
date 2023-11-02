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
        # Default to 'N/A' if 'class' data is not present
        student_class = student_data.get('class', 'N/A')
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

        # Debug prints
        print(f"Student Data: {student_data}")
        print(f"Completed Subjects: {student_data.get('completed_subjects', [])}")

        # Load your questions JSON data
        all_questions = load_questions()

        # Debug print
        print(f"All Questions: {all_questions}")

        # Filter questions based on the student's class
        class_questions = all_questions.get(student_class, {})

        # Debug print
        print(f"Class Questions: {class_questions}")

        # Initialize a dictionary to store the progress
        exam_progress = {}

        for subject, subject_data in class_questions.items():
            description = subject_data.get("description")

            # Debug print
            print(f"Checking progress for subject: {description}")

            # Calculate the progress based on the number of completed exams
            max_exams = subject_data.get("max_exams")

            if is_subject_completed(student_data, description, max_exams):
                progress = 100  # Subject completed
            else:
                progress = 0  # Subject not yet completed

            exam_progress[description] = progress

        # Debug print
        print(f"Exam Progress: {exam_progress}")

        # Extract the test data (date, time, duration) for each subject
        test_data = {
            subject: {
                "description": subject_data.get("description"),
                "date": subject_data.get("date"),
                "time": subject_data.get("time"),
                "duration": subject_data.get("duration")
            }
            for subject, subject_data in class_questions.items()
        }

        # Debug print
        print(f"Test Data: {test_data}")

        # Count the number of completed subjects
        num_completed_subjects = len(student_data.get('completed_subjects', []))

        return render_template('student/available_tests.html', subjects=class_questions.keys(), test_data=test_data,
                               student_class=student_class, exam_progress=exam_progress,
                               num_completed_subjects=num_completed_subjects, completed_subjects=student_data.get('completed_subjects', []))

    return redirect(url_for('student/login'))



def get_completed_subjects(student_data, class_questions):
    completed_subjects = []
    for subject, subject_data in class_questions.items():
        description = subject_data.get("description")
        max_exams = subject_data.get("max_exams")

        if is_subject_completed(student_data, description, max_exams):
            completed_subjects.append(description)

    return completed_subjects


def is_subject_completed(student_data, subject, max_exams):
    if max_exams is not None:
        if subject in student_data.get('completed_subjects', []):
            return True
        completed_exams = student_data.get('completed_exams', {}).get(subject, 0)
        return completed_exams >= max_exams
    return False


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


def get_subject_description(subject):
    # Replace this with your actual code to retrieve the description
    # You should extract the description from your questions data
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
                all_questions = load_questions()
                max_exams = all_questions.get(student_data['class'], {}).get(subject, {}).get('max_exams')

                # Update the progress in the student's data
                progress = calculate_progress(student_data, subject, max_exams)

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



def calculate_progress(student_data, subject, max_exams):
    # Check if 'completed_exams' key is present in student_data
    if 'completed_exams' in student_data:
        completed_exams = student_data['completed_exams'].get(subject, 0)
        if max_exams is not None:
            progress = (completed_exams / max_exams) * 100
        else:
            # Handle the case where max_exams is None
            progress = 0  # You can choose an appropriate default value or handle it differently
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