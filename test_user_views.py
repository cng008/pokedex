"""User views tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import db, connect_db, User, Favorite, Pokemon

# BEFORE we import our app, set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///pokedex-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(email="test@test.com",
                                    username="testuser",
                                    password="testuser")
        self.testuser.id = 8888

        db.session.commit()


    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()


###########################################################################
# USER ROUTES

    def test_show_user(self):

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id

            resp = client.get("/user")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser", str(resp.data))


    def test_add_no_session(self):
        """Is user logged in when adding a message?"""

        with self.client as client:
            resp = client.post("/user", follow_redirects=True)
            self.assertEqual(resp.status_code, 405)
            self.assertIn("Method Not Allowed", str(resp.data))
    

    def test_show_user_profile_invalid(self):
        """Redirect to home if user is not logged in"""
        with self.client as client:
            resp = client.get("/user", 
                            follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Caterpie", str(resp.data))
            # Should redirect to home if user is not logged in and tries to access their user profile


# ###########################################################################
# FAVORITES ROUTES

    def setup_favorites(self):
        p1 = Pokemon(name="dog", pokeapi_id=1)
        p2 = Pokemon(name="cat", pokeapi_id=2)
        db.session.add_all([p1, p2])
        db.session.commit()

        f1 = Favorite(user_id=self.testuser.id, poke_name="dog")

        db.session.add_all([f1])
        db.session.commit()


    def test_add_favorite(self):
        self.setup_favorites()
       
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id

            # make post request to favorite a pokemon
            resp = client.post("/pokemon/cat/fav", 
                                follow_redirects=True)

        f = Favorite.query.filter(Favorite.poke_name=="cat").all()

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(f), 1)
        self.assertEqual(f[0].user_id, self.testuser.id)
        self.assertIn("cat", str(resp.data))


    def test_remove_favorite(self):
        """Check to see if the pokemon is favorited by the user. If it is, then we can unfavorite it."""
        self.setup_favorites()

        # get the favorited pokemon 
        p = Pokemon.query.filter(Pokemon.name=="dog").one()
        self.assertIsNotNone(p)
        
        # query the pokemon which is favorited by the logged in user
        f = Favorite.query.filter(Favorite.user_id==self.testuser.id and Favorite.poke_name==p.name).one()

        # check if there is a favorite
        self.assertIsNotNone(f)

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id

            # make post request to favorite that pokemon so we can unfavorite it
            resp = client.post(f"/pokemon/{p.name}/fav", 
                                follow_redirects=True)

            f = Favorite.query.filter(Favorite.poke_name==p.name).all()

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(f), 0)