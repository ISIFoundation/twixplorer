# coding: utf-8
#
#  Copyright (C) 2012 André Panisson
#  You can contact me by email (panisson@gmail.com) or write to:
#  Via Alassio 11/c - 10126 Torino - Italy
#
from flask import request, redirect, url_for, session
#from flaskextlocal.oauth import OAuth
import flask
import config


# setup flask
app = flask.Flask(__name__)
app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY

from auth import mod as auth_mod
from collector import mod as collector_mod

app.register_blueprint(auth_mod)
app.register_blueprint(collector_mod)


@app.route('/')
def index():
    # app.logger.debug(request.url_rule.endpoint)
    if 'screen_name' in flask.session:
        return redirect(url_for('collector.main'))
    else:
        return flask.render_template('index.html')


@app.route('/about')
def about():
    return flask.render_template('about.html')


if __name__ == "__main__":
    # Starting flask
    app.run(host='0.0.0.0', port=8080)
