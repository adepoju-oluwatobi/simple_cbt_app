from flask import Flask, render_template, flash, request, redirect, url_for, session
from . import *  # Import the student_routes blueprint


@teacher_routes.route('/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_authenticated = True
        user_role = "teacher"

        print(f"Received username: {username}, password: {password}")

        # Simplified authentication (replace with your authentication logic)
        if username in teachers and teachers[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('teacher_routes.teacher_dashboard'))

        return render_template('teacher/login.html', error="Invalid credentials", user_authenticated=user_authenticated,
                               user_role=user_role)

    return render_template('teacher/login.html')


@teacher_routes.route('/dashboard')
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


# Load student data from student.json file
def load_student_data():
    with open('student_data/student.json', 'r') as student_file:
        student_data = json.load(student_file)
    return student_data


@teacher_routes.route('manage_student')
def manage_student():
    if 'username' in session:
        teacher_username = session['username']
        assigned_class = teachers[teacher_username]['class']

        # Load the updated student data from the JSON file
        student = load_student_data()

        # Filter students based on class
        filtered_students = {username: student_data for username, student_data in student.items() if
                             student_data.get('class') == assigned_class}

        return render_template('teacher/manage_student.html', username=teacher_username, students=filtered_students)
    else:
        return redirect(url_for('teacher_login'))


@teacher_routes.route('/subject_scores/<subject>')
def subject_scores(subject):
    # Get the class information from the request
    class_name = request.args.get('class')

    # Load student data from the JSON file
    student = load_student_data()

    # Create a list to store student data with scores for the selected subject and class
    students_with_scores = []

    for username, student in student.items():
        if student.get('class') == class_name and 'scores' in student and subject in student['scores']:
            students_with_scores.append({
                'username': username,
                'name': student['name'],
                'class': student['class'],
                'score': student['scores'][subject]
            })

    return render_template('teacher/subject_scores.html', subject=subject, students=students_with_scores)


@teacher_routes.route('/manage_cbt')
def manage_cbt():
    # Load student data from the JSON file
    student = load_student_data()

    return render_template('teacher/manage_cbt.html', students=student)


@teacher_routes.route('/submit_exam', methods=['GET', 'POST'])
def submit_exam():
    if request.method == 'POST':
        # Get the data from the form
        description = request.form['description']
        class_name = request.form['class']
        subject = request.form['subject']
        date = request.form['date']
        time = request.form['time']
        duration = request.form['duration']

        # Create a new subject entry in the 'questions' dictionary
        if class_name not in questions:
            questions[class_name] = {}

        # Create a new subject entry within the class
        questions[class_name][subject] = {
            'description': description,
            'date': date,
            'time': time,
            'duration': duration,
            'questions': {}
        }

        # Load the existing questions for the subject
        subject_questions = questions[class_name][subject]['questions']

        # Loop through the request form data to extract questions
        num_questions = int(request.form['num_questions'])
        for i in range(1, num_questions + 1):
            question = request.form[f'question_{i}']
            options = request.form[f'options_{i}'].split(',')
            correct_answer = request.form[f'correct_answer_{i}']

            # Create a new question entry within the subject's questions
            subject_questions[i] = {
                'question': question,
                'options': options,
                'correct_answer': correct_answer
            }

        # Save the entire questions dictionary back to the 'questions.json' file
        save_questions()

        return redirect(url_for('teacher_routes.manage_cbt'))

    return render_template('teacher/create_question.html')


def save_questions():
    # Save the questions data to the JSON file
    with open(questions_json_path, 'w') as questions_file:
        json.dump(questions, questions_file, indent=4)


def load_available_exams():
    # Load available exams data from 'questions.json' file
    exams_data = {}

    # Load questions data from the 'questions.json' file
    with open('questions/questions.json', 'r') as questions_file:
        questions = json.load(questions_file)

    # Iterate through the questions data to organize it by class and subject
    for class_name, class_data in questions.items():
        exams_data[class_name] = {}
        for subject, exams in class_data.items():
            exams_data[class_name][subject] = {}
            for exam_id, exam_name in exams.items():
                exams_data[class_name][subject][exam_id] = exam_name

    return exams_data


@teacher_routes.route('/available_exams')
def available_exams():
    # Load your available exams data
    exams_data = load_available_exams()

    return render_template('teacher/available_exam.html', exams_data=exams_data)


# Load questions from the JSON file
def load_questions():
    with open(questions_json_path, 'r') as questions_data:
        questions = json.load(questions_data)
    return questions


def get_questions_for_class(class_name):
    questions = load_questions()
    class_data = questions.get(class_name, {})
    return class_data


def get_questions_for_class_subject(class_name, subject):
    # Load the existing questions data from the 'questions.json' file
    with open(questions_json_path, 'r') as questions_file:
        questions = json.load(questions_file)

    # Check if the class_name and subject exist in the questions data
    if class_name in questions and subject in questions[class_name]:
        return questions[class_name][subject]
    else:
        return {}


def get_question_details(class_name, subject, question_id):
    # Load the existing questions from the questions.json file
    with open(questions_json_path, 'r') as questions_file:
        questions = json.load(questions_file)

    # Check if the class_name and subject exist in the questions data
    if class_name in questions and subject in questions[class_name]:
        question_data = questions[class_name][subject].get(question_id)

        # Check if the question_id exists in the specified class and subject
        if question_data:
            return question_data

    # Return None if the question details were not found
    return None


# Function to update questions for a specific class and subject
def update_questions_for_class_subject(class_name, subject, edited_questions_data, edited_details):
    # Load the existing questions from the 'questions.json' file
    with open(questions_json_path, 'r') as questions_file:
        questions = json.load(questions_file)

    # Check if the class_name and subject exist in the questions data
    if class_name in questions and subject in questions[class_name]:
        # Update the details (date, time, duration)
        questions[class_name][subject]['description'] = edited_details['description']
        questions[class_name][subject]['date'] = edited_details['date']
        questions[class_name][subject]['time'] = edited_details['time']
        questions[class_name][subject]['duration'] = edited_details['duration']

        # Update the questions
        for question_id, edited_data in edited_questions_data.items():
            questions[class_name][subject]['questions'][question_id] = edited_data

        # Save the updated questions data back to the 'questions.json' file
        with open(questions_json_path, 'w') as questions_file:
            json.dump(questions, questions_file, indent=4)


# Route to edit questions and details
@teacher_routes.route('/edit_exam/<class_name>/<subject>', methods=['GET', 'POST'])
def edit_exam(class_name, subject):
    if request.method == 'POST':
        # Handle form submission and save the edited questions and details
        edited_details = {
            'description': request.form['description'],
            'date': request.form['date'],
            'time': request.form['time'],
            'duration': request.form['duration']
        }
        edited_questions_data = {}
        for key, value in request.form.items():
            if key.startswith('question_'):
                question_id = key.replace('question_', '')
                edited_questions_data[question_id] = {
                    'question': request.form[f'question_{question_id}'],
                    'options': request.form[f'options_{question_id}'].split(', '),
                    'correct_answer': request.form[f'correct_answer_{question_id}']
                }

        # Update the questions and details for the specified class and subject
        update_questions_for_class_subject(class_name, subject, edited_questions_data, edited_details)

        return redirect(url_for('teacher_routes.available_exams'))

    class_subject_details = get_questions_for_class_subject(class_name, subject)
    questions_data = class_subject_details['questions']
    return render_template('teacher/edit_questions.html', class_name=class_name, subject=subject,
                           questions_data=questions_data, details=class_subject_details)


@teacher_routes.route('/delete_exam/<class_name>/<subject>')
def delete_exam(class_name, subject):
    # Load your questions JSON data
    with open(questions_json_path, 'r') as questions_file:
        questions = json.load(questions_file)

    if class_name in questions and subject in questions[class_name]:
        # Delete the subject data
        del questions[class_name][subject]

        # Save the updated data back to the JSON file
        with open(questions_json_path, 'w') as questions_file:
            json.dump(questions, questions_file, indent=4)

        success_message = f"Subject '{subject}' in class '{class_name}' has been deleted."
        flash(success_message, 'success')
    else:
        error_message = f"Subject '{subject}' in class '{class_name}' not found."
        flash(error_message, 'error')

    return redirect(url_for('teacher_routes.available_exams'))


@teacher_routes.route('/logout')
def teacher_logout():
    session.pop('username', None)
    return redirect(url_for('teacher_routes.teacher_login'))
