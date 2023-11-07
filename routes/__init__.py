# routes/__init__.py
from flask import Blueprint, render_template, session
import os
import json

current_directory = os.path.dirname(os.path.abspath(__file__))


students_json_path = os.path.join(current_directory, '../student_data/student.json')
teachers_json_path = os.path.join(current_directory, '../teacher_data/teacher.json')
admin_json_path = os.path.join(current_directory, '../admin_data/admin.json')
questions_json_path = os.path.join(current_directory, '../questions/questions.json')

# Declare a dictionary to store teacher-student assignments
teacher_student_assignments = {}

# questions = {}

# Load sample user data (student.json) and question data (questions.json)
with open(students_json_path, 'r') as students_data:
    students = json.load(students_data)

with open(teachers_json_path, 'r') as teachers_data:
    teachers = json.load(teachers_data)

with open(admin_json_path, 'r') as admin_data:
    admin = json.load(admin_data)

with open(questions_json_path, 'r') as questions_file:
    questions = json.load(questions_file)

# Create blueprint instances
student_routes = Blueprint('student_routes', __name__, static_folder="static", template_folder="templates")
teacher_routes = Blueprint('teacher_routes', __name__, static_folder="static", template_folder="templates")
admin_routes = Blueprint('admin_routes', __name__, static_folder="static", template_folder="templates")

# Import and register the routes
from . import student_routes, teacher_routes, admin_routes

