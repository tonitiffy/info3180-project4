from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.httpauth import HTTPBasicAuth

app = Flask(__name__)
app.config.from_pyfile('config.py')

db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view='signin'

auth = HTTPBasicAuth()

from app import views, models