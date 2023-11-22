import json
import os
import time
import schedule
from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from routes.admin_routes import admin_routes
from routes.student_routes import student_routes
from routes.teacher_routes import teacher_routes

# Get the current directory of your Python script
current_directory = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'username'
# Add the configuration for the upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:3000/CBT-app'
db = SQLAlchemy(app)


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5173'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

app.register_blueprint(student_routes, url_prefix="/student")
app.register_blueprint(teacher_routes, url_prefix="/teacher")
app.register_blueprint(admin_routes, url_prefix="/admin")


# route for the landing page
@app.route('/')
def homepage():
    return render_template('homepage.html', user_authenticated=is_authenticated())


# handles user authentication
def is_authenticated():
    return 'username' in session  # Return True if 'username' is in the session


# Define a model for student data
class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    name = db.Column(db.String(100))
    parent_name = db.Column(db.String(100))
    password = db.Column(db.String(100))
    class_name = db.Column(db.String(100))
    score = db.Column(db.Integer)
    scores = db.Column(db.JSON)
    progress = db.Column(db.JSON)


# Define a model for teacher data
class Teacher(db.Model):
    __tablename__ = 'teacher'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    subject = db.Column(db.String(100))
    class_name = db.Column(db.String(100))


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))


class Questions(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.String(100), unique=True, nullable=False)
    data = db.Column(db.JSON)


# Load student data from the JSON file
def load_student_data():
    with open('student_data/student.json', 'r') as student_file:
        student_data = json.load(student_file)
    return student_data


def load_teacher_data():
    with open('teacher_data/teacher.json', 'r') as teacher_file:
        teacher_data = json.load(teacher_file)
    return teacher_data


def load_admin_data():
    with open('admin_data/admin.json', 'r') as admin_file:
        admin_data = json.load(admin_file)
        # print(admin_data)
    return admin_data


def load_question_data():
    with open('questions/questions.json', 'r') as questions:
        question_data = json.load(questions)
    return question_data


# Function to save student data to the database
# Create a function to update the database from the JSON file
def update_student_database_from_json():
    student_data = load_student_data()
    with app.app_context():
        # Clear the 'student' table before updating
        Student.query.delete()

        # Add data from the JSON file to the database
        for username, data in student_data.items():
            student = Student(
                username=username,  # You should use a unique identifier as the username
                name=data.get('name'),
                parent_name=data.get('parent_name'),
                password=data.get('password'),
                class_name=data.get('class'),
                score=data.get('score'),
                scores=data.get('scores'),
                progress=data.get('progress')
            )
            db.session.add(student)
        db.session.commit()


def update_teacher_database_from_json():
    teacher_data = load_teacher_data()
    with app.app_context():
        # Clear the 'teacher' table before updating
        Teacher.query.delete()

        # Add data from the JSON file to the database
        for username, data in teacher_data.items():
            teacher = Teacher(
                username=username,
                email=data.get('email'),
                password=data.get('password'),
                subject=data.get('subject'),
                class_name=data.get('class')
            )

            db.session.add(teacher)

        db.session.commit()


def update_question_database_from_json():
    question_data = load_question_data()
    with app.app_context():
        db.create_all()
        Questions.query.delete()

        for year, data in question_data.items():
            questions = Questions(
                year=year,
                data=data
            )

            db.session.add(questions)

        db.session.commit()


def update_admin_database_from_json():
    admin_data = load_admin_data()
    with app.app_context():
        db.create_all()
        Admin.query.delete()

        # Add data from the JSON file to the database
        for username, data in admin_data.items():
            admin = Admin(
                username=username,
                email=data.get('email'),
                password=data.get('password')
            )

            db.session.add(admin)

        db.session.commit()


# Schedule the update_database_from_json function to run every hour
schedule.every(1).seconds.do(update_student_database_from_json)
schedule.every(1).seconds.do(update_teacher_database_from_json)
schedule.every(1).seconds.do(update_question_database_from_json)
schedule.every(1).seconds.do(update_admin_database_from_json)


# Function to start the scheduled data upload
def run_scheduled_job():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    update_teacher_database_from_json()
    update_student_database_from_json()
    update_question_database_from_json()
    update_admin_database_from_json()

    # Start the scheduled job in the background
    import threading

    threading.Thread(target=run_scheduled_job, daemon=True).start()
    app.run(debug=True)
