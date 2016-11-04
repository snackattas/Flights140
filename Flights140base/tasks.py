# http://supervisord.org/running.html#running-supervisorctl

from __future__ import absolute_import
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from twilio.rest import TwilioRestClient
from .models import TwitterAccount, UserProfile, Tweet, Alert
from .parse import parse_tweet
import requests
from .views import twitter_created_at_to_python
import twitter
from unidecode import unidecode
from django.utils.encoding import smart_str, smart_unicode
from unidecode import unidecode
import os
import codecs
from django.core.mail import send_mail
from django.core import mail
import arrow
import datetime
from collections import namedtuple
from celery import shared_task
import logging

logging.basicConfig(level=logging.INFO)

def chunks(array, size):
	"""Yield successive n-sized chunks from l."""
	for i in range(0, len(array), size):
		yield array[i:i + size]

@shared_task
def get_tweets():
    last_tweet_id = Tweet.objects.latest().tweet_id
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

    successfully_parsed_tweets = []
    for (n, tweet) in enumerate(tweets):
        tweet_text = tweet.text
        tweet_id = tweet.id

        twitter_account = TwitterAccount.objects.get(user_id=tweet.user.id)
        timestamp = twitter_created_at_to_python(tweet.created_at)

        tweet_parsed_results = parse_tweet(tweet.text)
        encoded_tweet = unidecode(smart_unicode(tweet_text))
        if tweet_parsed_results:
            from_keywords = tweet_parsed_results.get('from')
            to_keywords = tweet_parsed_results.get('to')
            new_tweet = Tweet(
                account=twitter_account,
                tweet_id=tweet_id,
                tweet=tweet_text,
                from_keywords=from_keywords,
                to_keywords=to_keywords,
                timestamp=timestamp)
            new_tweet.save()
            successfully_parsed_tweets.append({
                "tweet":               encoded_tweet,
                "tweet_from_keywords": from_keywords,
                "tweet_to_keywords":   to_keywords})
            logging.info("PARSED")
            logging.info(encoded_tweet)
            logging.info("FROM: "+str(from_keywords)+"   TO: "+str(to_keywords))
        else:
            new_tweet = Tweet(
                account=twitter_account,
                tweet_id=tweet_id,
                tweet=tweet_text,
                from_keywords=[],
                to_keywords=[],
                timestamp=timestamp,
                parsed=False)
            new_tweet.save()
            logging.info("NOT PARSED")
            logging.info(encoded_tweet)
    tweets_to_alerts_breakup(successfully_parsed_tweets)
    return

@shared_task
def tweets_to_alerts_breakup(parsed_tweets_list):
    total_alerts = Alert.objects.count()
    alert_chunk_size = 200
    chunks = range(0, total_alerts, alert_chunk_size)
    for tweet_dict in parsed_tweets_list:
        for from_alert in range(0, total_alerts, alert_chunk_size):
            to_alert = from_alert + alert_chunk_size
            tump = match_tweet_to_alerts.apply_async(
                args=[tweet_dict, from_alert, to_alert],
                queue='alert')

@shared_task
def match_tweet_to_alerts(tweet_dict, from_alert, to_alert):
    logging.info(tweet_dict)
    logging.info("from_alert: "+str(from_alert)+" to_alert: "+str(to_alert))
    tweet_from_keywords = tweet_dict["tweet_from_keywords"]
    tweet_to_keywords = tweet_dict["tweet_to_keywords"]
    tweet = tweet_dict["tweet"]
    matched_alerts = []
    for alert in Alert.objects.order_by('-timestamp')[from_alert:to_alert]:
        alert_from_place = alert.from_where()
        alert_from_keywords = alert_from_place.searchable_keywords()
        from_keyword_match = [match for match in tweet_from_keywords \
                              if match in alert_from_keywords]

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
            emails = tuple(emails)
            mail.send_mass_mail(emails)
        if texts:
            from_phone_number = os.environ['TWILIO_FROM_NUMBER']
            ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
            AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
            twilio_client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
            for text in texts:
                twilio_client.messages.create(\
                    to=text.to_phone_number, from_=from_phone_number,\
                    body=text.body)
