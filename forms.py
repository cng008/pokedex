from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import InputRequired, Email, email_validator, Optional, URL

class RegisterForm(FlaskForm):
    """Form for adding users."""

    email = EmailField('Email', validators=[InputRequired(), Email()])
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

class LoginForm(FlaskForm):
    """Form for logging in."""

    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])

class UserEditForm(FlaskForm):
    """Form for editing user login info."""

    profile_img_url = StringField('Profile Image URL', validators=[Optional(), URL()])
    username = StringField('Username', validators=[InputRequired()])
    location = StringField('Location')
    email = EmailField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
