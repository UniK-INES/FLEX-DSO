'''
Created on 07.07.2021

@author: Sascha Holzhauer
'''

import dsoTestClient as dso
import os
from flask import (Flask, render_template)
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

import threading

global app
global th
global dsoprogram

app = Flask(__name__, template_folder="../template")
auth = HTTPBasicAuth()

users = {
   secrets_local.webapp_username: generate_password_hash(secrets_local.webapp_password)
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username
    
@app.route('/')
def home():
    return render_template('dso.html')

@app.route('/start')
@auth.login_required  
def apistart():
    global dsoprogram
    global th
    
    flexserver = os.environ.get('FLEX_SERVER')
    if flexserver is None:
        flexserver = secrets_local.flexserver_default
      
    dsoprogram = dso.DsoTestClient(flexserver)
    
    th = threading.Thread(target=dsoprogram.run)
    th.start()
    
    return render_template('started.html')
    
@app.route('/stop')
@auth.login_required
def apistop():
    global dsoprogram
    global th
    
    dsoprogram.setInactive()
    th.join()
    
    return render_template('stopped.html')

if __name__ == '__main__':
    dsoserver = os.environ.get('DSO_SERVER')
    if dsoserver is None:
        dsoserver = "0.0.0.0"
        
    dsoport = os.environ.get('DSO_PORT')
    if dsoport is None:
        dsoport = 5000
    
    print("DSO test client waiting for activation at " + dsoserver + ":" + str(dsoport) + "/start")
    app.run(host=dsoserver, port=dsoport, debug=True)

    