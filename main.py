from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        credentials = request.get_json()
        username = credentials.get('username')
        password = credentials.get('password')
        
        driver = webdriver.Chrome()
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
        
        driver.quit()

        # Check if the name was successfully retrieved
        if not name or not token:
            return jsonify(error="Could not retrieve name from session storage"), 500
        
        return jsonify({"name": name, "token": token})
    else:
        return jsonify(error="Request must be JSON"), 400

if __name__ == '__main__':
    app.run(debug=True)
