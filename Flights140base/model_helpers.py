"""model_helpers.py - This module contains utilities to retrieve place_ids for use in the google place APIs.  place_ids are pieces of data for a Region/Subregion/Country/State/City that needs to be stored in the django database, so that a picture of the place can be retrieved with 1 API call using the place_id, instead of 2.

This module also contains helper functions to create place keywords that are able to be found using regex"""

import os
import re
import requests
from random import randrange


def encode_place(place):
    """Replaces spaces with addition signs in places since places are included in the request url, and you can't use spaces in urls"""

    encoded_place = place.replace(" ", "+") # this just url-ify's the string
    return encoded_place

def retrieve_random_image():
    """If the logic to retrieve the photo_reference from a field's place_id fails, or if there is no field specified, this method is called.  It will return a random picture, since no specific picture from place_id can be found"""
    return os.environ['RANDOM_PHOTO_LOCATION'] + str(randrange(1,51)) + ".jpg"

def retrieve_place_id(place):
    """First executes a textsearch to try and get a place_id.  If the textsearch doesn't return a place_id, then it picks the latitudes/longitudes from the textsearch and executes nearby searches to try and get a place_id"""

    encoded_place = encode_place(place)
    # https://developers.google.com/places/web-service/search#TextSearchRequests
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "key": os.environ["GOOGLE_PLACE_SEARCH_API_KEY"],
        "query": encoded_place}

    response = requests.get(url, params).json()
    try:
        # If the response contains a photo_reference, it will also contain a usable place_id.  If any of these dictionary get calls fail, it will mean that there's no photo_reference/place_id
        photo_details = response.get("results")[0].get("photos")[0]
        photo_reference = photo_details.get("photo_reference")
        if photo_reference:
            place_id = response.get("results")[0].get("place_id")
    except:
        # If the textsearch fails, we'll grab latitudes/longitudes from the textsearch and execute nearby searches with retrieve_place_id_by_location
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
    """This is the backup plan for getting a place_id, using latitude/longitude pairs instead of the text terms"""

    # https://developers.google.com/places/web-service/search#PlaceSearchRequests
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
    """We are able to cache place_ids, but it is not allowed according to Google Place APIs ToS to cache photo references, which are the strings that refer to google's photos.  This method retrieve a place_id's photo_reference."""

    # https://developers.google.com/places/web-service/details#PlaceDetailsRequests
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
    """Returns the url to put directly into a html img tag to reference a place_id's photo.  If for some reason no photo is able to be returned, a random photo will be returned."""

    # https://developers.google.com/places/web-service/photos
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
        return retrieve_random_image()

def regexify_special_chars(word_list):
    """This method turns special characters like '.','-',' ' and certain abbreviations in words like St. or Fort, and adds regex parts to it"""

    new_word_list = []
    for word in word_list:
        # In these replacement pairs, position 1 replaces position 0 in the word
        replacement_pairs = [
            [".", "\.?"],
            ["St.? ", "(St\.?|Saint)\s?"],
            ["Fort ", "(Ft\.?|Fort)\s?"],
            [" and ", "(\s?and\s?|\s?&\s?|\s?&amp;\s?)"],
            ["-","(-?|\s)"],
            ["'","'?"],
            [" ", "\s?"]]
        for pair in replacement_pairs:
            if pair[0] in word:
                word = word.replace(pair[0], pair[1])
        new_word_list.append(word)
    return new_word_list

def regexify_abbreviation(abbr_list):
    """Adds optional periods to abbreviations to better spot abbreviations using regex in tweets."""

    new_abbr_list = []
    for abbr in abbr_list:
        word_length = len(abbr)
        new_abbr = abbr[0]
        for n in range(1, word_length):
            new_abbr += "\.?" + abbr[n]
        new_abbr_list.append(new_abbr)
    return new_abbr_list
