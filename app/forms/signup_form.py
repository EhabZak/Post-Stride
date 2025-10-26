# from flask_wtf import FlaskForm
# from wtforms import StringField
# from wtforms.validators import DataRequired, Email, ValidationError, Length
# from app.models import User
# from zoneinfo import ZoneInfo


# def user_exists(form, field):
#     # Checking if user exists
#     email = field.data
#     user = User.query.filter(User.email == email).first()
#     if user:
#         raise ValidationError('Email address is already in use.')


# def username_exists(form, field):
#     # Checking if username is already in use
#     username = field.data
#     user = User.query.filter(User.username == username).first()
#     if user:
#         raise ValidationError('Username is already in use.')

# def timezone_valid(form, field):
#         # Validate it's a proper IANA timezone name (e.g., Asia/Dubai)
#         try:
#             ZoneInfo(field.data)
#         except Exception:
#             raise ValidationError('Invalid timezone name')


# class SignUpForm(FlaskForm):
#     username = StringField(
#         'username', validators=[DataRequired(), username_exists])
#     email = StringField('email', validators=[DataRequired(),Email(), user_exists])
#     password = StringField('password', validators=[DataRequired()])
#     timezone = StringField('timezone', validators=[DataRequired(), Length(max=64),timezone_valid])

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Email, ValidationError, Length
from zoneinfo import ZoneInfo
from app.models import User

# --- Helper filters (trim/lower) ---
def _strip(s):
    return s.strip() if isinstance(s, str) else s

def _lower(s):
    return s.lower().strip() if isinstance(s, str) else s

# --- External validators (DB checks / custom logic) ---
def user_exists(form, field):
    # Use a lighter query (only select id)
    email = field.data
    exists = User.query.with_entities(User.id).filter(User.email == email).first()
    if exists:
        raise ValidationError('Email address is already in use.')

def username_exists(form, field):
    username = field.data
    exists = User.query.with_entities(User.id).filter(User.username == username).first()
    if exists:
        raise ValidationError('Username is already in use.')

def timezone_valid(form, field):
    # Validate it's a proper IANA timezone name (e.g., Asia/Dubai)
    try:
        ZoneInfo(field.data)
    except Exception:
        raise ValidationError('Invalid timezone name')

# --- Form ---
class SignUpForm(FlaskForm):
    username = StringField(
        'username',
        filters=[_strip],
        validators=[
            DataRequired(),
            Length(min=3, max=40, message='Username must be 3–40 characters.'),
            username_exists
        ]
    )

    email = StringField(
        'email',
        filters=[_lower],  # normalize email to lowercase
        validators=[
            DataRequired(),
            Email(message='Invalid email address.'),
            Length(max=255, message='Email address must be 255 characters or fewer.'),
            user_exists
        ]
    )

    password = StringField(
        'password',
        validators=[
            DataRequired(),
            Length(min=6, max=128, message='Password must be 6–128 characters.')
        ]
    )

    timezone = StringField(
        'timezone',
        filters=[_strip],
        validators=[
            DataRequired(),
            Length(max=64),
            timezone_valid
        ]
    )

    
    
