# coding: utf-8
#
#  Copyright (C) 2012 André Panisson
#  You can contact me by email (panisson@gmail.com) or write to:
#  Via Alassio 11/c - 10126 Torino - Italy
#
import pymongo

class PyMongoDataStore(object):

    def __init__(self, mongodb_url):
        client = pymongo.MongoClient(mongodb_url)
        db = client.twixplorer
        twitter_collection = db.twitter

    def find(self, query):
        query_result = twitter_collection.find({'query': c.query})
        nr_tweets = query_result.count()
        tweets = query_result.sort('$natural', -1).limit(20)
        return nr_tweets, tweets

    def insert(self, obj):
        twitter_collection.insert(obj)

class NullDataStore(object):

    def __init__(self):
        pass

    def insert(self, obj):
        print obj['status']['text']

    def find(self, query):
        return 0, []
