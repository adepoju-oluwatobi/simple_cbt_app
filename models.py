from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:3000/students'  # Replace with your PostgreSQL database URL
db = SQLAlchemy(app)


# Define a model for student data
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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
def save_students_to_database():
    student_data = load_student_data()

    for username, data in student_data.items():
        student = Student(
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


if __name__ == '__main__':
    # Initialize the database
    db.create_all()
    save_students_to_database()
