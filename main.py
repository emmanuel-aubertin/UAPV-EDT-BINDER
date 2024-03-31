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
from datetime import datetime, timedelta, timezone
import db

app = Flask(__name__)
API_BASE_URL = "https://edt-api.univ-avignon.fr/api/"

#https://edt-api.univ-avignon.fr/api/enseignants
def is_promo_avaible(token, start, end, promo_code):
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT start, end FROM event WHERE promo_code = ?", (promo_code,))
    events = cursor.fetchall()
    conn.close()
    
    if events and not is_avaible(events, start, end):
        return False
    
    url = API_BASE_URL + f"events_promotion/{promo_code}"
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

def is_classroom_avaible(token, start, end, classroom_code):
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT start, end FROM event WHERE classroom_code = ?", (classroom_code,))
    events = cursor.fetchall()
    conn.close()
    
    if events and not is_avaible(events, start, end):
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
    
    return is_avaible(data, start, end)

def get_teacher_api_events(token, teacher_code):
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
    return response.json()["results"]

def get_classroom_api_events(token, classroom_code):
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
    return response.json()["results"]

def get_promotion_api_events(token, promo_code):
    url = API_BASE_URL + f"events_promotion/{promo_code}"
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
    return response.json()["results"]

def is_teacher_avaible(token, start, end, teacher_code):
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT start, end FROM event WHERE teacher_code = ?", (teacher_code,))
    events = cursor.fetchall()
    conn.close()
    if events and not is_avaible(events, start, end):
        return False
    return is_avaible(get_teacher_api_events(token, teacher_code), start, end)

def is_avaible(events, start, end):
    if not events:
        return False
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
    db.update_data(token);
    if not name or not token:
        return jsonify(error="Could not retrieve name from session storage"), 500

    return jsonify({"name": name, "token": token, "is_student": is_student})
        
@app.route('/event/create', methods=['POST'])
def create_event():
    if not request.is_json:
        return jsonify(error="Request must be JSON"), 400
    
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        return jsonify({"error": "Authorization token is missing or invalid"}), 401
    
    input_data = request.get_json()
    start = input_data.get('start')
    end = input_data.get('end')
    teacher_code = input_data.get('teacher_code')  
    print(teacher_code)
    print(is_teacher_avaible(token, start, end, teacher_code))
    if teacher_code != "" and not is_teacher_avaible(token, start, end, teacher_code):
        return jsonify({"error": "Teacher not avaible"})

    classroom_code = input_data.get('classroom_code')
    if classroom_code != "" and not is_classroom_avaible(token, start, end, classroom_code):
        return jsonify({"error": "Classroom not avaible"})
    
    promo_code = input_data.get('promo_code') 
    if promo_code != "" and not is_promo_avaible(token, start, end, promo_code):
        return jsonify({"error": "Classroom not avaible"})
    
    type = input_data.get('type')
    memo = input_data.get('memo')
    title = f"{input_data.get('title')}"
    event_code = os.urandom(4).hex()

    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''INSERT INTO event (code, start, end, type, memo, title, teacher_code, classroom_code, promo_code)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (event_code, start, end, type, memo, title, teacher_code, classroom_code, promo_code))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": f"Failed to insert event into database: {e}"}), 500

    conn.close()
    return jsonify({"message": "Event created successfully", "event_code": event_code}), 201

@app.route('/event/get/teacher/<teacher_code>', methods=['GET'])
def get_events_by_teacher(teacher_code):
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        return jsonify({"error": "Authorization token is missing or invalid"}), 401
    
    db.update_data(token)
    db_events = db.get_events_with_teacher_code(teacher_code)
    return jsonify({"results":  get_teacher_api_events(token, teacher_code) + db_events})

@app.route('/event/get/classroom/<classrooms_code>', methods=['GET'])
def get_events_by_classroom(classrooms_code):
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        return jsonify({"error": "Authorization token is missing or invalid"}), 401
    
    db.update_data(token)
    db_events = db.get_events_with_classrooms_code(classrooms_code)
    return jsonify({"results":  get_classroom_api_events(token, classrooms_code) + db_events})


@app.route('/event/get/promotion/<promo_code>', methods=['GET'])
def get_events_by_promotion(promo_code):
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        return jsonify({"error": "Authorization token is missing or invalid"}), 401
    
    db.update_data(token)
    db_events = db.get_events_with_promotion_code(promo_code)
    return jsonify({"results":  get_promotion_api_events(token, promo_code) + db_events})

if __name__ == '__main__':
    db.init_db()
    app.run(debug=True)
