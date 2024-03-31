import time
import sqlite3
import os
import requests
from dateutil import parser
from datetime import datetime, timedelta, timezone
from main import API_BASE_URL


DATABASE_NAME = 'custom_edt.db'
LAST_UPDATE = "2024-01-01T00:00:00+00:00"

 # TODO: make the table promotion and all func needed

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
                          title TEXT,
                          teacher_code TEXT,
                          classroom_code TEXT,
                          promo_code TEXT
                          )''')
        
                # Create the 'teachers' table
        cursor.execute('''CREATE TABLE teachers (
                          name TEXT,
                          code TEXT PRIMARY KEY,
                          uapvRH TEXT,
                          searchString TEXT
                          )''')

        # Create the 'classrooms' table
        cursor.execute('''CREATE TABLE classrooms (
                          name TEXT,
                          code TEXT PRIMARY KEY,
                          searchString TEXT
                          )''')
        
        # Create the 'academicPrograms' table
        cursor.execute('''CREATE TABLE academicPrograms (
                          name TEXT,
                          code TEXT PRIMARY KEY,
                          searchString TEXT
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

def update_teachers(token):
    url = API_BASE_URL + f"enseignants"
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
    
    results = response.json()["results"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM teachers")
    conn.commit()
    for letter_teachers in results:
        teachers = letter_teachers["names"]
        for teacher in teachers:
            try:
                cursor.execute("INSERT INTO teachers (name, code, uapvRH, searchString) VALUES (?, ?, ?, ?)", 
                               (teacher["name"], teacher["code"], teacher["uapvRH"], teacher["searchString"]))
                conn.commit()
            except sqlite3.IntegrityError as e:
                print(f"Error inserting {teacher['name']}: {e}")
    conn.commit()
    conn.close()

def update_classrooms(token):
    url = API_BASE_URL + f"salles"
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
    
    results = response.json()["results"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM classrooms")

    for letter_classrooms in results:
        classrooms = letter_classrooms["names"]
        for classroom in classrooms:
            try:
                cursor.execute("INSERT INTO classrooms (name, code, searchString) VALUES (?, ?, ?)", 
                               (classroom["name"], classroom["code"], classroom["searchString"]))
            except sqlite3.IntegrityError as e:
                print(f"Error inserting {classroom['name']}: {e}")
    conn.commit()
    conn.close()

def update_academicPrograms(token):
    url = API_BASE_URL + f"elements"
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
    
    results = response.json()["results"]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM academicPrograms")

    for letter_classrooms in results:
        classrooms = letter_classrooms["names"]
        for classroom in classrooms:
            try:
                cursor.execute("INSERT INTO academicPrograms (name, code, searchString) VALUES (?, ?, ?)", 
                               (classroom["name"], classroom["code"], classroom["searchString"]))
            except sqlite3.IntegrityError as e:
                print(f"Error inserting {classroom['name']}: {e}")
    conn.commit()
    conn.close()

def update_data(token):
    global LAST_UPDATE
    
    last_update_datetime = datetime.strptime(LAST_UPDATE, "%Y-%m-%dT%H:%M:%S%z")

    current_datetime_utc = datetime.now(timezone.utc)

    if current_datetime_utc - last_update_datetime > timedelta(weeks=1):
        print("UPDATE DATA")
        update_teachers(token)
        update_classrooms(token)
        update_academicPrograms(token)
        LAST_UPDATE = current_datetime_utc.strftime("%Y-%m-%dT%H:%M:%S%z")

def get_teacher_from_code(teacher_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teachers WHERE uapvRH = ?", (teacher_code,))
    db_events_list = cursor.fetchall()
    conn.close()
    return db_events_list[0]

def get_events_with_teacher_code(teacher_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        SELECT 
            event.code, 
            event.start, 
            event.end, 
            event.type, 
            event.memo, 
            event.title, 
            event.promo_code,
            teachers.name AS teacher_name,
            classrooms.name AS classroom_name,
            academicPrograms.name AS program_name
        FROM 
            event
        JOIN 
            teachers ON event.teacher_code = teachers.uapvRH
        JOIN 
            classrooms ON event.classroom_code = classrooms.code
        JOIN 
            academicPrograms ON event.promo_code = academicPrograms.code  
        WHERE 
            event.teacher_code = ?
    '''
    print(query)
    cursor.execute(query, (teacher_code,))
    results = cursor.fetchall()

    conn.close()

    # Formatting the result
    events_with_teachers_and_classrooms = [
        {'code': row[0], 'start': row[1], 'end': row[2],
         'title': f"Matière : {row[5]}\nEnseignant : {row[7]}\nSalle : {row[8]}\nPromotion : {row[9].upper()}\nType : {row[3]}\nMémo : {row[4]}"} 
        for row in results
    ]

    return events_with_teachers_and_classrooms

def get_events_with_classrooms_code(classrooms_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        SELECT 
            event.code, 
            event.start, 
            event.end, 
            event.type, 
            event.memo, 
            event.title, 
            event.promo_code,
            teachers.name AS teacher_name,
            classrooms.name AS classroom_name,
            academicPrograms.name AS program_name
        FROM 
            event
        JOIN 
            teachers ON event.teacher_code = teachers.uapvRH
        JOIN 
            classrooms ON event.classroom_code = classrooms.code
        JOIN 
            academicPrograms ON event.promo_code = academicPrograms.code  
        WHERE 
            event.classroom_code = ?
    '''

    cursor.execute(query, (classrooms_code,))
    results = cursor.fetchall()
    conn.close()

    # Formatting the result
    events = [
        {'code': row[0], 'start': row[1], 'end': row[2],
         'title': f"Matière : {row[5]}\nEnseignant : {row[7]}\nSalle : {row[8]}\nPromotion : {row[9].upper()}\nType : {row[3]}\nMémo : {row[4]}"} 
        for row in results
    ]

    return events

def get_events_with_promotion_code(promotion_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
        SELECT 
            event.code, 
            event.start, 
            event.end, 
            event.type, 
            event.memo, 
            event.title, 
            event.promo_code,
            teachers.name AS teacher_name,
            classrooms.name AS classroom_name,
            academicPrograms.name AS program_name
        FROM 
            event
        JOIN 
            teachers ON event.teacher_code = teachers.uapvRH
        JOIN 
            classrooms ON event.classroom_code = classrooms.code
        JOIN 
            academicPrograms ON event.promo_code = academicPrograms.code  
        WHERE 
            event.promo_code = ?
    '''

    cursor.execute(query, (promotion_code,))
    results = cursor.fetchall()
    conn.close()

    # Formatting the result
    events = [
        {'code': row[0], 'start': row[1], 'end': row[2],
         'title': f"Matière : {row[5]}\nEnseignant : {row[7]}\nSalle : {row[8]}\nPromotion : {row[9].upper()}\nType : {row[3]}\nMémo : {row[4]}"} 
        for row in results
    ]

    return events