import random
from flask import request, redirect, url_for, flash
from . import *  # Import the student_routes blueprint
import pandas as pd


def is_authenticated():
    return 'username' in session  # Return True if 'username' is in the session


@admin_routes.route('/login', methods=['GET', 'POST'])
def admin_login():
    user_authenticated = True
    user_role = "admin"

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Received username: {username}, password: {password}")

        # Simplified authentication (replace with your authentication logic)
        if username in admin and admin[username]['password'] == password:
            session['username'] = username

            return redirect(url_for('admin_routes.admin_dashboard'))

        return render_template('admin/login.html', error="Invalid credentials",
                               user_authenticated=user_authenticated, user_role=user_role)

    return render_template('admin/login.html', user_authenticated=user_authenticated, user_role=user_role)


@admin_routes.route('/dashboard')
def admin_dashboard():
    if 'username' in session:
        username = session['username']

        return render_template('admin/dashboard.html', username=username)
    else:
        return redirect(url_for('admin_routes.admin_login'))


def load_students_data():
    with open('student_data/student.json', 'r') as student_file:
        student_data = json.load(student_file)
    return student_data


@admin_routes.route('/manage_student')
def manage_all_students():
    if 'username' in session:
        # Load your student data here (replace with your actual data loading logic)
        student_data = load_students_data()

        return render_template('admin/manage_students.html', students=student_data)
    else:
        return redirect(url_for('admin_routes.admin_login'))


def get_student_data(username):
    # Load student data from the JSON file
    with open(students_json_path, 'r') as students_data_file:
        student_data = json.load(students_data_file)

    # Retrieve the student data by username
    return student_data.get(username)


@admin_routes.route('/edit_student/<username>')
def edit_student(username):
    # Add logic to retrieve the student's data using the username
    # and render the 'edit_student.html' template with the data.
    student = get_student_data(username)
    return render_template('admin/edit_student.html', username=username, student=student)


# Function to update student data
def update_student_data(username, updated_data):
    # Load student data from the JSON file
    with open(students_json_path, 'r') as students_data_file:
        student_data = json.load(students_data_file)

    # Update the student data for the specified username
    if username in student_data:
        student_data[username].update(updated_data)

        # Save the updated data back to the JSON file
        with open(students_json_path, 'w') as students_data_file:
            json.dump(student_data, students_data_file, indent=4)


@admin_routes.route('/save_edited_student/<username>', methods=['POST'])
def save_edited_student(username):
    if request.method == 'POST':
        name = request.form['name']
        student_class = request.form['class']
        parent_name = request.form['parent_name']

        updated_data = {
            'name': name,
            'class': student_class,
            'parent_name': parent_name
        }

        update_student_data(username, updated_data)

        return redirect(url_for('admin_routes.manage_all_students'))
    else:
        return "Invalid request"


def save_students_data(student_data):
    with open(students_json_path, 'w') as students_file:
        json.dump(student_data, students_file, indent=4)


@admin_routes.route('/delete_student/<username>', methods=['GET', 'POST'])
def admin_delete_student(username):
    if request.method == 'POST':
        # Check if the user has confirmed the deletion
        if 'confirm' in request.form:
            # Load the existing student data
            student = load_students_data()

            if username in student:
                # Remove the student with the provided username
                del student[username]

                # Save the updated student data back to the JSON file
                save_students_data(student)

                return redirect(url_for('admin_routes.manage_all_students'))
        else:
            # The user did not confirm the deletion
            return redirect(url_for('admin_routes.manage_all_students'))

    # If it's a GET request, display a confirmation page
    return render_template('admin/confirm_delete_student.html', username=username)


# Add a new route to display the form for adding a new student
@admin_routes.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        # Handle form submission to add the new student
        parent_name = request.form['parent_name']
        name = request.form['name']
        student_class = request.form['class']
        password = request.form['password']

        # Create a new student record (you can add more data fields as needed)
        new_student = {
            'parent_name': parent_name,
            'name': name,
            'class': student_class,
            'password': password,
            'score': 0  # You can set an initial score if needed
        }

        # Load the existing student data from the JSON file
        student_data = load_students_data()

        # Ensure the username is unique (you can add your logic for generating a unique username)
        username = generate_unique_username(name)

        # Add the new student to the dictionary with the unique username
        student_data[username] = new_student

        # Save the updated student data back to the JSON file
        save_students_data(student_data)

        return redirect(url_for('admin_routes.manage_all_students'))
    else:
        return render_template('admin/add_student.html')


# Define a function to generate a unique username (you can customize this logic)
def generate_unique_username(name):
    # generate a random username
    first_name = name.split()[0].lower()
    random_number = random.randint(1000, 9999)
    username = f"{first_name}{random_number}"
    return username


@admin_routes.route('/subject_scores/<subject>')
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

    return render_template('admin/subject_scores.html', subject=subject, students=students_with_scores)


def load_student_data():
    with open('student_data/student.json', 'r') as student_file:
        student_data = json.load(student_file)
    return student_data


@admin_routes.route('/manage_cbt')
def manage_cbt():
    # Load student data from the JSON file
    student = load_student_data()

    return render_template('admin/manage_cbt.html', students=student)


@admin_routes.route('/submit_exam', methods=['GET', 'POST'])
def submit_exam():
    if request.method == 'POST':
        # Check if the request contains a file
        if 'file' in request.files:
            file = request.files['file']
            print(f"File Name: {file.filename}, File Size: {file.content_length}")

            # Save the file to the 'uploads' folder
            file.save('uploads/' + file.filename)

            # Check if the file has a valid extension (you can customize this based on your needs)
            if file and file.filename.endswith('.xlsx'):
                try:
                    # Read the Excel file using pandas
                    df = pd.read_excel(file)

                    # Get the metadata from the form
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

                    # Loop through the DataFrame to extract questions
                    for index, row in df.iterrows():
                        question = row['question']
                        options = row['options'].split(',')
                        correct_answer = row['correct_answer']

                        # Convert the index to an integer
                        index = int(index)

                        # Create a new question entry within the subject's questions
                        subject_questions[index + 1] = {
                            'question': question,
                            'options': options,
                            'correct_answer': correct_answer
                        }

                    # Save the entire questions dictionary back to the 'questions.json' file
                    save_questions()

                    print(f"File Name: {file.filename}, File Size: {file.content_length}")
                    print(f"Request Files: {request.files}")

                    return redirect(url_for('admin_routes.manage_cbt'))

                except Exception as e:
                    # Handle any errors that may occur during file processing
                    return render_template('admin/create_question.html', error=str(e))

        # Continue with your existing code if no file is provided in the request
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

        return redirect(url_for('admin_routes.manage_cbt'))

    return render_template('admin/create_question.html')


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


@admin_routes.route('/available_exams')
def available_exams():
    # Load your available exams data
    exams_data = load_available_exams()

    return render_template('admin/available_exam.html', exams_data=exams_data)


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
@admin_routes.route('/edit_exam/<class_name>/<subject>', methods=['GET', 'POST'])
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
        update_questions_for_class_subject(
            class_name, subject, edited_questions_data, edited_details)

        return redirect(url_for('admin_routes.available_exams'))

    class_subject_details = get_questions_for_class_subject(
        class_name, subject)
    questions_data = class_subject_details['questions']
    return render_template('admin/edit_questions.html', class_name=class_name, subject=subject,
                           questions_data=questions_data, details=class_subject_details)


@admin_routes.route('/delete_exam/<class_name>/<subject>')
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

    return redirect(url_for('admin_routes.available_exams'))


@admin_routes.route('/logout')
def admin_logout():
    session.pop('username', None)
    return redirect(url_for('admin_routes.admin_login'))
