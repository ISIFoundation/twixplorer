# coding: utf-8
#
#  Copyright (C) 2012 André Panisson
#  You can contact me by email (panisson@gmail.com) or write to:
#  Via Alassio 11/c - 10126 Torino - Italy
#
from flask import request, redirect, url_for, session, Blueprint
from requests_oauthlib.oauth1_auth import Client
import requests
import config

# setup module
mod = Blueprint("auth", __name__)

oauth = Client(config.CONSUMER_KEY, client_secret=config.CONSUMER_SECRET)

@mod.route('/login')
def login():
    uri, headers, body = oauth.sign('https://twitter.com/oauth/request_token')
    res = requests.get(uri, headers=headers, data=body)
    res_split = res.text.split('&') # Splitting between the two params sent back
    oauth_token = res_split[0].split('=')[1] # Pulling our APPS OAuth token from the response.
    
    #TODO: add callback?
#    callback = "http://localhost:8080/oauth-authorized"
#    params['redirect_uri'] = callback

    return redirect('https://api.twitter.com/oauth/authenticate?'+
        'oauth_token=' + oauth_token, 302)


@mod.route('/logout')
def logout():
    session.pop('screen_name', None)
    return redirect(request.referrer or url_for('index'))

@mod.route('/oauth-authorized')
def oauth_authorized():
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    
    if oauth_token is None:
        return redirect(next_url)
    
    res = requests.post('https://api.twitter.com/oauth/access_token?oauth_token=' + oauth_token + '&oauth_verifier=' + oauth_verifier)
    print(res.text)
    res_split = res.text.split('&')
    oauth_token = res_split[0].split('=')[1]
    oauth_secret = res_split[1].split('=')[1]
    userid = res_split[2].split('=')[1]
    username = res_split[3].split('=')[1]

    next_url = request.args.get('next') or url_for('index')

#     screen_name = resp['screen_name']
#     oauth_token = resp['oauth_token']
#     oauth_token_secret = resp['oauth_token_secret']

#     user = User.select_by_screen_name(screen_name)
#     if not user:
#         app.logger.debug('User not found on database. Using the Twitter API')
#         auth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
#         auth.set_access_token(oauth_token, oauth_token_secret)
#         api = tweepy.API(auth)
#         twitter_user = api.get_user(screen_name=screen_name)
#         user = User()
#         user.id = twitter_user.id
#         user.screen_name = twitter_user.screen_name
#         user.blocked = 'N'
#         user.name = twitter_user.name
#         user.description = twitter_user.description
#         user.created_at = twitter_user.created_at
#         user.friends_count = twitter_user.friends_count
#         user.followers_count = twitter_user.followers_count
#         user.statuses_count = twitter_user.statuses_count
#         user.profile_image_url = twitter_user.profile_image_url
#         user.lang = twitter_user.lang
#         user.location = twitter_user.location
#         user.oauth_token = oauth_token
#         user.oauth_token_secret = oauth_token_secret
#         User.add(user)
#     else:
#         user.oauth_token = oauth_token
#         user.oauth_token_secret = oauth_token_secret

    session['screen_name'] = username
    session['oauth_token'] = oauth_token
    session['oauth_token_secret'] = oauth_secret

    return redirect(next_url)
