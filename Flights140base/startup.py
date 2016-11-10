"""startup.py - This file has methods to grab and load model data across different instances of this django database.  Moves data from test to production.  Very important because this website requires the models TwitterAccount, Region, Subregion, Country, State, and City to be populated before the website can be used.

And pg_save/pg_dump, the postgres utilites to do this sort of ETL work, don't work because the Foreign Key relationships in City-Region require that they be loaded into the database in a certain order."""

import json
import os
import dateutil.parser
from unidecode import unidecode
from collections import Counter
from django.utils.encoding import smart_unicode
from .models import Region, Subregion, Country, State, City, TwitterAccount


def load_places():
    """Loads Region, Subregion, Country, State, City in that order from a JSON file.  Order of loading these objects matters because of their Foreign Key relationships."""

    with open('places.JSON', 'r') as f:
        places = json.load(f)
    for place in places.get("regions"):
        new_region = Region(
            name=place.get("name"),
            plural_names=place.get("plural_names"),
            additional_keywords=place.get("additional_keywords"),
            abbreviations=place.get("abbreviations"),
            place_id=place.get("place_id"))
        new_region.save()
    for place in places.get("subregions"):
        new_subregion = Subregion(
            name=place.get("name"),
            plural_names=place.get("plural_names"),
            additional_keywords=place.get("additional_keywords"),
            abbreviations=place.get("abbreviations"),
            place_id=place.get("place_id"),
            region=Region.objects.get(name=place.get("region")))
        new_subregion.save()
    for place in places.get("countries"):
        new_country = Country(
            name=place.get("name"),
            plural_names=place.get("plural_names"),
            additional_keywords=place.get("additional_keywords"),
            abbreviations=place.get("abbreviations"),
            place_id=place.get("place_id"),
            region=Region.objects.get(name=place.get("region")))
        if place.get("subregion"):
            new_country.subregion =\
                Subregion.objects.get(name=place.get("subregion"))
        new_country.save()
    for place in places.get("states"):
        new_state = State(
            name=place.get("name"),
            plural_names=place.get("plural_names"),
            additional_keywords=place.get("additional_keywords"),
            abbreviations=place.get("abbreviations"),
            place_id=place.get("place_id"),
            region=Region.objects.get(name=place.get("region")),
            country=Country.objects.get(name=place.get("country")))
        if place.get("subregion"):
            new_state.subregion =\
                Subregion.objects.get(name=place.get("subregion"))
        new_state.save()
    for place in places.get("cities"):
        new_city = City(
            name=place.get("name"),
            plural_names=place.get("plural_names"),
            additional_keywords=place.get("additional_keywords"),
            abbreviations=place.get("abbreviations"),
            place_id=place.get("place_id"),
            iata=place.get("iata"),
            region=Region.objects.get(name=place.get("region")),
            country=Country.objects.get(name=place.get("country")))
        if place.get("subregion"):
            new_city.subregion =\
                Subregion.objects.get(name=place.get("subregion"))
        if place.get("state"):
            new_city.state =\
                State.objects.get(name=place.get("state"))
        new_city.save()
    return

def copy_places():
    """Copies City, State, Country, Subregion, and Region objects from django and dumps them to a JSON file"""

    cities = []
    countries = []
    states = []
    subregions = []
    regions = []
    for place in Region.objects.all():
        plural_names, additional_keywords, abbreviations= same_attributes(place)
        array = {
            "name": place.name,
            "plural_names": plural_names,
            "additional_keywords": additional_keywords,
            "abbreviations": abbreviations,
            "place_id": place.place_id
        }
        regions.append(array)
    for place in Subregion.objects.all():
        plural_names, additional_keywords, abbreviations= same_attributes(place)
        array = {
            "name": place.name,
            "plural_names": plural_names,
            "additional_keywords": additional_keywords,
            "abbreviations": abbreviations,
            "place_id": place.place_id,
            "region": place.region.name
        }
        subregions.append(array)
    for place in Country.objects.all():
        plural_names, additional_keywords, abbreviations= same_attributes(place)
        array = {
            "name": place.name,
            "plural_names": plural_names,
            "additional_keywords": additional_keywords,
            "abbreviations": abbreviations,
            "place_id": place.place_id,
            "region": place.region.name
        }
        if place.subregion:
            array["subregion"] = place.subregion.name
        countries.append(array)
    for place in State.objects.all():
        plural_names, additional_keywords, abbreviations= same_attributes(place)
        array = {
            "name": place.name,
            "plural_names": plural_names,
            "additional_keywords": additional_keywords,
            "abbreviations": abbreviations,
            "place_id": place.place_id,
            "region": place.region.name,
            "country": place.country.name
        }
        if place.subregion:
            array["subregion"] = place.subregion.name
        states.append(array)
    for place in City.objects.all():
        plural_names, additional_keywords, abbreviations= same_attributes(place)
        array = {
            "name": place.name,
            "plural_names": plural_names,
            "additional_keywords": additional_keywords,
            "abbreviations": abbreviations,
            "place_id": place.place_id,
            "region": place.region.name,
            "country": place.country.name
        }
        if place.subregion:
            array["subregion"] = place.subregion.name
        if place.state:
            array["state"] = place.state.name
        if place.iata:
            array["iata"] = place.iata
        else:
            array["iata"] = []
        cities.append(array)
    mass_array = {
        "regions": regions,
        "subregions": subregions,
        "countries": countries,
        "states": states,
        "cities": cities}
    with open('places.JSON','w') as fi:
        json.dump(mass_array, fi)
    return mass_array

def load_twitter_accounts():
    with open('twitterAccountMap.JSON', 'r') as f:
        twitter_accounts = json.load(f)
    for twitter_account in twitter_accounts:
        new_account = TwitterAccount(
            user_id=twitter_account.get("user_id"),
            full_name=twitter_account.get("full_name"),
            screen_name=twitter_account.get("screen_name"))
        new_account.save()
    return

def same_attributes(place):
    plural_names = place.plural_names
    if not plural_names:
        plural_names = []

    additional_keywords = place.additional_keywords
    if not additional_keywords:
        additional_keywords = []

    abbreviations = place.abbreviations
    if not abbreviations:
        abbreviations = []
    return plural_names, additional_keywords, abbreviations
