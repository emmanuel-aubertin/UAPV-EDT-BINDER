from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
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
    else:
        return jsonify(error="Request must be JSON"), 400

if __name__ == '__main__':
    app.run(debug=True)
