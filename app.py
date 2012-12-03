import os
from flask import Flask, request, redirect, url_for, session, flash, g, render_template
from flask_oauth import OAuth
from pydo.Model import *
import re

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

DEBUG = False


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
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
    consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"]
)

engine = create_engine(os.environ["DATABASE_URL"])
db_session = scoped_session(sessionmaker(bind=engine))



# Load user from the session
@app.before_request
def before_request():
    #session['user_id'] = 1
    g.user = None
    if 'user_id' in session:
        g.user = db_session.query(User).filter(User.id == session['user_id']).first()

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

@app.route('/', methods=['GET', 'POST'])
def index():
    """ Render the application
    :return:

    """
    tag_filter = None
    if request.method == 'POST':
        _, tag_filter = filter_tokens(request.form["tag_filter"])
    return render_template('index.html', tag_filter=tag_filter)

@app.route('/list/create', methods=['POST'])
def create_list():
    """ Create a new list for the current user

    """
    list_title = request.form['list_title']
    g.user.lists.append(List(list_title))
    db_session.commit()
    return redirect(url_for('index'))

@app.route('/task/create', methods=['POST'])
def create_task():
    """ Create a new task for a list

    """
    task_description = request.form['task_description']
    list_id = request.form['list_id']
    if len(request.form['task_date']) > 0:
        try:
            task_date = datetime.strptime(request.form['task_date'], '%m-%d-%Y')
        except ValueError:
            flash("Invalid Date")
            return redirect(url_for('index'))
    else:
        task_date = None

    parsed_description, tags = filter_tokens(task_description)
    task = Task(parsed_description, task_date)
    for tag in tags:
        new_tag = Tag.get(db_session, tag)
        task.tags.append(new_tag)
    try:
        list = db_session.query(List).filter(List.id == list_id).first()
        list.tasks.append(task)
        db_session.commit()
    except BaseException:
        flash("Unable to save task")
    return redirect(url_for('index'))

@app.route('/task/update', methods=['POST'])
def update_task():
    """ Update a task with completed or delete commands

    """

    task = db_session.query(Task).filter(Task.id == request.form['task_id']).first()
    requestform = request.form
    if task:
        if 'task_completed' in request.form:
            task.completed = True
        else:
            task.completed = False
        if 'task_delete' in request.form:
            db_session.delete(task)
        db_session.commit()

    return redirect(url_for('index'))

def filter_tokens(description):
    # filter out tags
    reg_ex = re.compile(r'(\@\w*)')
    tokens = reg_ex.split(description)
    parsed_description = tokens[0].strip()
    tags = []
    for token in tokens:
        if '@' in token:
            tags.append(token.replace("@", ""))
    return parsed_description, tags



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
    g.user = None
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
    user.oauth_secret = response['oauth_token_secret']
    db_session.commit()

    session['user_id'] = user.id
    flash(u'Welcome')
    return redirect(url_for('index'))

# Bootstrap
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
