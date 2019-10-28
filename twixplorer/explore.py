import pandas as pd
from flask import Response

import bz2
from datetime import datetime
import uuid

pd.set_option('display.max_colwidth', -1)

DEFAULT_LIMIT = 20

ALL_FIELDS = (
    'id', 'timestamp', 'created_at', 'author', 'author_id', 'hashtags', 'is_rt', 
    'rt_author', 'rt_author_id', 'rt_timestamp',
    'in_reply_to_status_id', 'in_reply_to_user_id', 'in_reply_to_screen_name',
    'geo', 'text',
)

DEFAULT_FIELDS = (
    'id', 'timestamp', 'author', 'rt_author', 'text',
)

def mongodb_query(twitter_query):
    return { "query": twitter_query, "status.limit" : { "$exists" : False } }

def find_queries(store):
    queries = set()
    results = True
    while results:
        results = list(store.twitter_collection.find(mongodb_query({"$nin": list(queries)})).limit(10))
        for result in results:
            queries.add(result["query"])
    return queries

def count_query(store, query):    
    return store.twitter_collection.find(mongodb_query(query)).count()

def iterate_query(store, query, limit=DEFAULT_LIMIT, fields=DEFAULT_FIELDS):
    mongo_search = store.twitter_collection.find(mongodb_query(query))
    if limit:
        mongo_search = mongo_search.limit(limit)
    for t in mongo_search:
        yield [find_field(t['status'], field) for field in fields]

def find_field(t, field):
    if field == 'timestamp':
        return int(datetime.strptime(t['created_at'], '%a %b %d %H:%M:%S %z %Y').timestamp())
    if field == 'text':
        return t['extended_tweet']['full_text'] if 'extended_tweet' in t else t['text']
    if field == 'author':
        return t['user']['screen_name']
    if field == 'author_id':
        return t['user']['id']
    if field == 'hashtags':
        return [ht['text'] for ht in t['entities']['hashtags']]
    if field == 'is_rt':
        return t.get('retweeted_status') is not None
    if field.startswith("in_reply_to") and field.endswith("id"):
        return t[field] or -1 # -1 so that pandas won't convert ids to float
    if field[:3] == 'rt_':
        retweet = t.get('retweeted_status')
        if retweet:
            return find_field(retweet, field[3:])
        else:
            return -1 # -1 so that pandas won't convert ids to float
    return t[field]

def explore_query(store, query, fields=DEFAULT_FIELDS, limit=DEFAULT_LIMIT, **kwargs):
    if fields is None:
        fields = DEFAULT_FIELDS
    count = count_query(store, query)
    sample_df = pd.DataFrame(iterate_query(store, query, fields=fields, limit=limit, **kwargs), columns=fields)
    sample_table = sample_df.to_html(index=False)
    sample_table = sample_table[sample_table.index("<thead"):]
    sample_table = sample_table[:sample_table.index("</table")]
    return {
        "limit": limit,
        "showing": min(limit, count),
        "fields": fields,
        "fields_str": ', '.join(fields),
        "ALL_FIELDS": ALL_FIELDS,
        "missing_fields_string": ', '.join([f for f in ALL_FIELDS if f not in fields]),
        "count": count,
        "query": query,
        "sample_table": sample_table,
        "uid": uuid.uuid4()
    }

def normalize_field(f):
    if isinstance(f, str):
        return str(f).encode().replace(b',', b' ').replace(b'\n', b' ').replace(b'\r', b' ')
    if isinstance(f, (list, tuple)):
        return b' '.join([e.encode() for e in f]) if f else b''
    return str(f).encode()
    
id2progress = dict()
id2total = dict()

def generate_zip_file(store, query, uid, fields=DEFAULT_FIELDS):
    zipper = bz2.BZ2Compressor()
    header = b','.join(field_name.encode() for field_name in fields) + b'\n'
    id2progress[uid] = 0
    yield zipper.compress(header)
    for row in iterate_query(store, query, fields=fields, limit=None):
        byte_string = b','.join([normalize_field(f) for f in row]) + b'\n'
        id2progress[uid] += 1
        yield zipper.compress(byte_string)
    yield zipper.flush()

def download_query(store, query, fields=DEFAULT_FIELDS, uid=None):
    id2total[uid] = count_query(store, query)
    response = Response(generate_zip_file(store, query, uid, fields=fields),
                    mimetype='application/x-bzip2')
    response.headers["Content-Disposition"] = "attachment; filename=twexplorer.csv.bz2"
    return response
    
def track_download(uid=None):
    if uid in id2progress and uid in id2total:
        return f"{id2progress[uid]}/{id2total[uid]}"
    else:
        return "Wait..."
