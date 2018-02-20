from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash

from sqlalchemy import create_engine, asc, desc, and_
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, CategoryItem
from flask import session as login_session

import random
import string

# Imports for Gconnect and FBconnect
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Declare my client ID
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"

# Connect to database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBsession = sessionmaker(bind=engine)
session = DBsession()


# -----------------------------------------------------------------------------
# API ENDPOINT

# JSON APIs to view catalog information
@app.route('/catalog/JSON')
def catalogJSON():
    catalog = session.query(Category).all()
    return jsonify(catalog=[i.serialize for i in catalog])

# JSON APIs to view category information


@app.route('/catalog/<category_name>/JSON')
def categoryJSON(category_name):
    category = session.query(Category).filter_by(name=category_name).one()
    items = session.query(CategoryItem).filter_by(category=category).all()
    return jsonify(category=[i.serialize for i in items])

# JSON APIs to view item information


@app.route('/catalog/<category_name>/<item_title>/JSON')
def itemJSON(category_name, item_title):
    category = session.query(Category).filter_by(name=category_name).one()
    item = session.query(CategoryItem).filter(and_(
        CategoryItem.category_id == category.id),
        CategoryItem.title == item_title).first()
    return jsonify(item=item.serialize)


# -----------------------------------------------------------------------------
# AUTHENTICATION

# Create a state token to prevent request forgery
# Store it in the session for later validation
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# GOOGLE PLUS CONNECT
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate stake token
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
            json.dumps("Token's user ID doesn't match given user ID"), 401)
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
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
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

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    print data
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: 100px; border-radius: 150px; '
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# GOOGLE PLUS DISCONNECT


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # print 'In gdisconnect access token is %s', access_token
    # print 'User name is: '
    # print login_session['username']

    # Execute HTTP GET request to revoke current token.
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    # print 'result is '
    # print result
    if result['status'] == '200':
        # Reset the user's sesson.s
        response = make_response(json.dumps(
            'Successfully Disconnected! Redirecting ...'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps(
            'Failed to Revoke Token For Given User.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# DISCONNECT
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
        flash('You have successfully logged out.')
        return redirect(url_for('showCategories'))
    else:
        flash('You were not logged in to begin with.')
        redirect(url_for('showCategories'))

# -----------------------------------------------------------------------------
# CATALOG HTML ENDPOINTS


# Show all categories
@app.route('/')
@app.route('/catalog/')
def showCategories():
    """HTML endpoint provides a list of all categories"""
    categories = session.query(Category).all()

    categories_count = session.query(Category).order_by(
        Category.id.desc()).first().id
    items_count = session.query(CategoryItem).order_by(
        CategoryItem.id.desc()).first().id

    if categories_count <= items_count:
        if items_count >= 5:
            items = session.query(CategoryItem).order_by(
                CategoryItem.id.desc()).limit(5)
        else:
            items = session.query(CategoryItem).order_by(
                CategoryItem.id.desc()).limit(categories_count)
    else:
        items = session.query(CategoryItem).order_by(
            CategoryItem.id.desc()).all()

    if 'username' not in login_session:
        return render_template(
            'publiccatalog.html', categories=categories, items=items)
    else:
        return render_template(
            'catalog.html', categories=categories, items=items)


# Show all items from a chosen category
@app.route('/catalog/<chosen_category>/items')
def showItems(chosen_category):
    """HTML endpoint provides a list of all items from the chosen category"""
    chosenCategory = session.query(Category).filter(
        Category.name == chosen_category).first()
    chosenItems = session.query(CategoryItem).filter(
        CategoryItem.category_id == chosenCategory.id)
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return render_template('publiccategory.html',
                               categories=categories,
                               chosen_category=chosen_category,
                               items=chosenItems)
    else:
        return render_template('category.html',
                               categories=categories,
                               chosen_category=chosen_category,
                               items=chosenItems)


# Show item description
@app.route('/catalog/<chosen_category>/<chosen_item>')
def showDescription(chosen_category, chosen_item):
    """HTML endpoint provides a description of the chosen item"""
    chosenCategory = session.query(Category).filter(
        Category.name == chosen_category).first()
    chosenItem = session.query(CategoryItem).filter(and_(
        CategoryItem.category_id == chosenCategory.id),
        CategoryItem.title == chosen_item).first()
    return render_template('description.html', item=chosenItem)


# Add new category
@app.route('/catalog/new', methods=['GET', 'POST'])
def addCategory():
    """HTML endpoint add new category for logined user"""
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        newCategory = Category(name=request.form['name'],
                               user_id=login_session['user_id'])
        session.add(newCategory)
        flash('New category %s successfully created' % newCategory.name)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newcategory.html')


# Add new item
@app.route('/catalog/newitem', methods=['GET', 'POST'])
def addItem():
    """HTML endpoint add new item for logined user"""
    if 'username' not in login_session:
        return redirect('/login')

    existCategoryNames = [i.name for i in session.query(Category).all()]

    if request.method == 'POST':
        
        if not (request.form['title'] and request.form['description']):
            flash("Category name, Item title and description are necessary!")
            return render_template('newitem.html')

        newItem = CategoryItem(
            title=request.form['title'],
            description=request.form['description'],
            user_id=login_session['user_id'],
            category_id=getCategoryID(request.form.get('name'))
        )
        session.add(newItem)
        session.commit()

        flash('New item %s successfully created' % newItem.title)
        return redirect(url_for('showCategories'))
    else:
        # return render_template('newitem.html')
        return render_template('newitem.html', categories=existCategoryNames)


# Edit item
@app.route('/catalog/<item_title>/edit', methods=['GET', 'POST'])
def editItem(item_title):
    if 'username' not in login_session:
        return redirect('/login')

    editItem = session.query(CategoryItem).filter_by(title=item_title).one()

    if login_session['user_id'] != editItem.user_id:
        flash('You are not authorized to edit this item to this category.')
        return redirect(
            url_for('showItems', chosen_category=getCategoryName(item_title)))

    if request.method == 'POST':
        if (request.form['name'] and request.form['title'] and
                request.form['description']):
            editItem.title = request.form['title']
            editItem.description = request.form['description']
            editItem.category_id = getCategoryID(request.form['name'])
            session.add(editItem)
            session.commit()
            flash("Item Successfully Edited")
            return redirect(
                url_for('showItems', chosen_category=request.form['name']))
        else:
            flash("Category name, Item title and description are all needed!")
            return render_template('edititem.html', item=editItem)
    else:
        return render_template('edititem.html', item=editItem)


# Delete item
@app.route('/catalog/<item_title>/delete', methods=['GET', 'POST'])
def deleteItem(item_title):
    if 'username' not in login_session:
        return redirect('/login')

    deleteItem = session.query(CategoryItem).filter_by(title=item_title).one()

    if login_session['user_id'] != deleteItem.user_id:
        flash('You are not authorized to delete this item to this category.')
        return redirect(
            url_for('showItems', chosen_category=getCategoryName(item_title)))

    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash("Item Successfully Deleted")
        return redirect(url_for('showCategories'))
    else:
        return render_template('deleteitem.html', item=deleteItem)

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(
        name=login_session['username'], email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getCategoryID(name):
    category = session.query(Category).filter_by(name=name).one()
    return category.id


def getCategoryName(title):
    item = session.query(CategoryItem).filter_by(title=title).one()
    return item.category.name


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

