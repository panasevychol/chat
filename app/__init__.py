import os
from gevent import monkey
from flask import Flask, Response, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from config import basedir

monkey.patch_all()

app = Flask(__name__)
app.config.from_object('config')
app.debug = True
app.config['PORT'] = 5000

db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
oid = OpenID(app, os.path.join(basedir, 'tmp'))

from app import views, models

