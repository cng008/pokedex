"""Flask app for Pokedex"""
from flask import Flask, render_template, redirect, flash, session, g, request
from flask_debugtoolbar import DebugToolbarExtension
import requests

from models import db, connect_db, User, Favorite, Pokemon
from forms import RegisterForm, LoginForm, UserEditForm
from pokemons import all_pokemon
from sqlalchemy.exc import IntegrityError
import random

import os
import re
uri = os.environ.get('DATABASE_URL', 'postgresql:///pokedex')
if uri.startswith('postgres://'):
    uri = uri.replace('postgres://', 'postgresql://', 1)
# rest of connection code using the connection string `uri`

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'shhhhhh'
app.config['SQLALCHEMY_ECHO'] = True

connect_db(app)
db.create_all()

CURR_USER_KEY = 'username'
API_BASE_URL = 'https://pokeapi.co/api/v2'


##############################################################################
# HOMEPAGE AND ERROR PAGES

@app.route('/')
def home_page():
    """Homepage. See first 20 pokemon."""

    pokemon = [i for i in requests.get(f'{API_BASE_URL}/pokemon/?limit=15').json()['results']]
    pokemon_data = [fetch_poke(i['name']) for i in pokemon] # https://medium.com/@sergio13prez/fetching-them-all-poke-api-62ca580981a2
    
    return render_template('pokemon/home.html', pokemon_data=pokemon_data, all_pokemon=all_pokemon, isIndex=True)


@app.errorhandler(404)
def page_not_found(e):
    """Show 404 NOT FOUND page."""

    return render_template('404.html', all_pokemon=all_pokemon), 404


##############################################################################
# GENERAL POKEMON SEARCH ROUTES

def fetch_poke(pokemon_name):
    """Return {id, name, image, types} from PokeApi for given search term."""

    resp = requests.get(f"{API_BASE_URL}/pokemon/{pokemon_name}")
    data = resp.json()

    id = data['id']
    name = data['name']
    img = data['sprites']['other']['official-artwork']['front_default']
    pokedex_img = data['sprites']['front_default']
    types = data['types']
    base_xp = data['base_experience']
    height = data['height']
    weight = data['weight']
    abilities = data['abilities']

    return {'id':id},{'name':name},{'image':img},{'pokedex_img':pokedex_img},{'types':types},{'base_xp':base_xp},{'height':height},{'weight':weight},{'abilities':abilities}


def fetch_evolutions(pokemon_name):
    """Return all pokemon evolutions (if exists) from PokeApi for given search term.
        Not every pokemon will have more than one evolution, so a catch/error accounts for that.
    """

    get_url = requests.get(f"{API_BASE_URL}/pokemon-species/{pokemon_name}").json()['evolution_chain']['url']
    chain = requests.get(get_url).json()['chain']

    first_evol = chain['species']['name']
    try: 
        second_evol = chain['evolves_to'][0]['species']['name']
    except IndexError:
        second_evol = None

    try: 
        third_evol = chain['evolves_to'][0]['evolves_to'][0]['species']['name']
    except IndexError:
        third_evol = None

    try: 
        fourth_evol = chain['evolves_to'][0]['evolves_to'][0]['evolves_to'][0]['species']['name']
    except IndexError:
        fourth_evol = None

    return [first_evol,second_evol,third_evol,fourth_evol]


def fetch_blurb(pokemon_name):
    """Generates a random fact about the pokemon on page load."""
    
    data = requests.get(f"{API_BASE_URL}/pokemon-species/{pokemon_name}").json()['flavor_text_entries']
    blurbs = []
    for i in data:
        if i['language']['name'] == 'en':
            blurbs.append(i['flavor_text'])

    return random.choice(blurbs)


@app.route('/pokemon/')
def get_poke():
    """Handle form submission; return form, showing pokemon info from submission."""

    search = request.args.get('search').lower().replace(' ', '-')
    try:
        pokemon = fetch_poke(search)
    except requests.exceptions.JSONDecodeError:
        return render_template('/pokemon/no-results.html', all_pokemon=all_pokemon, isIndex=True)

    return render_template('pokemon/results.html', pokemon=pokemon, all_pokemon=all_pokemon, isIndex=True)


@app.route('/pokemon/<pokemon_name>')
def poke_details(pokemon_name):
    """View details page of pokemon.
        Includes evolutions of the pokemon.
        Check if pokemon is in favorites if user is logged in.
    """

    pokemon_data = fetch_poke(pokemon_name)
    blurb = fetch_blurb(pokemon_name)

    evolutions_list = fetch_evolutions(pokemon_name)
    clean_list = []
    for i in evolutions_list:
        if i != None:
            clean_list.append(i)
    evolutions_data = [fetch_poke(i) for i in clean_list]

    poke_id = pokemon_data[0]['id']
    name = pokemon_data[1]['name']

    check_pokemon = Pokemon.query.get(name)

    if not check_pokemon:
        add_pokemon = Pokemon(name=name, pokeapi_id=poke_id)
        db.session.add(add_pokemon)
        db.session.commit()

    if g.user:        
        pokemon = (Pokemon.query.all())
        faved_pokemon_names = [favorite.name for favorite in g.user.favorites]
        return render_template('pokemon/show.html', pokemon=pokemon_data, blurb=blurb, evolutions=evolutions_data, all_pokemon=all_pokemon, favs=faved_pokemon_names)

    return render_template('pokemon/show.html', pokemon=pokemon_data, blurb=blurb, evolutions=evolutions_data, all_pokemon=all_pokemon)


##############################################################################
# FAVORITES ROUTE

@app.route('/pokemon/<pokemon_name>/fav', methods=['POST'])
def add_favorite(pokemon_name):
    """Toggle a liked pokemon for the currently-logged-in user."""

    favorited_poke = Pokemon.query.get_or_404(pokemon_name)
    user_favs = g.user.favorites

    if favorited_poke in user_favs:
        g.user.favorites = [fav for fav in user_favs if fav != favorited_poke]
    else:
        g.user.favorites.append(favorited_poke)

    db.session.commit()

    return redirect(request.referrer) # https://stackoverflow.com/a/61902927
    # return redirect(f"pokemon/{pokemon_name}") # use this instead for testing


##############################################################################
# USER SIGNUP/LOGIN/LOGOUT

@app.before_request
def add_user_to_g():
    """Runs before each request
        If we're logged in, add curr user to Flask global.
        g is a global namespace for holding any data you want during a single app context
    """

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/register', methods=["GET", "POST"])
def create_user():
    """Handle user signup."""

    if CURR_USER_KEY in session:
        flash("You're already logged in!", 'info')
        return redirect(f"/user/{session[CURR_USER_KEY]}")

    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = User.signup(
                email=form.email.data,            
                username=form.username.data,
                password=form.password.data)
            db.session.commit()

        except IntegrityError:
            form.username.errors.append('Username taken. Please pick another.')
            return render_template('user/register.html', form=form)

        do_login(user)
        flash("Welcome! Your account was created (-:", "success")
        return redirect("/")

    else:
        return render_template('user/register.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    if CURR_USER_KEY in session:
        flash("You're already logged in!", 'info')
        return redirect(f"/user/{session[CURR_USER_KEY]}")

    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}, welcome back!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('user/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    if not g.user:
        flash("You need to be logged into an account to do that...", "primary")
        return redirect('/')

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
        flash("You've been logged out.", "success")
        return redirect('/')


##############################################################################
# GENERAL USER ROUTES

@app.route('/user')
def user_show_favorites():
    """Show user profile.
        Show list of pokemon user has favorited.
    """

    if CURR_USER_KEY not in session:
        flash("Access unauthorized.", "primary")
        return redirect("/")

    fav_pokemon = [fetch_poke(pokemon.name) for pokemon in g.user.favorites]

    return render_template('user/favorites.html', user=g.user, favorites=fav_pokemon , all_pokemon=all_pokemon)


@app.route('/user/edit', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "primary")
        return redirect("/")
    
    user = g.user

    form = UserEditForm(obj=user)
    if form.validate_on_submit():
        try:
            if User.authenticate(user.username, form.password.data):
                user.profile_img_url = form.profile_img_url.data or User.profile_img_url.default.arg,
                user.username = form.username.data
                user.location = form.location.data
                user.email = form.email.data

                db.session.commit()
                flash(f"Your settings were saved!", "success")
                return redirect(f"/user")

        except IntegrityError:
            db.session.rollback()
            form.username.errors.append('Username taken. Please pick another.')
            return render_template('user/edit.html', form=form)

        flash("Invalid password.", 'primary')
    return render_template('user/edit.html', form=form)


@app.route('/user/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "primary")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/")


##############################################################################
# Turn off all caching in Flask
#   automatically close all unused/hanging connections and prevent bottleneck in your code

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()
# https://stackoverflow.com/a/53715116

