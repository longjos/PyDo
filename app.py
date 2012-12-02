import os
from flask import Flask, request, redirect, url_for, session, flash, g, render_template
from flask_oauth import OAuth
from pydo.Model import *

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

DEBUG = True


__author__="jlon"
__date__ ="$Dec 1, 2012 11:50:19 AM$"

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
app.debug = DEBUG
oauth = OAuth()

# Setup the remote application we are going to authenticate with
twitter = oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/authenticate',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
    consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"]
)

engine = create_engine(os.environ["DATABASE_URL"])
db_session = scoped_session(sessionmaker(bind=engine))

# Load user from the session
@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])

# Close database connection after request is processed
@app.after_request
def after_request(response):
    db_session.remove()
    return response

# Use this function to initialize the model into the target database
def init_db():
    import pydo.Model
    pydo.Model.init_db(engine)

# Setup OAuth handler
@twitter.tokengetter
def get_twitter_token():
    user = g.user
    if user is not None:
        return user.oauth_token, user.oauth_secret


# Begin application logic

@app.route('/')
def index():
    """ Render the application
    :return:

    """
    return render_template('index.html')

@app.route('/login')
def login():
    """ Begin the authorization process
    :return:

    """
    return twitter.authorize(callback=url_for('oauth_authorized'))

@app.route('/logout')
def logout():
    """ Clear user from the session
    :return:

    """
    session.pop('user_id', None)
    return render_template("index.html")

@app.route('/oauth-authorized')
@twitter.authorized_handler
def oauth_authorized(response):
    """ Handle the OAuth response. Associate to a local user if possible
        and put them in the session
    :param response:
    :return:

    """
    if response is None:
        flash(u'Request denied')
        return redirect(url_for('index'))

    # Find an existing user
    user = db_session.query(User).filter(User.display_name == response['screen_name']).first()
    #.query.filter_by(display_name = response['screen_name']).first()

    if user is None:
        # New user
        user = User(response['screen_name'])
        db_session.add(user)

    user.oauth_token = response['oauth_token']
    user.oauth_secret = response['oauth_secret']
    db_session.commit()

    session['user_id'] = user.id
    flash(u'Welcome')
    return redirect(url_for('index'))

# Bootstrap
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
