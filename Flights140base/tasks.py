"""tasks.py - This file contains code called by celery beat and code meant to operate on celery queues."""

from __future__ import absolute_import
from celery import shared_task
from twilio.rest import TwilioRestClient
import twitter
from django.core import mail
from collections import namedtuple
import os
import logging

from .models import TwitterAccount, UserProfile, Tweet, Alert
from .parse import parse_tweet
from .utilities import twitter_created_at_to_python, encode, chunks

# Logging is controlled by papertrail on heroku, so it doesn't need any other type of invocation other than this
logging.basicConfig(level=logging.WARNING)

@shared_task
def get_tweets():
    """This method is called by the celery beat scheduler every minute.  It uses the twitter APIs to check a particular list's timeline for the latest tweets, and calls tweet_parser for each of the tweets to actually do the parsing. """

    logging.warning("Celery beat check in")
    # There must be tweets in the database for this to work - otherwise it will crash
    last_tweet_id = Tweet.objects.latest().tweet_id
    # It's okay to re-initialize the twitter API every minute, it won't come close to reaching the rate limit
    api = twitter.Api(
        consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
        consumer_secret=os.environ['TWITTER_CONSUMER_SECRET'],
        access_token_key=os.environ['TWITTER_ACCESS_TOKEN_KEY'],
        access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET'])
    tweets = api.GetListTimeline(
        list_id=os.environ['TWITTER_LIST_ID'],
        since_id=last_tweet_id,
        count=10,
        include_rts=False)

    if tweets:
        for tweet in tweets:
            raw_tweet_dict = {
                "account_id":         tweet.user.id,
                "tweet_text":         tweet.text,
                "tweet_id":           tweet.id,
                "created_at":         tweet.created_at}
            tweet_parser.apply_async(
                args=[raw_tweet_dict],
                queue='tweetparser')

@shared_task
def tweet_parser(raw_tweet_dict):
    """Takes in one tweet_dict from get_tweets and parses the tweet.  The tweet then gets saved, and if keywords are found in the tweet, it will call break_up_alerts to start matching alerts to the tweet"""

    tweet_text = raw_tweet_dict.get("tweet_text")
    tweet_id = raw_tweet_dict.get("tweet_id")

    twitter_account = TwitterAccount.objects.get(\
        user_id=raw_tweet_dict.get("account_id"))
    timestamp = twitter_created_at_to_python(raw_tweet_dict.get("created_at"))

    tweet_parsed_results = parse_tweet(tweet_text)
    # Need to encode the raw tweet text in unicode that python can handle before sending it to a different queue
    encoded_tweet = encode(tweet_text)
    if tweet_parsed_results:
        from_keywords = tweet_parsed_results.get('from')
        to_keywords = tweet_parsed_results.get('to')
        # It's okay to save the raw tweet to the database, Django can handle foreign unicode characters
        new_tweet = Tweet(
            account=twitter_account,
            tweet_id=tweet_id,
            tweet=tweet_text,
            from_keywords=from_keywords,
            to_keywords=to_keywords,
            timestamp=timestamp)
        new_tweet.save()
        processed_tweet_dict = {
            "tweet":               encoded_tweet,
            "tweet_from_keywords": from_keywords,
            "tweet_to_keywords":   to_keywords}
        logging.warning("PARSED")
        logging.warning(encoded_tweet)
        logging.warning("FROM: "+str(from_keywords)+"   TO: "+str(to_keywords))
        break_up_alerts(processed_tweet_dict)
    else:
        # Even if tweet isn't parsed, still save it to the database, so that then next time "Tweet.objects.latest().tweet_id" is executed, it will still return a tweet that wasn't parsed.  This prevents tweets from being retrieved from get_tweets multiple times.
        new_tweet = Tweet(
            account=twitter_account,
            tweet_id=tweet_id,
            tweet=tweet_text,
            from_keywords=[],
            to_keywords=[],
            timestamp=timestamp,
            parsed=False)
        new_tweet.save()
        logging.warning("NOT PARSED")
        logging.warning(encoded_tweet)
    return

@shared_task
def break_up_alerts(processed_tweet_dict):
    """Sets partitions on total alerts in the database and calls match_tweet_to_alerts for each partition, so that match_tweet_to_alerts doesn't have to operate on all the database's alerts at once.  This method breaks up the task into manageable chunks"""

    alerts_count = Alert.objects.count()
    alert_chunk_size = 200
    for from_alert in range(0, alerts_count, alert_chunk_size):
        to_alert = from_alert + alert_chunk_size
        match_tweet_to_alerts.apply_async(
            args=[processed_tweet_dict, from_alert, to_alert],
            queue='alert')

@shared_task
def match_tweet_to_alerts(processed_tweet_dict, from_alert, to_alert):
    """Checks if any keywords in a tweet are in a particular chunk of alerts, and if so, sends an email/text to the user who created the alert."""

    tweet_from_keywords = processed_tweet_dict["tweet_from_keywords"]
    tweet_to_keywords = processed_tweet_dict["tweet_to_keywords"]
    tweet = processed_tweet_dict["tweet"]

    logging.warning("from_alert: "+str(from_alert)+" to_alert: "+str(to_alert))
    logging.warning(tweet)

    alerts_chunk = Alert.objects.order_by('-timestamp')[from_alert:to_alert]
    matched_alerts = []
    for alert in alerts_chunk:
        alert_from_place = alert.from_where()
        alert_from_keywords = alert_from_place.searchable_keywords()

        from_keyword_match = [match for match in tweet_from_keywords \
                              if match in alert_from_keywords]
        # First check if from keywords match. Might not to check to keywords if alert doesn't have to keywords
        if from_keyword_match:
            alert_to_place = alert.to_where()
            if not alert_to_place:
                matched_alerts.append({
                    "email":            alert.user.email,
                    "phone_number":     alert.user.phone_number,
                    "alert_from_place": alert_from_place.name,
                    "alert_to_place":   "anywhere"})
            else:
                alert_to_keywords = alert_to_place.searchable_keywords()
                to_keywords_match = [match for match in tweet_to_keywords \
                                     if match in alert_to_keywords]
                if to_keywords_match:
                    matched_alerts.append({
                        "email":            alert.user.email,
                        "phone_number":     alert.user.phone_number,
                        "alert_from_place": alert_from_place.name,
                        "alert_to_place":   alert_to_place.name})

    if matched_alerts:
        emails = []
        texts = []
        subject = "Flights140"
        text_tuple = namedtuple('text_tuple', ['to_phone_number', 'body'])

        for alert in matched_alerts:
            body = """Courtesy of Flights140.com \n
alert: {} to {} \n
tweet: {}""".format(alert["alert_from_place"], alert["alert_to_place"], tweet)

            to_phone_number = alert['phone_number']
            to_email = alert['email']
            if to_phone_number:
                texts.append(text_tuple(to_phone_number, body))
            if to_email:
                emails.append((subject, body, os.environ['FROM_EMAIL'],
                               [to_email]))
        if emails:
            # https://pypi.python.org/pypi/django-celery-email
            emails = tuple(emails)
            mail.send_mass_mail(emails)
        if texts:
            # If there are texts to send out, only initialize the twilio client once, and send each text across the wire separately
            from_phone_number = os.environ['TWILIO_FROM_NUMBER']
            ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
            AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
            twilio_client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
            for text in texts:
                twilio_client.messages.create(\
                    to=text.to_phone_number, from_=from_phone_number,\
                    body=text.body)
