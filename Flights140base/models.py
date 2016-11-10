from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.utils.encoding import python_2_unicode_compatible

from .model_helpers import retrieve_photo_reference, retrieve_photo_url,\
    retrieve_random_image, regexify_special_chars, regexify_abbreviation

import os
import requests
from random import randrange
from collections import Counter


class UserProfile(models.Model):
    """Each user has a UserProfile object created automatically from the python social auth User object in the main view.  The UserProfile object is the one that the app interacts with, not the python social auth one.

    userProfiles try to pull the email from the python social auth User object upon creation. UserProfile objects connect to alerts."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(blank=True, null=True, max_length=16)
    email = models.EmailField(null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name()


class TwitterAccount(models.Model):
    """This model contains the twitter accounts that this app pulls its tweets from"""

    user_id = models.CharField(primary_key=True, max_length=50)
    full_name = models.CharField(max_length=50)
    screen_name = models.CharField(max_length=50)

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ['full_name']


@python_2_unicode_compatible
class Tweet(models.Model):
    """Each Tweet and the parsed keywords are stored in this model"""
    account = models.ForeignKey(TwitterAccount, on_delete=models.DO_NOTHING,
                                null=False)
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


@python_2_unicode_compatible
class Region(models.Model):
    name = models.CharField(max_length=100, null=False)
    plural_names = JSONField(default=[], null=True, blank=True)
    additional_keywords = JSONField(default=[], null=True, blank=True)
    abbreviations = JSONField(default=[], null=True, blank=True)
    place_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

    def all_keywords(cls, derivative_keywords=True, sort=True):
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
        keywords = regexify_special_chars(keywords)

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

    def all_keywords(cls, derivative_keywords=True, sort=True):
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
        keywords = regexify_special_chars(keywords)

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


    def all_keywords(cls, derivative_keywords=True, sort=True):
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
        keywords = regexify_special_chars(keywords)

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

    def all_keywords(cls, derivative_keywords=True, sort=True):
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
        keywords = regexify_special_chars(keywords)
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

    def all_keywords(cls, num_cities_check=True, sort=True):
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
        keywords = regexify_special_chars(keywords)
        return keywords



class Alert(models.Model):
    """Alerts store a user's to/from choices.
    Rules:
        -One of the from fields must be specified.  And only one.
        -The to fields are optional. So either one of the to fields is specified, or none are specified"""

    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    from_region = models.ForeignKey(Region, null=True, blank=True,\
        on_delete=models.DO_NOTHING, related_name="from_region")
    from_subregion = models.ForeignKey(Subregion, null=True, blank=True,\
        on_delete=models.DO_NOTHING, related_name="from_subregion")
    from_country = models.ForeignKey(Country, null=True, blank=True,\
        on_delete=models.DO_NOTHING, related_name="from_country")
    from_state = models.ForeignKey(State, null=True, blank=True,\
        on_delete=models.DO_NOTHING, related_name="from_state")
    from_city = models.ForeignKey(City, null=True, blank=True,
        on_delete=models.DO_NOTHING, related_name="from_city")

    to_region = models.ForeignKey(Region, null=True, blank=True,\
        on_delete=models.DO_NOTHING, related_name="to_region")
    to_subregion = models.ForeignKey(Subregion, null=True, blank=True,\
        on_delete=models.DO_NOTHING, related_name="to_subregion")
    to_country = models.ForeignKey(Country, null=True, blank=True,\
        on_delete=models.DO_NOTHING, related_name="to_country")
    to_state = models.ForeignKey(State, null=True, blank=True,\
        on_delete=models.DO_NOTHING, related_name="to_state")
    to_city = models.ForeignKey(City, null=True, blank=True,\
        on_delete=models.DO_NOTHING, related_name="to_city")

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        alert = "{} to {}".format(self.from_name(), self.to_name())
        return alert

    def from_where(self):
        """Returns the from field in the alert."""
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
        """Returns the to field in the alert, or returns None if there is no to field."""
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
        """Returns the name of the from field"""
        return self.from_where().name

    def to_name(self):
        """Returns the name of the to field, or 'Anywhere' if no to field is specified"""
        to_place = self.to_where()
        if to_place:
            return to_place.name
        else:
            return "Anywhere"

    def from_url(self):
        """Returns a photo_url from the from fields' place_id or returns a random image if the photo logic fails"""
        photo_reference = retrieve_photo_reference(self.from_where().place_id)
        if photo_reference:
            return retrieve_photo_url(photo_reference)
        return retrieve_random_image()

    def from_place_id(self):
        """Returns the from place id"""
        return self.from_where().place_id

    def to_url(self):
        """Returns a photo_url from the to fields' place_id or returns a random image if the photo logic fails or if there is no to field specified"""
        to_place = self.to_where()
        if to_place:
            photo_reference = retrieve_photo_reference(to_place.place_id)
            if photo_reference:
                return retrieve_photo_url(photo_reference)
        return retrieve_random_image()

    def to_place_id(self):
        """Returns a to place_id, or a random image"""
        to_place = self.to_where()
        if to_place:
            return to_place.place_id
        return retrieve_random_image()

    def use_place_id(self):
        """Returns whether a place_id is present or not"""
        to_place = self.to_where()
        if to_place:
            return True
        return False

    def from_keywords(self):
        """Returns from field keywords"""
        return self.from_where().all_keywords()

    def to_keywords(self):
        """Returns to field keywords, or if to field is null, returns all keywords"""
        to_place = self.to_where()
        if to_place:
            return to_place.all_keywords()
        return all_keywords()


# These are some place-related utilities that are best kept here I think
def all_keywords():
    """Returns all keywords in the database"""
    keywords = []
    regions = Region.objects.all()
    for region in regions:
        keywords.extend(region.all_keywords(sort=False))
    keywords.sort()
    keywords.sort(key = lambda s: len(s))
    keywords.reverse()
    return keywords

def all_case_sensitive_keywords():
    """Returns all case sensitive keywords in the database"""
    keywords = []
    regions = Region.objects.all()
    for region in regions:
        keywords.extend(region.case_sensitive_keywords())
    # sort the keywords by smallest to largest, then alphabetically.  That's because the iata codes are 3 characters and the abbreviations are minimum 5 characters because of the optional period syntax.  With the keywords in this order, a keywords like LAX will be found before L\.?A, as it should be found first

    keywords.sort()
    keywords.sort(key = lambda s: len(s))
    return keywords

def all_case_insensitive_keywords():
    """Returns all case insensitive keywords in the database"""
    keywords = []
    regions = Region.objects.all()
    for region in regions:
        keywords.extend(region.case_insensitive_keywords())
    # sorted first by largest to smallest, then in reverse alphabetical order.  So more specific places are found first before less specific places.
    keywords.sort()
    keywords.sort(key = lambda s: len(s))
    keywords.reverse()
    return keywords


class ContactMessage(models.Model):
    user = models.ForeignKey(UserProfile, null=True, blank=True,
                             on_delete=models.SET_NULL)
    message = models.CharField(max_length=5000)
