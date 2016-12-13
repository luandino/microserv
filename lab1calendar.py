#!/usr/bin/env python
import flask
import urllib
import requests
import datetime
import dateutil.parser
import random
import string
import json
import os
from flask import Flask, url_for, render_template, redirect, send_from_directory, session as login_session

### NEEDED TO USE BOOTSTRAP'S TEMPLATES  ###

from flask_bootstrap import Bootstrap

def create_app():
  app = Flask(__name__)
  Bootstrap(app)
  return app

app = Flask(__name__)

### USER'S PUBLIC AND SECRET KEYS FROM REGISTRED APP ###
CLIENT_ID = '175927083112-mvpg2vtgem5t68fdu7vp60bggsurfmdt.apps.googleusercontent.com'
CLIENT_SECRET = '9zjYjm2o7G_6OHw6aB2msnkn'


REDIRECT_URI = 'http://localhost:5000/callback'
URL_GOOGLE_PLUS_USER = "https://www.googleapis.com/oauth2/v1/userinfo"

### AS I RECEIVED A WARNING OF LACK OF FAVICON, I CREATE ONE AND PUT IN THE PATH ###

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')


def auth_url():
    url = "https://accounts.google.com/o/oauth2/auth"
    scope_user = "https://www.googleapis.com/auth/userinfo.profile"
    scope_cal = "https://www.googleapis.com/auth/calendar.readonly"
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': '{0} {1}'.format(scope_cal, scope_user),
        'access_type': 'offline',
        'approval_prompt': 'force'
    }
    return "{0}?{1}".format(url, urllib.urlencode(params))


### BUILD THE TOKEN WITH RECEIVED CODE IN CALLBACK ###
def create_token(code):
    url = "https://accounts.google.com/o/oauth2/token"
    params = {
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    r = requests.post(url, data=params)
    results = json.loads(r.text)
    access_token = results['access_token']
    refresh_token = results['refresh_token']
    return (access_token , refresh_token)

############# NAME, PICTURE #################
def get_profile(access_token):
    url = URL_GOOGLE_PLUS_USER
    params = {'access_token': access_token}
    r = requests.get(url, params=params)
    return json.loads(r.text)

########### GET EMAIL FROM CALENDARS, BECAUSE NOT IN GOOGLE+ #############
def get_email(access_token):
    url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
    params = {'access_token': access_token}
    r = requests.get(url, params=params)
    result = json.loads(r.text)
    email_adress = result['items'][0]['id']
    return email_adress

########## ASK GOOGLE'S CALENDAR FOR TASKS
def get_todays_events(access_token, cal_id, date = None):
    url = "https://www.googleapis.com/calendar/v3/calendars/{0}/events"
    url = url.format(urllib.quote_plus(cal_id))
    ### ASK FOR TODAY
    day = datetime.datetime.now() if date is None else date
    params = {
        'access_token': access_token,
        'orderBy': 'startTime',
        'singleEvents': 'true',
        'timeMin': day.strftime("%Y-%m-%dT00:00:00Z"),
        'timeMax': day.strftime("%Y-%m-%dT23:59:59Z")
    }
    url = "{0}?{1}".format(url, urllib.urlencode(params))
    r = urllib.urlopen(url)
    results = json.loads(r.read())
    events = []
    if 'items' not in results:
        return events
    for item in results['items']:
        if 'date' in item['start']:
            time = -1
        else:
            start = dateutil.parser.parse(item['start']['dateTime'])
            if start.minute == 0:
                time = start.strftime("%H")
            else:
                time = start.strftime("%H.%M")
        name = item['summary']
        events.append((time, name))
    return events

def events_to_text(events, header=''):
    ### IF NO EVENTS, IS FREE DAY
    if events==[]:
        events=[('12', u'Free day!!! No task for today....')]
    events = ["{0}: {1}".format(*e) if e[0] != -1 else e[1] for e in events]
    build = "{0}{1}".format(header, events[0])
    texts = []
    for event in events[1:]:
        if len(build) + len(event) > 200:
            texts.append(build)
            build = event
        else:
            build += ", {0}".format(event)
    return texts + [build]

def texts_for_user(access_token, user,  date=None, header=''):
    user_events = []
    user_events += get_todays_events(access_token, user, date)
    return events_to_text(user_events, header)

### HOMEPAGE FOR ACCESSING GOOGLE'S SERVICES ###
@app.route('/')
def index():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    ####### CREATE ACCESS TO APP AND SEND IT TO INDEX PAGE
    return flask.render_template('index.html', url=auth_url())

@app.route('/logout')
def logout():
    login_session.clear()
    #return redirect(url_for("index"))
    return redirect("https://mail.google.com/mail/u/0/?logout&hl=en")


####    WHEN RECEIVE ANSWER FROM GOOGLE, I CATCH CODE FOR BUILD TOKEN AND ASK SERVER FOR RESOURCES

@app.route('/callback')
def callback():
    ### WE CATCH RECEIVED ARGUMENT
    args = flask.request.args
    if args.get('error', None):
        return "Auth error: {0}".format(args['error'])
    code = args.get('code', None)
    if not code:
        return "No code received from Google"
    ### WE BUILD TOKEN FOR QUERYING GOOGLE+ AND GOOGLE CALENDAR'S API.
    tokens = create_token(code)
    token = tokens[0]

    ### SOME INTERESTING INFO FROM USER: NAME AND PICTURE (EMAIL NOT)
    profile = get_profile(token)

    ### I GOT THE EMAIL QUERYING THE CALENDAR,  BECAUSE I COULDN'T FROM GOOGLE+ API ###
    mail_adress=get_email(token)

    ### WE RECEIVE TODAY'S TASK FROMS CALENDAR "MAIL_ADDRESS"
    cadena=texts_for_user(token, mail_adress)

    ### THEN PRINT NAME, PICTURE AND TODAY'S TASKS (IN A DASH BOARD)
    return render_template("inicio.html", USERNAME=profile['name'],PHOTO_URL=profile['picture'],TAREAS=cadena[0])


if __name__ == '__main__':
    app.secret_key = 'fdsfmkrtjkfmdslfjfssgshfklsnvdsklj'
    app.run()
