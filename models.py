"""SQLAlchemy models for Pokedex."""

import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


def connect_db(app):
    """Connect database to provided Flask app."""

    db.app = app
    db.init_app(app)


class User(db.Model):
    """User."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(254), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=True, unique=True)
    password = db.Column(db.Text, nullable=False)
    # location = db.Column(db.Text)
    account_creation = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now)

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, email, username, password):
        """Sign up user.
        Hashes password and adds user to system.
        """

        hashed_pw = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            email=email,
            username=username,
            password=hashed_pw,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

    @property
    def friendly_date(self):
        """Return nicely-formatted date."""
        return self.account_creation.strftime("%b %-d,  %Y @ %-I:%M %p")


class Favorite(db.Model):
    """Favorite pokemon for user."""
    __tablename__ = 'favorites'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'), primary_key=True)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemon.id', ondelete='cascade'), primary_key=True)


class Pokemon(db.Model):
    """Pokemon."""
    __tablename__ = 'pokemon'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False, unique=True)