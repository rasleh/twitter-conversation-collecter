import csv
import os
from collections import deque
import json
from datetime import date

import configparser
import tweepy


def authenticate():
    global api
    config = configparser.ConfigParser()
    config.read('twitter.ini')

    consumer_key = config.get('Twitter', 'consumer_key')
    consumer_secret = config.get('Twitter', 'consumer_secret')
    access_key = config.get('Twitter', 'access_key')
    access_secret = config.get('Twitter', 'access_secret')

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    return tweepy.API(auth)


def identify_comments(tweet_id, username):
    children = []
    # Lookup a given user, extract all recent replies to user, and check if replies are to a specific tweet
    for result in tweepy.Cursor(api.search, q='to:' + username, result_type='recent', timeout=999999, tweet_mode='extended').items():
        if hasattr(result, 'in_reply_to_status_id_str'):
            if result.in_reply_to_status_id_str == tweet_id:
                # Mark tweets for further investigation, and add tweet id to list of comments
                tweets_of_interest.append(result)
                children.append(result.id_str)

    # Add ids for all commenting tweets to json of parent tweet
    collected_tweets[tweet_id]['children'] = children


def write_to_file():
    # Check that folder exist, create directory and file if not
    if not os.path.exists('data'):
        os.makedirs('data')

    filename = date.today().strftime("%d-%m-%y")+'.json'
    with open(os.path.join('data/', filename), 'w') as db_file:
        db_file.write(json.dumps(collected_tweets))


def retrieve_conversation_thread(source_tweet_id, source_username):
    # Collect source tweet
    source_tweet_item = api.get_status(source_tweet_id, tweet_mode='extended')
    collected_tweets[source_tweet_item.id_str] = source_tweet_item.json

    # Identify tweets commenting on source
    identify_comments(source_tweet_id, source_username)

    # Iterate over tweets identified in comment section, collect them, and search for deeper comments
    while tweets_of_interest.__len__() != 0:
        item_of_interest = tweets_of_interest.popleft()
        collected_tweets[item_of_interest.id_str] = item_of_interest.json
        identify_comments(item_of_interest.id_str, item_of_interest.user.screen_name)

    # Save tweets in JSON format
    write_to_file()


tweets_of_interest = deque()
collected_tweets = {}
api = authenticate()

# retrieve_conversation_thread("1168509279978053633", "NLPatITU")
# retrieve_conversation_thread("1168771907036033024", "oestergaard")
#retrieve_conversation_thread("1168845054569566208", "JacobUSchultz1")