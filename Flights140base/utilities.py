"""utilities.py - Contains general utilities for Flights140"""
import dateutil.parser
from unidecode import unidecode
from django.utils.encoding import smart_unicode
from twilio.rest.lookups import TwilioLookupsClient
import requests
import os

def encode(words):
    """This method expects raw unicode to be passed in.  Smart unicode converts accents and diacritic marks to bytestrings.  Unidecode does its best to convert bytestrings to their 26 character alphabetic equivalent.

    It is smart to handle the encoding of things from the outside world the same way every time."""
    return unidecode(smart_unicode(words))

def twitter_created_at_to_python(twitter_created_at):
    """This method expects a string like 'Thu Nov 10 15:20:32 +0000 2016', which is how the dates are formatted on twitter, and converts it to a python UTC string"""
    return dateutil.parser.parse(twitter_created_at).\
                                     replace(tzinfo=dateutil.tz.tzutc())

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def twilio_validate(value):
    """Uses twilio api to verify phone number is valid syntax and is a real number"""
    ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
    AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
    client = TwilioLookupsClient(ACCOUNT_SID, AUTH_TOKEN)
    try:
        number = client.phone_numbers.get(value)
    except:
        return '{} is not a valid phone number'.format(value)


def mailgun_validate(value):
    """Uses mailgun api to verify if an email is valid syntax and also does some degree of validating.  It is not perfect though"""
    MAILGUN_PUBLIC_API_KEY = os.environ['MAILGUN_PUBLIC_API_KEY']
    request = requests.get(
        "https://api.mailgun.net/v3/address/validate",
        auth=("api", MAILGUN_PUBLIC_API_KEY),
        params={"address": value})
    if not request.json().get("is_valid"):
        return '{} is not a valid email'.format(value)
