# coding: utf-8
#
#  Copyright (C) 2012 André Panisson
#  You can contact me by email (panisson@gmail.com) or write to:
#  Via Alassio 11/c - 10126 Torino - Italy
#

class PyMongoDataStore(object):

    def __init__(self, mongodb_url):
        import pymongo
        client = pymongo.MongoClient(mongodb_url)
        db = client.twixplorer
        self.twitter_collection = db.twitter

    def find(self, query):
        query_result = self.twitter_collection.find(query)
        nr_tweets = query_result.count()
        tweets = query_result.sort('$natural', -1).limit(20)
        return nr_tweets, tweets

    def insert(self, obj):
        self.twitter_collection.insert(obj)

import json
f = open('out.json', 'tw')

class NullDataStore(object):

    def __init__(self):
        pass

    def insert(self, obj):

        f.write(json.dumps(obj) + "\n")

        print(obj['status']['text'])
        if 'extended_tweet' in obj['status']:
            print(obj['status']['extended_tweet']['full_text'])
        print(obj['status']['truncated'])
        print()

    def find(self, query):
        return 0, []
