# Library used in code
from flask import Flask, render_template, request, redirect, url_for, Response, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func,text
import RPi.GPIO as GPIO
import time
import base64
import cv2



app = Flask(__name__)

# Define GPIO pins
# PIR sensor
PIR = 7

enA = 17
in1 = 27
in2 = 22
enB = 18
in3 = 14
in4 = 15

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(enA, GPIO.OUT)
GPIO.setup(in1, GPIO.OUT)
GPIO.setup(in2, GPIO.OUT)
GPIO.setup(enB, GPIO.OUT)
GPIO.setup(in3, GPIO.OUT)
GPIO.setup(in4, GPIO.OUT)
p1 = GPIO.PWM(enA, 1000)
p2 = GPIO.PWM(enB, 1000)
p1.start(25)
p2.start(25)

# For Database
# configuration of the database 
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///Database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'survey_secret'

db = SQLAlchemy(app)

class Survey1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(225))
    There_Department = db.Column(db.String(50))
    There_TDepartment = db.Column(db.String(50))
    rating = db.Column(db.Integer)
    suggestion = db.Column(db.Text)
    srating = db.Column(db.Integer)
    
class Slider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)

class Aboutimage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)

class Coursesimage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)

class Administration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    image = db.Column(db.LargeBinary, nullable=False)


# For Camera Settings
camera = cv2.VideoCapture(0)
def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Route Index Login page
@app.route('/')
def index():
    return render_template('Login.html')

# Route Login Settings 
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username == 'Sebasty' and password == '12345':
        return redirect(url_for('admin'))
    else:
        return render_template('Login.html', message='Invalid username or password. Please try again.')

@app.route("/control", methods=["POST"])
def control():
    direction = request.form["direction"]
    if direction == "forward":
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)
    elif direction == "backward":
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
    elif direction == "right":
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.HIGH)
        GPIO.output(in3, GPIO.HIGH)
        GPIO.output(in4, GPIO.LOW)
    elif direction == "left":
        GPIO.output(in1, GPIO.HIGH)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.HIGH)
    elif direction == "stop":
        GPIO.output(in1, GPIO.LOW)
        GPIO.output(in2, GPIO.LOW)
        GPIO.output(in3, GPIO.LOW)
        GPIO.output(in4, GPIO.LOW)
    return redirect(url_for('admin'))

@app.route("/speed", methods=["POST"])
def speed():
    speed = int(request.form["speed"])
    p1.ChangeDutyCycle(speed)
    p2.ChangeDutyCycle(speed)
    return redirect(url_for('admin'))


# Admin interface
@app.route('/admin')
def admin():
    query = text("""
        SELECT 
            There_TDepartment AS Target_Department,
            COUNT(*) AS total_voter,
            COUNT(*) * 5 AS expected_total_stars,
            SUM(rating) AS total_earned_stars
        FROM 
            Survey1
        GROUP BY 
            There_TDepartment;
        """)

    conn = db.engine.connect()
    results = conn.execute(query)
    average_ratings = results.fetchall()

    query_overall_srating = text("""
        SELECT 
            AVG(srating) AS overall_average_rating,
            COUNT(*) AS    Stotal_voter,
            COUNT(*) * 5 AS Sexpected_total_stars,
            SUM(srating) AS Stotal_earned_stars
        FROM Survey1
        """)

    # Execute the query for overall school rating
    results_overall_srating = conn.execute(query_overall_srating)
    overall_srating = results_overall_srating.fetchall()

    surveys = Survey1.query.all()
    conn.close()

    return render_template('Admin.html', surveys=surveys, average_ratings=average_ratings, overall_srating=overall_srating)
  
  
# Admin Form-Post
# Update form Slider
@app.route('/upload_slider', methods=['GET','POST'])
def upload_slider():
    if request.method == 'POST':
        slider_name = request.form['Slide_name']
        slider_image = request.files['image'].read()
        existing_slider = Slider.query.filter_by(name=slider_name).first()
        if existing_slider:
            existing_slider.image = slider_image
            db.session.commit()
            flash('Slider image updated successfully', 'success')
        else:
            new_slider = Slider(name=slider_name, image=slider_image)
            db.session.add(new_slider)
            db.session.commit()
            flash('New slider uploaded successfully', 'success')
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))

# Update form About
@app.route('/upload_About', methods=['GET','POST'])
def upload_About():
    if request.method == 'POST':
        About_name = request.form['About_name']
        About_image = request.files['About_image'].read()
        existing_About = Aboutimage.query.filter_by(name=About_name).first()
        if existing_About:
            existing_About.image = About_image
            db.session.commit()
            flash('About image updated successfully', 'success')
        else:
            new_slider = Aboutimage(name=About_name, image=About_image)
            db.session.add(new_slider)
            db.session.commit()
            flash('New About uploaded successfully', 'success')
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))

# Update form Courses
@app.route('/upload_Course', methods=['GET','POST'])
def upload_Course():
    if request.method == 'POST':
        Course_name = request.form['Course_name']
        Course_image = request.files['Course_image'].read()
        existing_Course = Coursesimage.query.filter_by(name=Course_name).first()
        if existing_Course:
            existing_Course.image = Course_image
            db.session.commit()
            flash('Course image updated successfully', 'success')
        else:
            new_Course = Coursesimage(name=Course_name, image=Course_image)
            db.session.add(new_Course)
            db.session.commit()
            flash('New Course uploaded successfully', 'success')
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))

# Update form Administration
@app.route('/upload_Administration', methods=['GET','POST'])
def upload_Administration():
    if request.method == 'POST':
        Administration_name = request.form['Administration_name']
        Administration_image = request.files['Course_image'].read()
        existing_Administration = Administration.query.filter_by(name=Administration_name).first()
        if existing_Administration:
            existing_Administration.image = Administration_image
            db.session.commit()
            flash('Administration image updated successfully', 'success')
        else:
            new_Administration = Administration(name=Administration_name, image=Administration_image)
            db.session.add(new_Administration)
            db.session.commit()
            flash('New Administration uploaded successfully', 'success')
        return redirect(url_for('admin'))
    return redirect(url_for('admin'))
  
# Button Funtions
# Delete button for the individual survey
@app.route('/delete/<int:id>')
def delete(id):
    survey = Survey1.query.get_or_404(id)
    db.session.delete(survey)
    db.session.commit()
    return redirect(url_for('admin'))

# Delete all Data at table Survey1
@app.route('/delete_all', methods=['POST'])
def delete_all():
    Survey1.query.delete()
    db.session.commit()
    return redirect(url_for('admin'))

# Logout Settings
@app.route('/logout')
def logout():
    return redirect(url_for('index'))
  
  
@app.route("/forward")
def forward():
    set_motor("forward")
    return "Moving forward"

@app.route("/backward")
def backward():
    set_motor("backward")
    return "Moving backward"

@app.route("/stop")
def stop():
    set_motor("stop")
    return "Motor stopped"

@app.route("/right")
def right():
    set_motor("right")
    return "Turning right"

@app.route("/left")
def left():
    set_motor("left")
    return "Turning left"

  
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
