'''
This file is part of INES FLEX - 
INES (Integrated Energy Systems) FLexibility Energy eXchange

INES FLEX is free software: You can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

INES FLEX is distributed in the hope that it will be useful, but 
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

You should have received a copy of the GNU Lesser General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

Copyright (C) 2021
Department of Integrated Energy Systems, University of Kassel,
Kassel, Germany

--
 
This script starts a webserver to start and stop the DSO test-client and 
set variables. Call DSO_SERVER:DSO_PORT to get hints.

This script requires flask and werkzeug.security.

The server address is read from env. var. DSO_SERVER (default is 
gyges.iee.fraunhofer.de/flex) and port from DSO_PORT (default is 5000)

--

Created on 07.07.2021

@author: Sascha Holzhauer
'''

import dsoTestClient as dso
import os
from flask import (Flask, render_template, request)
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

import threading
import sys
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
import secrets_local

global app
global th
global dsoprogram

app = Flask(__name__, template_folder="../template")
auth = HTTPBasicAuth()

users = {
    webapp_username: generate_password_hash(webapp_password)
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username
    
@app.route('/')
def home():
    return render_template('dso.html')

@app.route('/setvar')
@auth.login_required  
def apiparam():
    varname = request.args.get('var', default = 'DSO_PARAM_ID', type = str)
    value = request.args.get('value', default = '0', type = str)
  
    os.environ[varname] = value
    
    return render_template('setparam.html', varname=varname, value=os.environ.get(varname))

@app.route('/start')
@auth.login_required  
def apistart():
    global dsoprogram
    global th
    
    flexserver = os.environ.get('FLEX_SERVER')
    if flexserver is None:
        flexserver = flexserver_default
      
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

    