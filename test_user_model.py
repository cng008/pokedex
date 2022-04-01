"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Favorite, Pokemon

# BEFORE we import our app, set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///pokedex-test"


# Now we can import app

from app import app

# Create tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        u1 = User.signup("email1@email.com", "test1", "password")
        u1.id = 111

        u2 = User.signup("email2@email.com", "test2", "password")
        u2.id = 222

        db.session.commit()

        u1 = User.query.get(u1.id)
        u2 = User.query.get(u2.id)

        self.u1 = u1
        self.u1id = u1.id

        self.u2 = u2
        self.u2id = u2.id

        self.client = app.test_client()


    def tearDown(self):
        """Clean up any fouled transaction."""

        db.session.rollback()


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no favorites
        self.assertEqual(len(u.favorites), 0)

        # test repr method
        self.assertEqual(u.__repr__(), "<User #1: testuser, test@test.com>")


####### FAVORITES TESTS ######################
    def test_favorited(self):
        """Did user1 favorite a pokemon?"""

        p1 = Pokemon(name='charizard', pokeapi_id=6)
        db.session.add(p1)
        db.session.commit()

        self.u1.favorites.append(p1)
        db.session.commit()

        self.assertEqual(len(self.u1.favorites), 1)


####### SIGNUP TESTS ######################
    def test_valid_signup(self):
        u3 = User.signup("emailnew@email.com", "testnew", "password")
        u3.id = 333
        db.session.commit()

        u3 = User.query.get(u3.id)
        self.assertEqual(u3.email, "emailnew@email.com")
        self.assertEqual(u3.username, "testnew")
        self.assertNotEqual(u3.password, "password")
        # Bcrypt strings should start with $2b$
        self.assertTrue(u3.password.startswith("$2b$"))


    def test_invalid_username_signup(self):
        invalid = User.signup("testest@email.com", None, "password")
        invalid.id = 9999
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_invalid_email_signup(self):
        invalid = User.signup(None, "testest", "password")
        invalid.id = 8888
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()


    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("email@email.com", "testtest", "")
        
        with self.assertRaises(ValueError) as context:
            User.signup("email@email.com", "testtest", None)
    

####### AUTHENTICATION TESTS ######################
    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.u1.id)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "notpassword"))
