from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Manufacturer, Disc, User
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from functools import wraps

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Disc Golf App"

engine = create_engine('postgresql://grader:grader@52.38.7.112/discgolf')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase +
            string.digits) for x in xrange(32))
    login_session['state'] = state
    #return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/v2.8/oauth/access_token?grant_type=\
           fb_exchange_token&client_id=%s&client_secret=%s&\
           fb_exchange_token=%s' % (
          app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    # extract access token from response:
    token = 'access_token=' + data['access_token']

    # Use token to get user info from the API:
    url = 'https://graph.facebook.com/v2.8/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout.
    # let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?%s&redirect=\
          0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="' + login_session['picture'] + '"'
    output += 'style = "width: 300px; height: 300px;border-radius: 150px;\
              -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
           facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "You have been logged out."


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already\
                                             connected.'),200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    app.logger.warning(data)

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome'
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="' + login_session['picture'] + '"'
    output += 'style = "width: 300px; color: #2460c1; height: 300px;\
              border-radius: 150px;-webkit-border-radius: 150px;\
              -moz-border-radius: 150px;"> '
    flash("You have logged in successfully using Google")
    print "done!"
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    app.logger.warning(user.id)
    app.logger.warning(user.name)
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/manufacturer/<int:manufacturer_id>/discs/JSON')
def manufacturerJSON(manufacturer_id):
    manufacturer = session.query(Manufacturer).filter_by(id=manufacturer_id).one()
    discs = session.query(Disc).filter_by(manufacturer_id=manufacturer_id).all()
    return jsonify(Discs=[disc.serialize for disc in discs])


@app.route('/manufacturer/<int:manufacturer_id>/discs/<int:disc_id>/JSON')
def discJSON(manufacturer_id, disc_id):
    disc = session.query(Disc).filter_by(id=disc_id).one()
    return jsonify(disc = disc.serialize)



@app.route('/manufacturer/JSON')
def manufacturersJSON():
    manufacturers = session.query(Manufacturer).all()
    return jsonify(manufacturers=[manufacturer.serialize for
                                  manufacturer in manufacturers])


# View the names of all manufacturers
@app.route('/')
@app.route('/allmanufacturers')
def showManufacturers():
    #return "This page will show all the manufacturers"
    manufacturers = session.query(Manufacturer).order_by(asc(Manufacturer.name))
    if 'username' not in login_session:
        return render_template('allmanufacturerspublic.html',
                                manufacturers = manufacturers)
    else:
        return render_template('allmanufacturers.html',
                                manufacturers = manufacturers)


# Create a new manufacturer
@app.route('/manufacturer/new', methods=['GET', 'POST'])
@login_required
def newManufacturer():
    if request.method == 'POST':
        newManufacturer = Manufacturer(name=request.form['name'],
                                       user_id=login_session['user_id'])
        session.add(newManufacturer)
        flash('New Manufacturer %s Successfully Added' % newManufacturer.name)
        session.commit()
        return redirect(url_for('showManufacturers'))
    else:
        return render_template('newmanufacturer.html')



# Edit a manufacturer
@app.route('/manufacturer/<int:manufacturer_id>/edit', methods=['GET', 'POST'])
@login_required
def editManufacturer(manufacturer_id):
    editedManufacturer = session.query(Manufacturer).filter_by(id=manufacturer_id).one()
    if editedManufacturer.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized\
         to edit this manufacturer. Please create your own manufacturer\
          in order to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedManufacturer.name = request.form['name']
            flash('Manufacturer successfully edited %s' %
                  editedManufacturer.name)
            return redirect(url_for('showManufacturers'))
    else:
        return render_template('editManufacturer.html',
                                manufacturer=editedManufacturer)


# Delete a manufacturer (including all their discs)
@app.route('/manufacturer/<int:manufacturer_id>/delete', methods=['GET','POST'])
@login_required
def deleteManufacturer(manufacturer_id):
    manufacturerToDelete = session.query(Manufacturer).filter_by(id=manufacturer_id).one()
    if manufacturerToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized\
               to delete this manufacturer. Please create your own manufacturer\
               in order to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(manufacturerToDelete)
        flash('%s successfully deleted' % manufacturerToDelete.name)
        session.commit()
        return redirect(url_for('showManufacturers',
                                 manufacturer_id=manufacturer_id))
    else:
        return render_template('deleteManufacturer.html',
                                manufacturer=manufacturerToDelete)

# View a manufacturer's discs
@app.route('/manufacturer/<int:manufacturer_id>')
@app.route('/manufacturer/<int:manufacturer_id>/discs')
def showDiscs(manufacturer_id):
    manufacturer = session.query(Manufacturer).filter_by(id=manufacturer_id).one()
    creator = getUserInfo(manufacturer.user_id)
    discs = session.query(Disc).filter_by(manufacturer_id=manufacturer_id).all()
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('manufacturerpublic.html', discs = discs,
                                manufacturer = manufacturer, creator = creator)
    else:
        return render_template('manufacturer.html', discs = discs,
                                manufacturer = manufacturer, creator = creator)

# Create a new disc
@app.route('/manufacturer/<int:manufacturer_id>/discs/new',
            methods=['GET','POST'])
@login_required
def newDisc(manufacturer_id):
    manufacturer = session.query(Manufacturer).filter_by(id=manufacturer_id).one()
    if login_session['user_id'] != manufacturer.user_id:
        return "<script>function myFunction() {alert('You are not authorized\
               to add new discs to this manufacturer's collection.');}</script>\
               <body onload='myFunction()''>"
    if request.method == 'POST':
        newDisc = Disc(name=request.form['name'], description=
                       request.form['description'],disc_type=request.form
                       ['disc_type'], speed=request.form['speed'],
                       glide=request.form['glide'], turn=request.form['turn'],
                       fade=request.form['fade'],
                       manufacturer_id=manufacturer_id)
        session.add(newDisc)
        session.commit()
        flash("You added disc %s to the manufacturer's collection!" %
              newDisc.name)

        return redirect(url_for('showDiscs', manufacturer_id=manufacturer_id))
    else:
        return render_template('newdisc.html', manufacturer_id=manufacturer_id)


# Edit a disc
@app.route('/manufacturer/<int:manufacturer_id>/discs/<int:disc_id>/edit',
            methods=['GET','POST'])
@login_required
def editDisc(manufacturer_id, disc_id):
    editedDisc = session.query(Disc).filter_by(id=disc_id).one()
    manufacturer = session.query(Manufacturer).filter_by(id=manufacturer_id).one()
    if login_session['user_id'] != manufacturer.user_id:
        return "<script>function myFunction() {alert('You are not authorized\
               to edit discs from this manufacturer.');}</script><body onload=\
               'myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedDisc.name = request.form['name']
        if request.form['description']:
            editedDisc.description = request.form['description']
        if request.form['disc_type']:
            editedDisc.disc_type = request.form['disc_type']
        if request.form['speed']:
            editedDisc.speed = request.form['speed']
        if request.form['glide']:
            editedDisc.glide = request.form['glide']
        if request.form['turn']:
            editedDisc.turn = request.form['turn']
        if request.form['fade']:
            editedDisc.fade = request.form['fade']
        session.add(editedDisc)
        session.commit()
        flash('Disc edited successfully')
        return redirect(url_for('showDiscs', manufacturer_id=manufacturer_id))
    else:
        return render_template('editdisc.html', manufacturer_id=manufacturer_id,
                                disc_id=disc_id, disc=editedDisc)


# Delete a disc
@app.route('/manufacturer/<int:manufacturer_id>/discs/<int:disc_id>/delete',
             methods=['GET','POST'])
@login_required
def deleteDisc(manufacturer_id, disc_id):
    manufacturer = session.query(Manufacturer).filter_by(id=manufacturer_id).one()
    discToDelete = session.query(Disc).filter_by(id=disc_id).one()
    if login_session['user_id'] != manufacturer.user_id:
        return "<script>function myFunction() {alert('You are not authorized\
                to delete discs belonging to this manufacturer.');}</script>\
                <body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(discToDelete)
        session.commit()
        flash('Disc successfully deleted')
        return redirect(url_for('showDiscs', manufacturer_id=manufacturer_id))
    else:
        return render_template('deletedisc.html',
                                manufacturer_id=manufacturer_id,
                                disc=discToDelete)

@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully logged out.")
        return redirect(url_for('showManufacturers'))
    else:
        flash("You were not logged in.")
        return redirect(url_for('showManufacturers'))



if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.debug = True
    app.run(host = '172.26.15.116', port = 2200)