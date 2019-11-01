import os
from collections import deque
import json
from datetime import date
import configparser
import tweepy


# TODO: Implement "update_conversation" method which, given a root node id, checks for new tweets in convo, and adds
#  them to the corresponding line in the dataset
# TODO: Implement "update all conversations in db" method which looks through DB file, and checks for new tweets
#  in conversation
# TODO: Create method (separate file?) which looks through database, checks submission date of source tweets, and
#  moves them to "closed" database file, if they are older than x (30 days?), so they wont be looked through when
#  updating conversation trees
# Performs authentication necessary to access the Twitter API, using the credentials given in twitter.ini
def authenticate():
    config = configparser.ConfigParser()
    config.read('twitter.ini')

    consumer_key = config.get('Twitter', 'consumer_key')
    consumer_secret = config.get('Twitter', 'consumer_secret')
    access_key = config.get('Twitter', 'access_key')
    access_secret = config.get('Twitter', 'access_secret')

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    return tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def navigate_to_source(tweet_id, username):
    parent = api.get_status(tweet_id)._json['in_reply_to_status_id_str']
    while parent:
        print('Given tweet is not a root node - navigating to root node\n')
        tweet_id = parent
        tweet_data = api.get_status(tweet_id)._json
        parent = tweet_data['in_reply_to_status_id_str']
        username = tweet_data['user']['name']
    return tweet_id, username


def add_sdqc_placeholders(tweet_item):
    tweet_item['SourceSDQC'] = "Underspecified"
    tweet_item['SDQC_Parent'] = "Underspecified"
    tweet_item['SDQC_Submission'] = "Underspecified"


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

# TODO: Remove the overwrite stuff, write it into the two primary methods as updates to a json object -> Update the
#  "Children" array with any new posts. Should be easy
def write_to_file(source_tweet_id):
    exists = os.path.isfile(os.path.join('data/tweet_data.txt'))
    in_db = False
    if exists:
        # Check whether a line already exists for the source tweet. If so, save data of db to array and overwrite line
        with open('data/tweet_data.txt', 'r') as db_file:
            data = db_file.readlines()
        for i in range(len(data)):
            if data[i].split('\t')[0] == source_tweet_id:
                in_db = True
                data[i] = source_tweet_id + '\t' + json.dump(collected_tweets, db_file)

    # Write data back into db file, with line containing source tweet conversation altered
    if in_db:
        with open('data/tweet_data.txt', 'w') as db_file:
            for line in data:
                db_file.write(line)

    # Append line containing source tweet conversation to end of file
    else:
        with open('data/tweet_data.txt', 'a') as db_file:
            # Write to new line, if file already exists
            if exists:
                db_file.write('\n')
            db_file.write(source_tweet_id + '\t')
            json.dump(collected_tweets, db_file)


def retrieve_conversation_thread(tweet_id, username):
    source_tweet_id, source_username = navigate_to_source(tweet_id, username)
    in_db = False
    conv_tree = {}

    # Check that data folder exist, create directory if not
    if not os.path.exists('data'):
        os.makedirs('data')

    # Open data file, check if source_tweet_id is one of the source tweets in DB. If it is, load convo and raise flag
    if os.path.isfile(os.path.join('data/tweet_data.txt')):
        with open('data/tweet_data.txt', 'r') as db:
            for line in db:
                if line.split('\t')[0] == source_tweet_id:
                    in_db = True
                    conv_tree = json.loads(line.split('\t')[1])

    # Collect source tweet, add to collected tweets and fill SDQC-related fields with placeholders
    source_tweet_item = api.get_status(source_tweet_id, tweet_mode='extended')._json
    print("Scraping from source tweet {}\n{}\n\nCollected tweets:"
          .format(source_tweet_id, source_tweet_item['full_text'].replace('\n', ' ')))
    add_sdqc_placeholders(source_tweet_item)
    source_tweet_item['full_text'] = source_tweet_item['full_text'].replace('\n', ' ')
    collected_tweets[str(source_tweet_id)] = source_tweet_item

    # Identify tweets commenting on source
    identify_comments(source_tweet_id, source_username)

    # Iterate over tweets identified in comment section, collect them, and search for deeper comments
    while tweets_of_interest.__len__() != 0:
        item_of_interest = tweets_of_interest.popleft()
        add_sdqc_placeholders(item_of_interest._json)
        item_of_interest._json['full_text'] = item_of_interest._json['full_text'].replace('\n', ' ')
        collected_tweets[item_of_interest.id_str] = item_of_interest._json
        print(item_of_interest.id_str+"\t"+item_of_interest.full_text)
        identify_comments(item_of_interest.id_str, item_of_interest.user.screen_name)

    # Save tweets in JSON format
    write_to_file(source_tweet_id)


tweets_of_interest = deque()
collected_tweets = {}
api = authenticate()

# retrieve_conversation_thread("1168771907036033024", "oestergaard")
retrieve_conversation_thread("1168845054569566208", "JacobUSchultz1")
# retrieve_conversation_thread("1169544969784320000", "Kristianthdahl")
