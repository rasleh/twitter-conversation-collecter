
-------------
HOW TO RUN IT
-------------

Credentials for the Twitter API must be specified in a file named Twitter.ini, with the format:

```
[Twitter]
consumer_key = 
consumer_secret = 
access_key = 
access_secret = 
```

Once you have the ID of the tweet that you want to get the conversation for, you execute the retrieve_conversation_thread command of the get.thread.py file, using the parameters ('user id', 'tweet id')

Files are UTF-16 encoded, and data is saved in the format:
dd-mm-yy.json
dd being the date of the data load, mm the month and yy the year. 