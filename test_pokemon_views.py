"""Pokemon View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_pokemon_views.py


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


class PokemonViewTestCase(TestCase):
    """Test views for pokemon."""

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


#######################################################################
# SHOW POKEMON SEARCH RESULTS
    
    def test_show_valid_search_results(self):
        """Show valid pokemon results from a user's search input"""

        with self.client as client:
            res = client.get('/pokemon?search=pikachu', 
                             follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            # should show heading indicating number of results for that search
            self.assertIn("pikachu ", str(res.data))


    def test_show_invalid_pokemon_result(self):
        """Try to route to a pokemon that doesn't exist in database"""
        with self.client as client:
           
            res = client.get('/pokemon/99999',
                             follow_redirects = True)

            self.assertEqual(res.status_code, 200)
            self.assertIn("Page Not Found", str(res.data))


# #######################################################################
# # SHOW AN INDIVIDUAL POKEMON'S DETAILS

    def test_pokemon_show(self):
        """Show the details for a valid individual pokemon"""

        with self.client as client:
            res = client.get(f'/pokemon/pikachu')

            self.assertEqual(res.status_code, 200)
            self.assertIn("lightning-rod", str(res.data))


    def test_invalid_pokemon_show(self):
        """Does pokemon exist?"""

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = client.get('/pokemon/99999',
                             follow_redirects = True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid path", str(resp.data))


# #######################################################################
# Test Invalid Routes (404, 405 errors)

    def test_invalid_route_404(self):
        """Try to route to a page that doesn't exist in the app"""

        with self.client as client:
            res = client.get('/neopets',
                             follow_redirects = True)

        self.assertEqual(res.status_code, 404)
        self.assertIn("404: Page Not Found", str(res.data))


    def test_invalid_route_405(self):
        """Try to route a method which is not allowed"""

        with self.client as client:
            res = client.get('/pokemon/91730/fav',
                             follow_redirects = True)

        self.assertEqual(res.status_code, 405)

        # Method not allowed since pokemon (id 91730) does not exist in the database
        self.assertIn("405: Method Not Allowed", str(res.data))
    