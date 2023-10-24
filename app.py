import os

from flask import Flask, render_template, session

from routes.admin_routes import admin_routes
from routes.student_routes import student_routes
from routes.teacher_routes import teacher_routes

# Get the current directory of your Python script
current_directory = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = 'username'
print(app.secret_key)

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


if __name__ == '__main__':
    app.run(debug=True)
