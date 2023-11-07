import os
import json
from flask import Flask, render_template, session, current_app
from flask_sqlalchemy import SQLAlchemy
from routes.admin_routes import admin_routes
from routes.student_routes import student_routes
from routes.teacher_routes import teacher_routes
import schedule  # Import the schedule library
import time

# Get the current directory of your Python script
current_directory = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'username'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:3000/CBT-app'
db = SQLAlchemy(app)

app.register_blueprint(student_routes, url_prefix="/student")
app.register_blueprint(teacher_routes, url_prefix="/teacher")
app.register_blueprint(admin_routes, url_prefix="/admin")


# route for the landing page
@app.route('/')
def homepage():
    return render_template('landingPage.html', user_authenticated=is_authenticated())


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


# Load student data from the JSON file
def load_student_data():
    with open('student_data/student.json', 'r') as student_file:
        student_data = json.load(student_file)
    return student_data


# Function to save student data to the database
# Create a function to update the database from the JSON file
def update_database_from_json():
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


# Schedule the update_database_from_json function to run every hour
schedule.every(1).minutes.do(update_database_from_json)


# Function to start the scheduled job
def run_scheduled_job():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    update_database_from_json()

    # Start the scheduled job in the background
    import threading

    threading.Thread(target=run_scheduled_job, daemon=True).start()
    app.run(debug=True)
