# Python’s glob module has several functions that can help in listing files that match a given pattern under a specified folder.
import glob
#interacting with operating system
import os
#subclass of Exception 
import warnings
#use of regular expressions 
import re
#reading pdf in python
import textract
#for making HTTP requests to a specified URL
import requests
#Flask is an API of Python that allows us to build up web-applications.
from flask import (Flask,session, g, json, Blueprint,flash, jsonify, redirect, render_template, request,
                   url_for, send_from_directory)
#for text summarization
from gensim.summarization import summarize
# ml module for knn algorithm 
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
#Pass it a filename and it will return a secure version of it. This filename can then safely be stored on a regular file system
from werkzeug.utils import secure_filename
#The PyMongo library allows interaction with the MongoDB database through Python
import pymongo
#pypdf2 is used to modify and read existing pdfs 
import PyPDF2
# importing files 
import screen
import hashlib

import smtplib
# all these are email module functions for sending emails
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email import encoders
from pyresparser import ResumeParser
# ignoring warnings frpm gensim module
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')

app = Flask(__name__)
#to import flask configurations
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    USERNAME='admin',
    PASSWORD='d8dff0d50788ce8997b1404e4601fc72',
    SECRET_KEY='development key',
))


app.config['UPLOAD_FOLDER'] = 'Original_Resumes/'
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

#to make successfull mongodb server connections
mongo_client = pymongo.MongoClient()

class jd:
    def __init__(self, name):
        self.name = name

def getfilepath(loc):
    temp = str(loc).split('\\')
    return temp[-1]
    



@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == app.config['USERNAME']  and app.config['PASSWORD'] == hashlib.md5(request.form['password'].encode('utf-8')).hexdigest():
            session['username'] = request.form['username']
            flash('You were logged in')
            return redirect(url_for('home'))
        username = request.form['username']
        password = hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()
        db = mongo_client['resumescreening']
        col = db['users']
        x = col.find_one({'username': username})
        if not x:
            error = 'Invalid Username'
        elif x['password'] != password:
            error = 'Invalid Password'
        else:
            session['username'] = request.form['username']
            flash('You were logged in')
            return redirect(url_for('home'))
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if not re.fullmatch(r'[A-Za-z0-9@#$%^&+=]{8,}', request.form['password']):
            error = 'Invalid Password'
        elif request.form['password'] != request.form['confirm']:
            error = 'Passwords doesn\'t match'
        else:
            username = request.form['username']
            password = hashlib.md5(request.form['password'].encode('utf-8')).hexdigest()
            db = mongo_client['resumescreening']
            col = db['users']
            row = {'username': username, 'password': password}
            col.insert_one(row)
            return render_template('login.html')
        return render_template('register.html', error=error)


@app.route('/new')
def new():
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You were logged out')
    return redirect(url_for('home'))


@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    x = []
    for file in glob.glob("./Job_Description/*.txt"):
        res = jd(file)
        x.append(jd(getfilepath(file)))
    print(x)
    if session['username']=="admin":
        return render_template('admin.html', results = x)
    else:
        return render_template('index.html', results = x)



@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
        email = request.form['email']
        job_desc = request.form['des']
        db = mongo_client['resumescreening']
        col = db['resumes']
        row = {'email': email, 'job_desc': job_desc, 'resume': f.filename}
        col.insert_one(row)
        return render_template('upload.html', results = f.filename)


@app.route('/results', methods=['GET', 'POST'])
def res():
    if request.method == 'POST':
        jobfile = request.form['des']
        flask_return = screen.res(jobfile)
        files = []
        sorting_dic = {}
        for i in flask_return:
            files.append(i.filename)
            sorting_dic[i.filename] = i.rank
        db = mongo_client['resumescreening']
        col = db['resumes']
        query = {'resume': {'$in': files}, 'job_desc': jobfile}
        result = col.find(query)
        res = []
        for r in result:
            print(r)
            data = ResumeParser(os.path.join(app.config['UPLOAD_FOLDER'], r['resume'])).get_extracted_data()
            r['data'] = data
            res.append(r)
        print(res)
        res.sort(key=lambda r: sorting_dic[r['resume']])
        return render_template('result.html', results = res)
    return ''

@app.route('/mail', methods=['GET', 'POST'])
def send_mail():
    if request.method == 'POST':
        email = request.form['email']
        sender_email = 'alapativamsi@outlook.com'
        password = 'Nani@501'
        receiver_email = email
        try:
            smtpObj = smtplib.SMTP('smtp-mail.outlook.com', 587)
        except Exception as e:
            print(e)
            smtpObj = smtplib.SMTP_SSL('smtp-mail.outlook.com', 465)
        body = 'Subject: Resume Selected.\n\n You have been selected for the interview round. Please stay tuned for updates.'
        
        smtpObj.ehlo()
        smtpObj.starttls()
        smtpObj.login(sender_email, password) 
        smtpObj.sendmail(sender_email, receiver_email, body)
        smtpObj.quit()
        
        return render_template('mailsent.html')


#when we got resultsearch url we are calling resultsearch method , getting the name from the request
@app.route('/resultscreen' ,  methods = ['POST', 'GET'])
def resultscreen():
    if request.method == 'POST':
        jobfile = request.form.get('Name')
        print(jobfile)
        flask_return = screen.res(jobfile)
        return render_template('result.html', results = flask_return)

@app.route('/search')
def search():
    return "<h1 align=center style=margin-top:10%;>Under Development<h1>"
# no need at this moment 
@app.route('/resultsearch' ,methods = ['POST', 'GET'])
def resultsearch():
    if request.method == 'POST':
        search_st = request.form.get('Name')
        print(search_st)
    result = search.res(search_st)
    # return result
    return render_template('result.html', results = result)

# mapping urls to a specific function 
# to download files from a particular folder 
@app.route('/Original_Resume/<path:filename>')
def custom_static(filename):
    return send_from_directory('./Original_Resumes', filename)



if __name__ == '__main__':
       app.run('0.0.0.0' , 5000 , debug=True , threaded=True)
    
