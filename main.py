import os

from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pyrebase
import firebase_admin
from firebase_admin import credentials, firestore, storage
from apscheduler.schedulers.background import BackgroundScheduler
import inventory.scheduled_tasks
import inventory.credentials

firebase_admin.initialize_app(credentials.Certificate(inventory.credentials.creds_for_firebase()))
firebase = pyrebase.initialize_app(inventory.credentials.creds_for_pyrebase())
auth = firebase.auth()

app = firebase_admin.initialize_app(credentials.Certificate(inventory.credentials.creds_for_firebase()), {
    'storageBucket': 'hostelmessmanagement.appspot.com',
}, name='storage')
bucket = storage.bucket(app=app)

db = firestore.client()
doc_ref_recipes = db.collection("mealsfortom").document("wVjEr23OuiRIJMMTw1ZD") 
doc_ref_count_choice = db.collection("count").document("3XAuDDcCBxPjeLnoJDZ5")
doc_ref_count_attended = db.collection("count").document("ocqraJyO161eUcBnEDTa")
doc_ref_count_total = db.collection("count").document("AmMJEJd4Dx7n9zEwOFiQ")

app = Flask(__name__)
scheduler = BackgroundScheduler()


def sign_in(email, password):
    user_record = auth.sign_in_with_email_and_password(email, password)
    return user_record


def sign_out():
    del session['user_id']
    return True


@app.before_request
def authenticate():
    if 'user_id' not in session and request.endpoint in ['dashboard']:
        return redirect(url_for('sign_in_route'))


@app.route('/sign-in', methods=['POST', 'GET'])
def sign_in_route():
    if 'user_id' in session:
        return redirect(url_for("dashboard"))
    else:
        if request.method == 'POST':
            try:
                email = request.form.get('email')
                password = request.form.get('password')
                if not email or not password:
                    return 'Email and password are required.'
                user_record = sign_in(email, password)
                if user_record and email == "meals.admn@gmail.com":
                    session['user_id'] = user_record['localId']
                    return redirect(url_for('dashboard'))
                else:
                    return render_template('sign_in.html')
            except:
                return render_template('sign_in.html')
        else:
            return render_template('sign_in.html')


@app.route("/styles/sign_in.css", methods=["GET"])
def sign_in_css():
    return send_file("web/styles/sign_in.css")


@app.route('/sign-out')
def sign_out_route():
    if sign_out():
        session.pop('user_id', None)
        return redirect(url_for('index'))
    else:
        return 'Sign-out failed'


@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    document_choice = doc_ref_count_choice.get()
    document_attended = doc_ref_count_attended.get()
    document_total = doc_ref_count_total.get()
    if document_choice.exists and document_attended.exists and document_total.exists:
        choices_from_app = document_choice.to_dict()
        totals_from_auth = document_total.to_dict()
        attendance_from_mess = document_attended.to_dict()
        
        choices = {"breakfast": choices_from_app.get("breakfast", None), "lunch": choices_from_app.get("lunch", None),
                     "snacks": choices_from_app.get("snacks", None), "dinner": choices_from_app.get("dinner", None)}
        
        totals = {"total": totals_from_auth.get("headcount", None)}
        
        attendance = {"breakfast": attendance_from_mess.get("breakfast", None), "lunch": attendance_from_mess.get("lunch", None),
                     "snacks": attendance_from_mess.get("snacks", None), "dinner": attendance_from_mess.get("dinner", None)}
        
        if request.method == 'GET':
            document = doc_ref_recipes.get()
            if document.exists:
                data = document.to_dict()
            else:
                print("Document does not exist")
            recipes = {"breakfast": data.get("breakfast", None), "lunch": data.get("lunch", None),
                       "snacks": data.get("snacks", None), "dinner": data.get("dinner", None)}
            return render_template("dashboard.html", recipes=recipes, choices=choices, totals=totals, attendance=attendance)
        elif request.method == "POST":
            recipes = {'breakfast': request.form.get("recipe-breakfast"), 'lunch': request.form.get("recipe-lunch"),
                       'snacks': request.form.get("recipe-snacks"), 'dinner': request.form.get("recipe-dinner")}
            print(recipes)
            doc_ref_recipes.set(recipes, merge=True)    
            print(recipes)
            return render_template("dashboard.html", recipes=recipes, choices=choices, totals=totals, attendance=attendance)


@app.route('/styles/dashboard.css', methods=["GET", "POST"])
def dashboard_css():
    return send_file("web/styles/dashboard.css")


@app.route('/scripts/dashboard.js', methods=["GET", "POST"])
def dashboard_js():
    return send_file("web/scripts/dashboard.js")


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/styles/index.css')
def index_css():
    return send_file("web/styles/index.css")


@app.route('/meals.png', methods=["GET"])
def meals_png_dash():
    return send_file("web/assets/meals.png")


@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")


@app.route("/styles/about.css", methods=["GET"])
def about_css():
    return send_file("web/styles/about.css")


if __name__ == '__main__':
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'The_most_scret_key_ever_made_in_the_namkind')
    scheduler.add_job(func=inventory.scheduled_tasks.scheduled_task_meal_analytics, args=["breakfast", db],
                      trigger="cron", hour="0-9", minute="15-45", jitter=120)
    scheduler.add_job(func=inventory.scheduled_tasks.scheduled_task_meal_analytics, args=["lunch", db], trigger="cron",
                      hour="3-12", minute="15-45", jitter=121)
    scheduler.add_job(func=inventory.scheduled_tasks.scheduled_task_meal_analytics, args=["snacks", db], trigger="cron",
                      hour="6-16", minute="15-45", jitter=122)
    scheduler.add_job(func=inventory.scheduled_tasks.scheduled_task_meal_analytics, args=["dinner", db], trigger="cron",
                      hour="12-20", minute="15-45", jitter=123)
    scheduler.add_job(func=inventory.scheduled_tasks.scheduled_task_daily, args=(db,), trigger="cron", hour=0, minute=0,
                      second=5)
    scheduler.add_job(func=inventory.scheduled_tasks.scheduled_task_monthly, args=(db,), trigger="cron", day=1, hour=0,
                      minute=1, second=0)
    scheduler.start()
    app.run(debug=True)
