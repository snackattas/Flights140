"""prodTests.py - This is a module for unit testing the production database.  It's necesary to test with the prod database because much of the functionality of Flights140 is dependent on the data in the models that refer to places like Region,  Subregion, etc.  Simply run `python manage.py prodTests` in the root directory to run all the tests in this module"""
# http://stackoverflow.com/questions/5360833/how-to-run-multiple-classes-in-single-test-suite-in-python-unit-testing
# http://stackoverflow.com/questions/1646468/how-to-run-django-unit-tests-on-production-database

import os
import twitter
import unittest
from django.core.management.base import BaseCommand
from Flights140base.parse import remove_airline, parse_tweet


class Command(BaseCommand):
    help = """
    If you need Arguments, please check other modules in
    django/core/management/commands.
    """

    def handle(self, **options):
        test_classes_to_run = [ExcludeAirlineTestCase, ParseTweetTestCase]
        loader = unittest.TestLoader()
        suites_list = []

        for test_class in test_classes_to_run:
                suite = loader.loadTestsFromTestCase(test_class)
                suites_list.append(suite)

        big_suite = unittest.TestSuite(suites_list)
        runner = unittest.TextTestRunner()
        results = runner.run(big_suite)



class ExcludeAirlineTestCase(unittest.TestCase):
    def test_exclude_airline_spaces(self):
        base_tweet = u'#Airfare Deal: [AA] Detroit - Dallas by {} (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        airline = "Air Asia"
        tweet = base_tweet.format(airline)
        result = tweet.replace(airline, "")
        self.assertEqual(exclude_airline(tweet), result)

    def test_exclude_airline_no_spaces(self):
        base_tweet = u'#Airfare Deal: [AA] Detroit - Dallas by {} (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        airline = "AirAsia"
        tweet = base_tweet.format(airline)
        result = tweet.replace(airline, "")
        self.assertEqual(exclude_airline(tweet), result)

    def test_exclude_airline_caps(self):
        base_tweet = u'#Airfare Deal: [AA] Detroit - Dallas by {} (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        airline = "AIRASIA"
        tweet = base_tweet.format(airline)
        result = tweet.replace(airline, "")
        self.assertEqual(exclude_airline(tweet), result)

    def test_exclude_airline_two_airlines_same(self):
        base_tweet = u'#Airfare Deal: [AA] Detroit - Dallas by {}/{} (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        airline = "China Air"
        tweet = base_tweet.format(airline, airline)
        result =  base_tweet.format("", "")
        self.assertEqual(exclude_airline(tweet), result)

    def test_exclude_airline_two_airlines_different(self):
        base_tweet = u'#Airfare Deal: [AA] Detroit - Dallas by {}/{} (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        airline = "China Air"
        airline2 = "US Airway"
        tweet = base_tweet.format(airline, airline2)
        result = tweet.replace(airline, "")
        result = result.replace(airline2, "")
        self.assertEqual(exclude_airline(tweet), result)

    def test_exclude_airline_no_airline(self):
        tweet = u'#Airfare Deal: [AA] Detroit - Dallas by Air (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        self.assertEqual(exclude_airline(tweet), tweet)

    def test_exclude_airline_front(self):
        tweet = u'AirFrance: Detroit - Dallas (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        result = u': Detroit - Dallas (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        self.assertEqual(exclude_airline(tweet), result)

    def test_exclude_airline_back(self):
        tweet = u'Detroit - Dallas (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel Air France'
        result = u'Detroit - Dallas (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel '
        self.assertEqual(exclude_airline(tweet), result)

    def test_exclude_airline_hash(self):
        tweet = u'Detroit - Dallas #AirFrance (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        result =  u'Detroit - Dallas # (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        self.assertEqual(exclude_airline(tweet), result)

    def test_exclude_airline_at_symbol(self):
        tweet = u'Detroit - Dallas @AirFrance (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        result =  u'Detroit - Dallas @ (and vice versa) $116 r/t. Details: https://t.co/0IrlMBUy7O #travel'
        self.assertEqual(exclude_airline(tweet), result)

class ParseTweetTestCase(unittest.TestCase):
    def test_with_real_tweets(self):
        api = twitter.Api(
            consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
            consumer_secret=os.environ['TWITTER_CONSUMER_SECRET'],
            access_token_key=os.environ['TWITTER_ACCESS_TOKEN_KEY'],
            access_token_secret=os.environ['TWITTER_ACCESS_TOKEN_SECRET'])
        tweets = api.GetListTimeline(
            list_id=os.environ['TWITTER_LIST_ID'],
            max_id=789875287827906560,
            count=15,
            include_rts=False)
        parse_results = []
        for tweet in tweets:
            parse_results.append(parse_tweet(tweet.text))
        result = [None,
            {'from': [u'Phoenix', u'Portland'],
                'to': [u'Phoenix', u'Portland']},
            {'from': [u'Washington'],
                'to': [u'Trinidad(\\s?and\\s?|\\s?&\\s?|\\s?&amp;\\s?)Tobago',
                u'Port(-?|\\s)of(-?|\\s)Spain']},
            None,
            None,
            {'from': [u'Chicago', u'(Ft.?\\?|Fort)\\s?Lauderdale'],
                'to': [u'Chicago', u'(Ft.?\\?|Fort)\\s?Lauderdale']},
            None,
            None,
            None,
            None,
            {'from': [u'FLL', u'Orlando', u'New\\s?York', u'Miami'],
                'to': [u'Havana', u'Cuba']},
            {'from': [u'Miami', u'Dallas'], 'to': [u'Nairobi', u'Kenya']},
            {'from': [u'Houston'], 'to': [u'Miami']},
            None,
            {'from': [u'Miami', u'Dallas'], 'to': [u'Nairobi', u'Kenya']}]
        self.assertEqual(parse_results, result)

    def test_parse_tweet_from_to(self):
        tweet = u"#Airfare Deal: [AA] from Detroit to Dallas for $116 r/t. Details: https://t.co/0IrlMBUy7O #travel"
        result = {'from': [u'Detroit'], 'to': [u'Dallas']}
        self.assertEqual(parse_tweet(tweet), result)

    def test_parse_tweet_to_from(self):
        tweet = u"#Airfare Deal: [AA] to Greenland from Dallas or Cincinnati for $116 r/t. Details: https://t.co/0IrlMBUy7O #travel"
        result = {'from': [u'Dallas', u'Cincinnati'], 'to': [u'Greenland']}
        self.assertEqual(parse_tweet(tweet), result)
