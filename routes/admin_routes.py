import random
from flask import request, redirect, url_for
from . import *  # Import the student_routes blueprint


def is_authenticated():
    return 'username' in session  # Return True if 'username' is in the session


@admin_routes.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        print(f"Received username: {username}, password: {password}")

        # Simplified authentication (replace with your authentication logic)
        if username in admin and admin[username]['password'] == password:
            session['username'] = username

            # Check for a teacher assigned to the student's class
            # student_class = students[username]['class']
            # assigned_teacher = get_teacher_for_class(student_class)

            # if assigned_teacher:
            #     session['assigned_teacher'] = assigned_teacher

            return redirect(url_for('admin_routes.admin_dashboard'))

        return render_template('admin/login.html', error="Invalid credentials", user_authenticated=is_authenticated())

    return render_template('admin/login.html')


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


@admin_routes.route('/logout')
def admin_logout():
    session.pop('username', None)
    return redirect(url_for('admin_routes.admin_login'))
