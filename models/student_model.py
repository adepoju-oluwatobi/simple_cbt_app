from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
