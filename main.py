import os
from datetime import datetime, timedelta
from time import strftime, gmtime
from pytz import utc
from flask import Flask, render_template, request, redirect, url_for, session, send_file, send_from_directory
import pyrebase
import firebase_admin
from firebase_admin import auth as auth_from_admin
from firebase_admin import credentials, firestore, storage
from apscheduler.schedulers.background import BackgroundScheduler

config = {
    "apiKey": "AIzaSyATkBZEF9GzYJLjlpL1qfePf55uWQIvC-8",
    "authDomain": "hostelmessmanagent.firebaseapp.com",
    "databaseURL": "https://hostelmessmanagent-default-rtdb.firebaseio.com/",
    "storageBucket": "hostelmessmanagent.appspot.com"
}

cred = credentials.Certificate("hostelmessmanagent-firebase-adminsdk-v14sr-d7a6bfecdb.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

# db = firebase.database()

app = firebase_admin.initialize_app(cred, {
    'storageBucket': 'hostelmessmanagement.appspot.com',  # Replace with your bucket name
}, name='storage')

bucket = storage.bucket(app=app)

doc_ref_recipes = db.collection("mealsfortom").document("wVjEr23OuiRIJMMTw1ZD")
doc_ref_headcount = db.collection("headcount").document("ZHp354UuSReeWvZ1mD15")

char_val_map = {
    "1": 10,
    "2": 20,
    "3": 30,
    "4": 40,
    "5": 50,
    "6": 60,
    "7": 70,
    "8": 80,
    "9": 90,
    "a": 100,
    "b": 110,
    "c": 120,
    "d": 130,
    "e": 140,
    "f": 150,
    "g": 160,
    "h": 170,
    "i": 180,
    "j": 190,
    "k": 200
}
month_val_map = {
    "01": 0,
    "02": 1,
    "03": 2,
    "04": 3,
    "05": 4,
    "06": 5,
    "07": 6,
    "08": 7,
    "09": 8,
    "10": 9,
    "11": 10,
    "12": 11
}

app = Flask(__name__)
scheduler = BackgroundScheduler()


def sign_in(email, password):
    user_record = auth.sign_in_with_email_and_password(email, password)
    return user_record


def sign_up(email, password, display_name):
    try:
        user_record = auth.create_user(email=email, password=password, display_name=display_name)
        return user_record
    except auth.AuthError as error:
        return None


def sign_out():
    del session['user_id']
    return True


def manipulate_booleans(doc_ref, update_data):
    doc_ref.update(update_data)


def scheduled_task_daily():
    attendance_collection_ref = db.collection("attendance")
    attendance_docs = attendance_collection_ref.stream()

    for doc in attendance_docs:
        data = doc.to_dict()

        new_data = {
            "breakfast": False,
            "lunch": False,
            "Snacks": False,
            "Dinner": False,
        }
        manipulate_booleans(doc.reference, new_data)

    choice_collection_ref = db.collection("choice")
    choice_docs = choice_collection_ref.stream()

    for doc in choice_docs:
        data = doc.to_dict()

        new_data = {
            "breakfast": True,
            "lunch": True,
            "snacks": True,
            "dinner": True,
        }
        manipulate_booleans(doc.reference, new_data)


def scheduled_task_monthly():
    fee_dailies_ref = db.collection("fees").document("daily")
    fee_monthly_ref = db.collection("fees").document("monthly")

    fee_dailies_collection, fee_monthly_collection = fee_dailies_ref.get(), fee_monthly_ref.get()
    fee_dailies_collection, fee_monthly_collection = fee_dailies_collection.to_dict(), fee_monthly_collection.to_dict()

    current_month = datetime.now().strftime("%m")
    to_monthly = {}
    to_daily = {}
    for keys in fee_dailies_collection:
        value = fee_dailies_collection[keys]
        valued = 0
        for value in value[:]:
            if value in char_val_map:
                valued += char_val_map[value]

        to_monthly[keys] = valued

    if current_month in month_val_map:
        current_month = month_val_map[current_month]
    for keys in fee_monthly_collection:
        value = fee_monthly_collection[keys]
        value[current_month] = to_monthly[keys]

    fee_monthly_ref.set(fee_monthly_collection, merge=True)

    for keys in fee_dailies_collection:
        fee_dailies_collection[keys] = "0000000000000000000000000000000"
    fee_dailies_ref.set(fee_dailies_collection, merge=True)
    # print(fee_monthly_collection)


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


@app.route('/sign-up', methods=['POST'])
def sign_up_route():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        display_name = request.form.get('display_name')
        if not email or not password or not display_name:
            return 'Email, password, and display name are required.'
        user_record = sign_up(email, password, display_name)
        if user_record:
            session['user_id'] = user_record['localId']
            return redirect(url_for('protected-route'))
        else:
            return 'Sign-up failed'
    else:
        return render_template('sign_up.html')


@app.route('/sign-out')
def sign_out_route():
    if sign_out():
        session.pop('user_id', None)
        return redirect(url_for('index'))
    else:
        return 'Sign-out failed'


@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    document101 = doc_ref_headcount.get()
    if document101.exists:
        data101 = document101.to_dict()
        headcount = {"breakfast": data101.get("breakfast", None), "lunch": data101.get("lunch", None),
                     "snacks": data101.get("snacks", None), "dinner": data101.get("dinner", None)}
        if request.method == 'GET':
            document = doc_ref_recipes.get()
            if document.exists:
                data = document.to_dict()
            else:
                print("Document does not exist")
                breakfast, lunch, snacks, dinner = "None"
            recipes = {"breakfast": data.get("breakfast", None), "lunch": data.get("lunch", None),
                       "snacks": data.get("snacks", None), "dinner": data.get("dinner", None)}
            return render_template("dashboard.html", recipes=recipes, headcount=headcount)
        elif request.method == "POST":
            recipes = {'breakfast': request.form.get("recipe-breakfast"), 'lunch': request.form.get("recipe-lunch"),
                       'snacks': request.form.get("recipe-snacks"), 'dinner': request.form.get("recipe-dinner")}
            print(recipes)
            doc_ref_recipes.set(recipes, merge=True)
            print(recipes)
            return render_template("dashboard.html", recipes=recipes, headcount=headcount)


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


# @app.route("/users", methods=["GET", "POST"])
# def users():
#     page = auth_from_admin.list_users()
#     users_email_list = []
#     count = 0
#     for user in page.users:
#         count += 1
#         users_email_list.append(user.email)
#     print(users_email_list)
#     users_email_dict = {"email": users_email_list[:], "count": count}
#     return render_template("users.html", users_email_dict=users_email_dict)
#
#
# @app.route("/styles/users.css", methods=["GET"])
# def users_css():
#     return send_file("web/styles/users.css")


if __name__ == '__main__':
    app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'The_most_scret_key_ever_made_in_the_namkind')
    scheduler.add_job(func=scheduled_task_daily, trigger="cron", hour=0, minute=0, second=5)
    scheduler.add_job(func=scheduled_task_monthly, trigger="cron", day=1, hour=0, minute=1, second=0)
    scheduler.start()
    app.run(debug=True)
