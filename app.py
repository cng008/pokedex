"""Flask app for Pokedex"""
from flask import Flask, render_template
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Favorite, Pokemon

import os
import re
uri = os.environ.get('DATABASE_URL', 'postgresql:///pokedex')
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
# rest of connection code using the connection string `uri`

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "shhhhhh"
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)

##############################################################################
# Homepage and error pages

@app.route('/')
def home_page():
    """Homepage."""
    return render_template('base.html')


@app.errorhandler(404)
def page_not_found(e):
    """Show 404 NOT FOUND page."""

    return render_template('404.html'), 404


##############################################################################
# User signup/login/logout
