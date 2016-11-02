from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
# Create your models here.
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from twilio.rest.lookups import TwilioLookupsClient
import requests
import os
from django.utils.encoding import python_2_unicode_compatible
from random import randrange
from collections import Counter

def twilio_validate(value, initial=True):
    ACCOUNT_SID="AC7dc7a31d6cb366f25a4af4fa73c6ac48"
    AUTH_TOKEN="45e68885d7ab2755d4e965cf71db47e2"
    client = TwilioLookupsClient(ACCOUNT_SID, AUTH_TOKEN)
    try:
        number = client.phone_numbers.get(value)
    except:
        if initial:
            raise ValidationError(
                '{} is not a valid phone number'.format(value))
        return '{} is not a valid phone number'.format(value)


def mailgun_validate(value, initial=True):
    MAILGUN_PUBLIC_API_KEY = "pubkey-2b308844086ef26cee582ce10ac7303b"
    request = requests.get(
        "https://api.mailgun.net/v3/address/validate",
        auth=("api", MAILGUN_PUBLIC_API_KEY),
        params={"address": value})
    if not request.json().get("is_valid"):
        if initial:
            raise ValidationError(
                '{} is not a valid email'.format(value))
        return '{} is not a valid email'.format(value)

def regexify_chars(word_list):
    new_word_list = []
    for word in word_list:
        replacement_pair = [
            [".", ".?"],
            ["St.? ", "(St.?\?|Saint\?)\s?"],
            ["Fort ", "(Ft.?\?|Fort)\s?"],
            [" and ", "(\s?and\s?|\s?&\s?|\s?&amp;\s?)"],
            ["-","(-?|\s)"],
            ["'","'?"],
            [" ", "\s?"]]
        for pair in replacement_pair:
            if pair[0] in word:
                word = word.replace(pair[0], pair[1])
        new_word_list.append(word)
    return new_word_list

def regexify_abbreviation(abbr_list):
    new_abbr_list = []
    for abbr in abbr_list:
        word_length = len(abbr)
        new_abbr = abbr[0]
        for n in range(1, word_length):
            new_abbr += ".?" + abbr[n]
        new_abbr_list.append(new_abbr)
    return new_abbr_list

def all_keywords(case_sensitive, case_insensitive):
    keywords = []
    regions = Region.objects.all()
    for region in regions:
        keywords.extend(region.searchable_keywords(sort=False))
    keywords.sort()
    keywords.sort(key = lambda s: len(s))
    keywords.reverse()
    return keywords

def case_sensitive_keywords():
    keywords = []
    regions = Region.objects.all()
    for region in regions:
        keywords.extend(region.case_sensitive_keywords())
    keywords.sort()
    keywords.sort(key = lambda s: len(s))
    keywords.reverse()
    return keywords

def case_insensitive_keywords():
    keywords = []
    regions = Region.objects.all()
    for region in regions:
        keywords.extend(region.case_insensitive_keywords())
    keywords.sort()
    keywords.sort(key = lambda s: len(s))
    keywords.reverse()
    return keywords


def encode_place(place):
    encoded_place = place.replace(" ", "+") # this just url-ify's the string
    return encoded_place

def retrieve_place_id(place):
    encoded_place = encode_place(place)

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "key": os.environ["GOOGLE_PLACE_SEARCH_API_KEY"],
        "query": encoded_place}
    response = requests.get(url, params).json()
    try:
        photo_details = response.get("results")[0].get("photos")[0]
        photo_reference = photo_details.get("photo_reference")
        if photo_reference:
            place_id = response.get("results")[0].get("place_id")
    except:
        try:
            lat_long_pairs = []
            geometry = response.get("results")[0].get("geometry")
            location = geometry.get("location")
            viewport_northeast = geometry.get("viewport").get("northeast")
            viewport_southwest = geometry.get("viewport").get("southwest")
            for pair in [location, viewport_northeast, viewport_southwest]:
                lat_long_pairs.append("{},{}".format(
                    str(pair.get("lat")), str(pair.get("lng"))))
            return retrieve_place_id_by_location(
                place, lat_long_pairs)
        except:
            place_id = None
    return place_id


def retrieve_place_id_by_location(place, lat_long_pairs):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "key": os.environ["GOOGLE_PLACE_SEARCH_API_KEY"],
        "radius": 50000,
        "keywords": encode_place(place)}
    for pair in lat_long_pairs:
        params["location"] = pair
        response = requests.get(url, params).json()
        try:
            photo_details = response.get("results")[0].get("photos")[0]
            photo_reference = photo_details.get("photo_reference")
            if photo_reference:
                place_id = response.get("results")[0].get("place_id")
                return place_id
        except:
            pass
    place_id = None
    return place_id

def retrieve_photo_reference(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "key": os.environ["GOOGLE_PLACE_SEARCH_API_KEY"],
        "placeid": place_id}
    response = requests.get(url, params).json()
    try:
        photo_details = response.get("result").get("photos")[0]
        photo_reference = photo_details.get("photo_reference")
        return photo_reference
    except:
        return None

def retrieve_photo_url(photo_reference):
    url = "https://maps.googleapis.com/maps/api/place/photo"
    params = {
        "key": os.environ["GOOGLE_PLACE_SEARCH_API_KEY"],
        "photoreference": photo_reference,
        "maxheight": 50,
        "maxwidth": 50}
    response = requests.get(url, params)
    try:
        return response.url
    except:
        random_img =\
            "/static/Flights140base/image/randompics/{}.jpg".\
            format(randrange(1,11))
        return random_img


class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    phone_number = models.CharField(
        validators=[twilio_validate], blank=True, null=True,
        max_length=16)
    email = models.EmailField(
        validators=[mailgun_validate], null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name()

class TwitterAccount(models.Model):
    user_id = models.CharField(primary_key=True, max_length=50)
    full_name = models.CharField(max_length=50)
    screen_name = models.CharField(max_length=50)

    def __str__(self):
        return self.full_name

    class Meta:
        get_latest_by = 'full_name'


@python_2_unicode_compatible
class Tweet(models.Model):
    account = models.ForeignKey(TwitterAccount, on_delete=models.DO_NOTHING, null=False)
    tweet_id = models.BigIntegerField(primary_key=True, unique=True, null=False)
    tweet = models.CharField(max_length=160)
    from_keywords = JSONField(null=False)
    to_keywords = JSONField(null=False)
    timestamp = models.DateTimeField(null=False)
    parsed = models.BooleanField(default=True, null=False)
    def __str__(self):
        return self.tweet

    class Meta:
        get_latest_by = 'tweet_id'

class ContactMessage(models.Model):
    user = models.ForeignKey(UserProfile, null=True, blank=True,
                             on_delete=models.SET_NULL)
    message = models.CharField(max_length=5000)

@python_2_unicode_compatible
class Region(models.Model):
    name = models.CharField(max_length=100, null=False)
    plural_names = JSONField(default=[], null=True, blank=True)
    additional_keywords = JSONField(default=[], null=True, blank=True)
    abbreviations = JSONField(default=[], null=True, blank=True)
    place_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    def create_place_id(cls):
        return retrieve_place_id(cls.name)

    # def searchable_keywords(cls, sort=True):
    #     keywords = []
    #     keywords.append(cls.name)
    #     keywords.extend(cls.plural_names)
    #     keywords.extend(cls.additional_keywords)
    #     if cls.abbreviations:
    #         keywords.extend(regexify_abbreviation(cls.abbreviations))
    #     keywords = regexify_chars(keywords)
    #     # Check if this city only has 1 country, if so, add the country keywords
    #     countries = Country.objects.filter(region=cls)
    #     subregions = Subregion.objects.filter(region=cls)
    #     for country in countries:
    #         keywords.extend(country.searchable_keywords(sort=False))
    #     for subregion in subregions:
    #         keywords.extend(subregion.searchable_keywords(
    #             derivative_keywords=False, sort=False))
    #     if sort:
    #         keywords.sort()
    #         keywords.reverse()
    #     return keywords

    def searchable_keywords(cls, derivative_keywords=True, sort=True):
        keywords = []
        keywords.extend(cls.case_sensitive_keywords(derivative_keywords))
        keywords.extend(cls.case_insensitive_keywords(derivative_keywords))
        if sort:
            keywords.sort()
            keywords.reverse()
        return keywords

    def case_sensitive_keywords(cls, derivative_keywords=True):
        keywords = []
        keywords.extend(regexify_abbreviation(cls.abbreviations))
        if derivative_keywords:
            countries = Country.objects.filter(region=cls)
            subregions = Subregion.objects.filter(region=cls)

            for country in countries:
                keywords.extend(country.case_sensitive_keywords())
            for subregion in subregions:
                keywords.extend(
                    subregion.case_sensitive_keywords(
                    derivative_keywords=False))
        return keywords

    def case_insensitive_keywords(cls, derivative_keywords=True):
        keywords = []
        keywords.append(cls.name)
        keywords.extend(cls.plural_names)
        keywords.extend(cls.additional_keywords)
        keywords = regexify_chars(keywords)

        if derivative_keywords:
            countries = Country.objects.filter(region=cls)
            subregions = Subregion.objects.filter(region=cls)

            for country in countries:
                keywords.extend(country.case_insensitive_keywords())
            for subregion in subregions:
                keywords.extend(
                    subregion.case_insensitive_keywords(
                    derivative_keywords=False))
        return keywords


@python_2_unicode_compatible
class Subregion(models.Model):
    region = models.ForeignKey(Region, null=False, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100, null=False)
    plural_names = JSONField(default=[], null=True, blank=True)
    additional_keywords = JSONField(default=[], null=True, blank=True)
    abbreviations = JSONField(default=[], null=True, blank=True)
    place_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    def create_place_id(cls):
        return retrieve_place_id(cls.name)

    # def searchable_keywords(cls, derivative_keywords=True, sort=True):
    #     keywords = []
    #     keywords.append(cls.name)
    #     keywords.extend(cls.plural_names)
    #     keywords.extend(cls.additional_keywords)
    #     if cls.abbreviations:
    #         keywords.extend(regexify_abbreviation(cls.abbreviations))
    #     keywords = regexify_chars(keywords)
    #     # Check if this city only has 1 country, if so, add the country keywords
    #     if derivative_keywords:
    #         countries = Country.objects.filter(subregion=cls)
    #         for country in countries:
    #             keywords.extend(country.searchable_keywords(sort=False))
    #     if sort:
    #         keywords.sort()
    #         keywords.reverse()
    #     return keywords

    def searchable_keywords(cls, derivative_keywords=True, sort=True):
        keywords = []
        keywords.extend(cls.case_sensitive_keywords(derivative_keywords))
        keywords.extend(cls.case_insensitive_keywords(derivative_keywords))
        if sort:
            keywords.sort()
            keywords.sort(key = lambda s: len(s))
            keywords.reverse()
        return keywords


    def case_sensitive_keywords(cls, derivative_keywords=True):
        keywords = []
        keywords.extend(regexify_abbreviation(cls.abbreviations))
        if derivative_keywords:
            countries = Country.objects.filter(subregion=cls)
            for country in countries:
                keywords.extend(country.case_sensitive_keywords())
        return keywords

    def case_insensitive_keywords(cls, derivative_keywords=True):
        keywords = []
        keywords.append(cls.name)
        keywords.extend(cls.plural_names)
        keywords.extend(cls.additional_keywords)
        keywords = regexify_chars(keywords)

        if derivative_keywords:
            countries = Country.objects.filter(subregion=cls)
            for country in countries:
                keywords.extend(country.case_insensitive_keywords())
        return keywords


@python_2_unicode_compatible
class Country(models.Model):
    region = models.ForeignKey(Region, null=False, on_delete=models.DO_NOTHING)
    subregion = models.ForeignKey(Subregion, null=True, blank=True,
                                  on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100, null=False)
    plural_names = JSONField(default=[], null=True, blank=True)
    additional_keywords = JSONField(default=[], null=True, blank=True)
    abbreviations = JSONField(default=[], null=True, blank=True)
    place_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    def create_place_id(cls):
        return retrieve_place_id(cls.name)

    # def searchable_keywords(cls, sort=True):
    #     keywords = []
    #     keywords.append(cls.name)
    #     keywords.extend(cls.plural_names)
    #     keywords.extend(cls.additional_keywords)
    #     if cls.abbreviations:
    #         keywords.extend(regexify_abbreviation(cls.abbreviations))
    #     keywords = regexify_chars(keywords)
    #     # Check if this city only has 1 country, if so, add the country keywords
    #     cities = City.objects.filter(country=cls)
    #     states = State.objects.filter(country=cls)
    #     for city in cities:
    #         keywords.extend(city.searchable_keywords(num_cities_check=False,\
    #                                                  sort=False))
    #     for state in states:
    #         keywords.extend(state.searchable_keywords(derivative_keywords=False,
    #                                                   sort=False))
    #     if sort:
    #         keywords.sort()
    #         keywords.reverse()
    #     return keywords
    def searchable_keywords(cls, derivative_keywords=True, sort=True):
        keywords = []
        keywords.extend(cls.case_sensitive_keywords(derivative_keywords))
        keywords.extend(cls.case_insensitive_keywords(derivative_keywords))
        if sort:
            keywords.sort()
            keywords.sort(key = lambda s: len(s))
            keywords.reverse()
        return keywords

    def case_sensitive_keywords(cls, derivative_keywords=True):
        keywords = []
        keywords.extend(regexify_abbreviation(cls.abbreviations))
        if derivative_keywords:
            cities = City.objects.filter(country=cls)
            states = State.objects.filter(country=cls)

            for city in cities:
                keywords.extend(
                    city.case_sensitive_keywords(num_cities_check=False))
            for state in states:
                keywords.extend(
                    state.case_sensitive_keywords(derivative_keywords=False))
        return keywords

    def case_insensitive_keywords(cls, derivative_keywords=True):
        keywords = []
        keywords.append(cls.name)
        keywords.extend(cls.plural_names)
        keywords.extend(cls.additional_keywords)
        keywords = regexify_chars(keywords)

        if derivative_keywords:
            cities = City.objects.filter(country=cls)
            states = State.objects.filter(country=cls)

            for city in cities:
                keywords.extend(
                    city.case_insensitive_keywords(num_cities_check=False))
            for state in states:
                keywords.extend(
                    state.case_insensitive_keywords(derivative_keywords=False))
        return keywords


@python_2_unicode_compatible
class State(models.Model):
    region = models.ForeignKey(Region, null=False, on_delete=models.DO_NOTHING)
    subregion = models.ForeignKey(Subregion, null=True, blank=True,
                                  on_delete=models.DO_NOTHING)
    country = models.ForeignKey(Country, null=False,
                                on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100, null=False)
    plural_names = JSONField(default=[], null=True, blank=True)
    additional_keywords = JSONField(default=[], null=True, blank=True)
    abbreviations = JSONField(default=[], null=True, blank=True)
    place_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    def create_place_id(cls):
        name = cls.name + " " + cls.country.name
        return retrieve_place_id(name)

    def searchable_keywords(cls, derivative_keywords=True, sort=True):
        keywords = []
        keywords.extend(cls.case_sensitive_keywords(derivative_keywords))
        keywords.extend(cls.case_insensitive_keywords(derivative_keywords))
        if sort:
            keywords.sort()
            keywords.sort(key = lambda s: len(s))
            keywords.reverse()
        return keywords

    def case_sensitive_keywords(cls, derivative_keywords=True):
        keywords = []
        keywords.extend(regexify_abbreviation(cls.abbreviations))

        if derivative_keywords:
            cities = City.objects.filter(state=cls)
            for city in cities:
                keywords.extend(city.case_sensitive_keywords(
                    num_cities_check=False))
        return keywords

    def case_insensitive_keywords(cls, derivative_keywords=True):
        keywords = []
        keywords.append(cls.name)
        keywords.extend(cls.plural_names)
        keywords.extend(cls.additional_keywords)
        keywords = regexify_chars(keywords)
        if derivative_keywords:
            cities = City.objects.filter(state=cls)
            for city in cities:
                keywords.extend(city.case_insensitive_keywords(
                    num_cities_check=False))
        return keywords


@python_2_unicode_compatible
class City(models.Model):
    region = models.ForeignKey(Region, null=False, on_delete=models.DO_NOTHING)
    subregion = models.ForeignKey(Subregion, null=True, blank=True,
                                  on_delete=models.DO_NOTHING)
    country = models.ForeignKey(Country, null=False,
                                on_delete=models.DO_NOTHING)
    state = models.ForeignKey(State, null=True, blank=True,
                              on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=100, null=False)
    plural_names = JSONField(default=[], null=True, blank=True)
    additional_keywords = JSONField(default=[], null=True, blank=True)
    abbreviations = JSONField(default=[], null=True, blank=True)
    iata = JSONField(default=[], null=True, blank=True)
    place_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    def create_place_id(cls):
        name = cls.name + " " + cls.country.name
        return retrieve_place_id(name)

    # def searchable_keywords(cls, num_cities_check=True, sort=True):
    #     keywords = []
    #     keywords.append(cls.name)
    #     keywords.extend(cls.plural_names)
    #     keywords.extend(cls.additional_keywords)
    #     if cls.abbreviations:
    #         keywords.extend(regexify_abbreviation(cls.abbreviations))
    #
    #     # Check if this city only has 1 country, if so, add the country keywords
    #     if num_cities_check:
    #         num_cities = City.objects.filter(country=cls.country).count()
    #         if num_cities == 1:
    #             keywords.append(cls.country.name)
    #             keywords.extend(cls.country.plural_names)
    #             keywords.extend(cls.country.additional_keywords)
    #             if cls.country.abbreviations:
    #                 keywords.extend(regexify_abbreviation(
    #                     cls.country.abbreviations))
    #
    #     keywords = regexify_chars(keywords)
    #     keywords.extend(cls.iata)
    #
    #     if sort:
    #         keywords.sort()
    #         keywords.reverse()
    #     return keywords

    def searchable_keywords(cls, num_cities_check=True, sort=True):
        keywords = cls.case_insensitive_keywords(num_cities_check)
        keywords.extend(cls.case_sensitive_keywords(num_cities_check))

        if sort:
            keywords.sort()
            keywords.sort(key = lambda s: len(s))
            keywords.reverse()
        return keywords

    def case_sensitive_keywords(cls, num_cities_check=True):
        keywords = []
        keywords.extend(regexify_abbreviation(cls.abbreviations))

        if num_cities_check:
            num_cities = City.objects.filter(country=cls.country).count()
            if num_cities == 1:
                keywords.extend(
                    regexify_abbreviation(cls.country.abbreviations))

        keywords.extend(cls.iata)
        return keywords

    def case_insensitive_keywords(cls, num_cities_check=True):
        keywords = []
        keywords.append(cls.name)
        keywords.extend(cls.plural_names)
        keywords.extend(cls.additional_keywords)
        if num_cities_check:
            num_cities = City.objects.filter(country=cls.country).count()
            if num_cities == 1:
                keywords.append(cls.country.name)
                keywords.extend(cls.country.plural_names)
                keywords.extend(cls.country.additional_keywords)
        keywords = regexify_chars(keywords)
        return keywords

class Alert(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    from_region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="from_region")
    from_subregion = models.ForeignKey(Subregion, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="from_subregion")
    from_country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="from_country")
    from_state = models.ForeignKey(State, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="from_state")
    from_city = models.ForeignKey(City, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="from_city")


    to_region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="to_region")
    to_subregion = models.ForeignKey(Subregion, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="to_subregion")
    to_country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="to_country")
    to_state = models.ForeignKey(State, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="to_state")
    to_city = models.ForeignKey(City, null=True, blank=True, on_delete=models.DO_NOTHING, related_name="to_city")


    timestamp = models.DateTimeField(auto_now_add=True)

    def from_where(self):
        if self.from_region:
            return self.from_region
        if self.from_subregion:
            return self.from_subregion
        if self.from_country:
            return self.from_country
        if self.from_state:
            return self.from_state
        if self.from_city:
            return self.from_city

    def to_where(self):
        if self.to_region:
            return self.to_region
        if self.to_subregion:
            return self.to_subregion
        if self.to_country:
            return self.to_country
        if self.to_state:
            return self.to_state
        if self.to_city:
            return self.to_city
        return None

    def from_name(self):
        return self.from_where().name

    def to_name(self):
        to_place = self.to_where()
        if to_place:
            return to_place.name
        else:
            return "Anywhere"

    def from_url(self):
        photo_reference = retrieve_photo_reference(self.from_where().place_id)
        if photo_reference:
            return retrieve_photo_url(photo_reference)
        random_img =\
            "/static/Flights140base/image/randompics/{}.jpg".\
            format(randrange(1,11))
        return random_img

    def from_place_id(self):
        return self.from_where().place_id

    def to_place_id(self):
        to_place = self.to_where()
        if to_place:
            return to_place.place_id, True
        random_img =\
            "/static/Flights140base/image/randompics/{}.jpg".\
            format(randrange(1,11))
        return random_img, False

    def to_url(self):
        to_place = self.to_where()
        if to_place:
            photo_reference = retrieve_photo_reference(to_place.place_id)
            if photo_reference:
                return retrieve_photo_url(photo_reference)
        random_img =\
            "/static/Flights140base/image/randompics/{}.jpg".\
            format(randrange(1,11))
        return random_img

    def from_keywords(self):
        return self.from_where().searchable_keywords()

    def to_keywords(self):
        to_place = self.to_where()
        if to_place:
            return to_place.searchable_keywords()
        else:
            return all_keywords()

    def __str__(self):
        alert = "{} to {}".format(self.from_name(), self.to_name())
        return alert
