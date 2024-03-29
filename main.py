from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import sqlite3
import os
import requests
from dateutil import parser

app = Flask(__name__)
DATABASE_NAME = 'custom_edt.db'
API_BASE_URL = "https://edt-api.univ-avignon.fr/api/"

def init_db():
    """Create the database and tables if they don't already exist."""
    if not os.path.exists(DATABASE_NAME):
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        # Create the 'event' table
        cursor.execute('''CREATE TABLE event (
                          code TEXT PRIMARY KEY,
                          start TEXT,
                          end TEXT,
                          type TEXT,
                          memo TEXT,
                          teacher_code TEXT,
                          classroom_code TEXT
                          )''')
        conn.commit()
        conn.close()
        print("Database and table created.")
    else:
        print("Database already exists.")
        
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def is_classroom_avaible(token, start, end, classroom_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT start, end FROM event WHERE classroom_code = ?", (classroom_code,))
    events = cursor.fetchall()
    conn.close()
    
    if not is_avaible(events, start, end):
        return False
    
    url = API_BASE_URL + f"events_salle/{classroom_code}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://edt.univ-avignon.fr/",
        "token": token,
        "Origin": "https://edt.univ-avignon.fr",
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return False
    
    data = response.json()["results"]
    print("Checking web info")
    return is_avaible(data, start, end)
    return True

def is_teacher_avaible(token, start, end, teacher_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT start, end FROM event WHERE teacher_code = ?", (teacher_code,))
    events = cursor.fetchall()
    conn.close()
    
    if not is_avaible(events, start, end):
        return False
    
    url = API_BASE_URL + f"events_enseignant/{teacher_code}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://edt.univ-avignon.fr/",
        "token": token,
        "Origin": "https://edt.univ-avignon.fr",
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return False
    
    data = response.json()["results"]
    return is_avaible(data, start, end)

def is_avaible(events, start, end):
    if(len(events) == 0):
        return True
    for event in events:
        if(is_overlapping(event, start, end)):
            return False
    return True

def is_overlapping(event, start, end):
    return parser.parse(start) < parser.parse(event["end"]) and parser.parse(end) > parser.parse(event["start"])

@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify(error="Request must be JSON"), 400
    
    credentials = request.get_json()
    username = credentials.get('username')
    password = credentials.get('password')
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

    # Instantiate a webdriver with the options
    driver = webdriver.Chrome(options=chrome_options)
    
    driver.get("https://cas.univ-avignon.fr/cas/login?service=https%3A%2F%2Fedt.univ-avignon.fr%2Flogin")
    
    driver.find_element(by=By.ID, value="username").send_keys(username)
    input_password = driver.find_element(by=By.ID, value="password")
    input_password.send_keys(password)
    input_password.send_keys(Keys.RETURN)
    
    if(driver.title != "Edt"):
        driver.quit()
        return jsonify(error="Invalid username or password"), 401
    time.sleep(3)
    name = driver.execute_script("return window.sessionStorage.getItem('name');")
    token = driver.execute_script("return window.sessionStorage.getItem('token');")

    uid = driver.execute_script("return window.sessionStorage.getItem('uid');")
    """ Taken from edt main.js
    isStudent()
    {
        var e = window.sessionStorage.getItem("uid");
        return !(e && "uapv" != e.substring(0, 4) || null == e)
    }
    """
    is_student = not (uid == None or not uid.startswith("uapv"))
    driver.quit()

    # Check if the name was successfully retrieved
    if not name or not token:
        return jsonify(error="Could not retrieve name from session storage"), 500
    
    return jsonify({"name": name, "token": token, "is_student": is_student})
        

@app.route('/event/create', methods=['POST'])
def create_event():
    if not request.is_json:
        return jsonify(error="Request must be JSON"), 400
    
    input_data = request.get_json()
    token = input_data.get('token')
    start = input_data.get('start')
    end = input_data.get('end')
    teacher_code = input_data.get('teache_code')
    
    if teacher_code != "" and not is_teacher_avaible(token, start, end, teacher_code):
        return jsonify({"error": "Teacher not avaible"})

    classroom_code = input_data.get('classroom_code')
    type = input_data.get('type')
    memo = input_data.get('memo')
    
    if classroom_code != "" and not is_classroom_avaible(token, start, end, classroom_code):
        return jsonify({"error": "Classroom not avaible"})
    
    event_code = os.urandom(4).hex()

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''INSERT INTO event (code, start, end, type, memo, teacher_code, classroom_code)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''',
                       (event_code, start, end, type, memo, teacher_code, classroom_code))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": f"Failed to insert event into database: {e}"}), 500

    conn.close()
    return jsonify({"message": "Event created successfully", "event_code": event_code}), 201
    
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
