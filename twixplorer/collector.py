# coding: utf-8
#
#  Copyright (C) 2012 André Panisson
#  You can contact me by email (panisson@gmail.com) or write to:
#  Via Alassio 11/c - 10126 Torino - Italy
#
from flask import request, redirect, url_for, session, Blueprint, \
        render_template, jsonify

import config
import explore

import tweepy
import socket
import json
import threading
import time
import sys
import traceback
import store

import urllib.parse

# setup module
mod = Blueprint("collector", __name__)

@mod.app_template_filter()
def quote(s):
    return urllib.parse.quote(s)

active_collectors = []
datastore = store.PyMongoDataStore(config.MONGODB_URL)

def get_api(request):
    # set up and return a twitter api object
    oauth = tweepy.OAuthHandler(config.CONSUMER_KEY, config.CONSUMER_SECRET)
    access_key = session['oauth_token']
    access_secret = session['oauth_token_secret']
    oauth.set_access_token(access_key, access_secret)
    api = tweepy.API(oauth)
    return api


@mod.route('/main')
def main():
    # app.logger.debug(request.url_rule.endpoint)
    api = get_api(request)
    user = api.me()
    return render_template('main.html', user=user,
                           active_collectors=active_collectors)


@mod.route('/collect')
def collect():
    oauth_token = session['oauth_token']
    oauth_token_secret = session['oauth_token_secret']

    key = [config.CONSUMER_KEY,
           config.CONSUMER_SECRET,
           oauth_token,
           oauth_token_secret]
    query = request.args.get('query', '')

    c = Collector(query, key)
    active_collectors.append(c)
    c.start()
    return redirect(url_for('collector.main'))


@mod.route('/list_jobs')
def list_jobs():
    return render_template('collect.html', active_collectors=active_collectors)


@mod.route('/job')
def job():
    job_id = request.args.get('id', '1')
    c = active_collectors[int(job_id) - 1]
    nr_tweets, tweets =  datastore.find({'query': c.query})
    return render_template('job.html',
                           job=c, tweets=tweets,
                           nr_tweets=nr_tweets)


@mod.route('/stop_job')
def stop_job():
    job_id = request.args.get('id', '1')
    c = active_collectors.pop(int(job_id) - 1)
    c.stop()
    return redirect(url_for('collector.main'))
    

@mod.route('/explore/')
def explore_homepage():
    return render_template('explore.html', queries=explore.find_queries(datastore))
    
def parse_fields(fields_param):
    return [f.strip() for f in fields_param.split(",")] if fields_param else explore.DEFAULT_FIELDS

def get_query_fields():
    assert 'q' in request.args, "Missing query"
    q = urllib.parse.unquote(request.args.get('q').strip("'"))
    fields = parse_fields(request.args.get('fields'))
    return q, fields

@mod.route('/explore/query')
def explore_query():
    q, fields = get_query_fields()
    limit = int(request.args.get('limit', explore.DEFAULT_LIMIT))
    return render_template('query.html', **explore.explore_query(datastore, q, limit=limit, fields=fields))
    
@mod.route('/explore/query/download')
def download_query():
    q, fields = get_query_fields()
    return explore.download_query(datastore, q, fields=fields, uid=request.args.get('uid'))

@mod.route('/explore/query/download/track')
def track_download():
    return jsonify(explore.track_download(uid=request.args.get('uid')))

class StreamingListener(tweepy.StreamListener):

    def __init__(self, collector, *args, **kwargs):
        self.collector = collector
        self.count = 0
        super(StreamingListener, self).__init__(*args, **kwargs)

    def on_data(self, data):

        try:
            status = json.loads(data)
        except Exception as e:
            print(e, repr(data))
            return False

        twitter_obj = {'status':status, 'query':self.collector.query}
        datastore.insert(twitter_obj)

        self.collector.count += 1

    def on_error(self, status_code):
        if status_code == 401:
            raise Exception("Authentication error")

    def on_status(self, status):
        pass


class Collector(threading.Thread):
    def __init__(self, query, key, log=None):
        self.query = query
        self.key = key
        self.log = log
        self.count = 0
        self.active = False
        self.connected = False
        super(Collector, self).__init__()

    def run(self):
        q = self.query.split(",")

        print("Streaming retweets for query '%s'" % q)
        listener = StreamingListener(self)

        consumer_key, consumer_secret, \
            access_token, access_token_secret = self.key

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)

        self.active = True

        while (self.active):
            try:
                self.connected = True
                self.stream = tweepy.streaming.Stream(auth, listener, timeout=60.0)
                self.stream.filter(track=q)
                self.connected = False
                print("Connection dropped:", self.query)
                if self.active:
                    time.sleep(60)
            except socket.gaierror:
                self.connected = False
                print("Stream closed")
                time.sleep(60)
            except Exception:
                self.connected = False
                traceback.print_exc(file=sys.stdout)
                sys.stdout.flush()
                time.sleep(60)

        print("Collector stopped.")

    def stop(self):
        print("Stopping collector: ", self.query)
        self.active = False
        self.stream.disconnect()
