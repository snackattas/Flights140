"""parse.py - Contains parse_tweets which parses for keywords from the django database and returns a dictionary of the relevant information (or none).  It also contains all the helper methods for parsing tweets."""

from .utilities import encode
from .models import all_case_sensitive_keywords, all_case_insensitive_keywords

import os
import re
import json
from collections import Counter, namedtuple
import logging

def parse_tweet(raw_tweet):
    """This is the main method of this module.  It tries to parse tweets, looking for place keywords and determining if they are part of the from keywords or to keywords.  It runs thousands of regex checks.  A tweet will only be considered parsed if it has both from keywords and to keywords.  If there are no matches, it will return None."""

    # First do some tweet cleanup
    processed_tweet = encode(raw_tweet)
    processed_tweet = remove_url(processed_tweet)
    processed_tweet = remove_airline(processed_tweet)
    processed_tweet = remove_specific(processed_tweet)
    processed_tweet = remove_stopover(processed_tweet)
    processed_tweet = remove_end_of_string(processed_tweet)
    # This finds all the keywords in the whole tweet
    found_keywords = find_keywords(processed_tweet)
    if is_keyword_none(found_keywords):
        return None

    # Now we have the keywords, but we need to know where they are to establish
    # the to/from relationship
    from_to_search = re.compile(r'.*from\s(.*?)\sto\s(.*)', flags=re.IGNORECASE)
    from_to_results = from_to_search.match(processed_tweet)
    if from_to_results:
        from_string = from_to_results.groups()[0]
        to_string = from_to_results.groups()[1]
        if from_string and to_string:
            from_keywords_tuple = find_keywords(from_string, found_keywords)
            to_keywords_tuple = find_keywords(to_string, found_keywords)
            if not are_keywords_none(from_keywords_tuple, to_keywords_tuple):
                return build_parsed_tweet(from_keywords_tuple,
                                          to_keywords_tuple, processed_tweet)

    to_from_search = re.compile(r'.*to\s(.*?)from\s(.*)', flags=re.IGNORECASE)
    to_from_results = to_from_search.match(processed_tweet)
    if to_from_results:
        from_string = to_from_results.groups()[1]
        to_string = to_from_results.groups()[0]
        if from_string and to_string:
            from_keywords_tuple = find_keywords(from_string, found_keywords)
            to_keywords_tuple = find_keywords(to_string, found_keywords)
            if not are_keywords_none(from_keywords_tuple, to_keywords_tuple):
                return build_parsed_tweet(from_keywords_tuple,
                                          to_keywords_tuple, processed_tweet)
    to_search = re.compile(r'(.*?)\sto\s(.*)', flags=re.IGNORECASE)
    to_results = to_search.match(processed_tweet)
    if to_results:
        from_string = to_results.groups()[0]
        to_string = to_results.groups()[1]
        if from_string and to_string:
            from_keywords_tuple = find_keywords(from_string, found_keywords)
            to_keywords_tuple = find_keywords(to_string, found_keywords)
            if not are_keywords_none(from_keywords_tuple, to_keywords_tuple):
                return build_parsed_tweet(from_keywords_tuple,
                                          to_keywords_tuple, processed_tweet)

    from_search = re.compile(r'(.*?)\sfrom\s(.*)', flags=re.IGNORECASE)
    from_results = from_search.match(processed_tweet)
    if from_results:
        from_string = from_results.groups()[1]
        to_string = from_results.groups()[0]
        if from_string and to_string:
            from_keywords_tuple = find_keywords(from_string, found_keywords)
            to_keywords_tuple = find_keywords(to_string, found_keywords)
            if not are_keywords_none(from_keywords_tuple, to_keywords_tuple):
                return build_parsed_tweet(from_keywords_tuple,
                                          to_keywords_tuple, processed_tweet)

    # assume that the place we're looking for doesn't have dashes if the tweet
    # is using dashes to separate the origin and destination
    dashes = ["- -","--","-"]
    for dash in dashes:
        if processed_tweet.find(dash) > -1:
            parts = processed_tweet.split(dash)
            number_parts = len(parts)
            for n in range(number_parts-1):
                from_string = parts[n]
                to_string = parts[n+1]
                from_keywords_tuple = find_keywords(from_string, found_keywords)
                to_keywords_tuple = find_keywords(to_string, found_keywords)
                if not are_keywords_none(from_keywords_tuple,
                                         to_keywords_tuple):
                    return build_parsed_tweet(from_keywords_tuple,
                        to_keywords_tuple, processed_tweet)

    both_way_search = re.compile(r'(.*)to/from\s(.*)', flags=re.IGNORECASE)
    both_way_result = both_way_search.match(processed_tweet)
    if both_way_result:
        from_string = both_way_result.groups()[0]
        to_string = both_way_result.groups()[1]
        if from_string and to_string:
            from_keywords_tuple = find_keywords(from_string, found_keywords)
            to_keywords_tuple = find_keywords(to_string, found_keywords)
            if not are_keywords_none(from_keywords_tuple, to_keywords_tuple):
                keywords = []
                keywords.extend(extract_keywords(from_keywords_tuple))
                keywords.extend(extract_keywords(to_keywords_tuple))
                parsed_tweet= {
                    "from": keywords,
                    "to":   keywords}
                return parsed_tweet

    between_search = re.compile(r'.*between(.*)', flags=re.IGNORECASE)
    between_result = between_search.match(processed_tweet)
    if between_result:
        between_string = between_result.groups()[0]
        keywords = find_keywords(between_string, found_keywords)
        keywords = extract_keywords(keywords)
        if len(keywords) >= 2:
            parsed_tweet = {
                'from': keywords,
                'to':   keywords}
            return parsed_tweet

    forward_slash_search = re.compile(r'(.*?)/(.*)', flags=re.IGNORECASE)
    forward_slash_results = forward_slash_search.match(processed_tweet)
    if forward_slash_results:
        from_string = forward_slash_results.groups()[0]
        to_string = forward_slash_results.groups()[1]
        if from_string and to_string:
            from_keywords_tuple = find_keywords(from_string, found_keywords)
            to_keywords_tuple = find_keywords(to_string, found_keywords)
            if not are_keywords_none(from_keywords_tuple, to_keywords_tuple):
                return build_parsed_tweet(from_keywords_tuple, to_keywords_tuple,
                                          processed_tweet)
    return None

# These next methods prefixed with "remove" are the processing methods that prepare the raw tweet text to go through its regex parsing
def remove_url(tweet):
    """There can be random letters in the urls in tweets that sometimes get flagged as iata codes or abbreviations of places, so it's wise to just get rid of the url in a tweet."""

    pos = tweet.find("http")
    if pos > -1:
        return tweet[0:pos]
    return tweet

def get_exclude_airline():
    """Retrieves excludeAirlineList.JSON from server, puts it in a list"""

    module_dir = os.path.dirname(__file__)# get current directory
    exclude_airline_file = os.path.join(module_dir,
        'excludeAirlineList.JSON')

    with open(exclude_airline_file, "r") as json_file3:
        exclude_airline_list = json.load(json_file3)

    unique_exclude_airline_list = []
    for airline in exclude_airline_list:
        unique_exclude_airline_list.append(airline)
    return unique_exclude_airline_list

def remove_airline(tweet):
    """Airline names have place names in them that throw off the regex place searching, so we need to remove known airline names"""

    exclude_airline_list = get_exclude_airline()
    for airline in exclude_airline_list:
        airline_spaces = airline.replace(" ", "\s?")
        search_string = r'.*({}).*'.format(airline)
        airline_search = re.compile(search_string, flags=re.IGNORECASE)
        airline_match = airline_search.match(tweet)
        if airline_match:
            for match in airline_match.groups():
                if match:
                    tweet = tweet.replace(match, "")
    return tweet

def remove_specific(tweet):
    """This method removes strings I've come across that throw off the tweet parsing for various random reasons"""
    remove_list = ["\[us\]", "per person", "\d*\W?day"]
    for removal in remove_list:
        remove_string = r'.*({}).*'.format(removal)
        remove_search = re.compile(remove_string, flags=re.IGNORECASE)
        remove_match = remove_search.match(tweet)
        if remove_match:
            for match in remove_match.groups():
                if match:
                    tweet = tweet.replace(match, "")
    return tweet

def remove_stopover(tweet):
    """When tweets mention stopovers/layovers, the regex can include them accidentally in to/from results.  Since they are not actual results we remove everything after the strings are found"""

    stopover_criteria = re.compile(r'.*(stopover|layover)(.*)', re.IGNORECASE)
    stopover_match = stopover_criteria.match(tweet)
    if stopover_match:
        stopover_string = stopover_match.groups()[1]
        return tweet.replace(stopover_string, "")
    return tweet

def remove_end_of_string(tweet):
    """If tweets have carriage returns or new lines, that messes up the regex's $ syntax, or the end of search.  So it's good to just get rid of new lines/carriage returns and smush the tweet text together when parsing."""

    tweet = tweet.replace("\n", "")
    tweet = tweet.replace("\r", "")
    return tweet

# These are helper functions usesd in the parsing of the tweet
def search_string_capture(text, ignore_case=True):
    """This method responsibly compiles searches for the keywords we're looking for in tweets.

    Ex.
    BEG is the airport code for Belgrade.  If the tweet is 'Now it BEGINS', BEG won't be flagged because it's in the middle of a word.  But something like #BEG will be flagged"""

    if ignore_case:
        return re.compile("^({})$|^({})\W.*$|^.*\W({})$|.*\W({})\W.*".format(
            text, text, text, text), re.IGNORECASE)
    return re.compile("^({})$|^({})\W.*$|^.*\W({})$|.*\W({})\W.*".format(
        text, text, text, text))

def is_keyword_none(keyword_tuple):
    """Checks if the keywords tuple is empty."""

    if keyword_tuple.case_sensitive or keyword_tuple.case_insensitive:
        return False
    return True

def are_keywords_none(keyword_tuple, keywords_tuple2):
    """Checks if either of two keywords tuples are empty"""

    if is_keyword_none(keyword_tuple) or is_keyword_none(keywords_tuple2):
        return True
    return False

def extract_keywords(keyword_tuple):
    """Combines the keyword tuple attributes case sensitive and case insensitive into a list"""

    keywords = []
    keywords.extend(keyword_tuple.case_sensitive)
    keywords.extend(keyword_tuple.case_insensitive)
    return keywords

def vice_versa_check(from_keywords, to_keywords, tweet):
    """This method looks for the characters vice-versa in a tweet, and if it's present, it combines the to and from keywords together."""

    vice_versa_search = re.compile(r'.*(vice\Wversa).*',
                                   flags=re.IGNORECASE)
    vice_versa_results = vice_versa_search.match(tweet)
    if vice_versa_results:
        from_keywords.extend(to_keywords)
        return from_keywords, from_keywords
    return from_keywords, to_keywords

def build_parsed_tweet(from_keywords_tuple, to_keywords_tuple, tweet):
    """Takes the keywords tuples, performs some checks, and returns a parsed tweet dictionary that can be sent through queues."""

    from_keywords = extract_keywords(from_keywords_tuple)
    to_keywords = extract_keywords(to_keywords_tuple)
    logging.warning(from_keywords)
    logging.warning(to_keywords)
    if from_keywords == to_keywords:
        return None
    from_keywords, to_keywords = vice_versa_check(
        from_keywords, to_keywords, tweet)
    parsed_tweet = {
        "from": from_keywords,
        "to":   to_keywords}
    return parsed_tweet


def find_keywords(string, list_keywords=None):
    """This is the main helper method for parse_tweet.  It does the work of looking for the keywords in tweets.

    The first time find_keywords is called in parse_tweets, the variable list_keywords should not be passed in.  With list_keywords=None, the method will pull all the possible keywords from the Django database and search the entire tweet for them, and return a keywords tuple of the found keywords.

    Subsequent calls of find_keywords should pass in the results of the first call as list_keywords.  That way, when the tweet is later broken up into to/from parts, and it needs to be discovered which keywords are in which segment, the pool of keywords to draw upon will be the keywords_tuple initially returned, and is much smaller than the total amount of keywords."""

    keywords = namedtuple("keywords", ["case_sensitive", "case_insensitive"])
    case_sensitive_keyword_list = []
    case_insensitive_keyword_list = []
    # If no list was passed in, method retrieves all keywords from database
    if not list_keywords:
        list_keywords = keywords(all_case_sensitive_keywords(),
                                 all_case_insensitive_keywords())

    for keyword in list_keywords.case_insensitive:
        keyword_search = search_string_capture(keyword)
        keyword_found = keyword_search.match(string)
        if keyword_found:
            for string_part in keyword_found.groups():
                if string_part:
                    string = string.replace(string_part, "")
            case_insensitive_keyword_list.append(keyword)

    for keyword in list_keywords.case_sensitive:
        keyword_search = search_string_capture(keyword, ignore_case=False)
        keyword_found = keyword_search.match(string)
        if keyword_found:
            for string_part in keyword_found.groups():
                if string_part:
                    string = string.replace(string_part, "")
            case_sensitive_keyword_list.append(keyword)

    found_keyword_list = keywords(case_sensitive_keyword_list,
                                case_insensitive_keyword_list)
    return found_keyword_list
