import os
import re
import json
from collections import Counter
from django.utils.encoding import smart_unicode
from unidecode import unidecode
from .models import case_insensitive_keywords, case_sensitive_keywords
import logging
from collections import namedtuple


def encode(words):
    return unidecode(smart_unicode(words))

def variables():
    module_dir = os.path.dirname(__file__)# get current directory
    navigate = os.path.join(module_dir,
                            "static/Flights140base/js/JSON/")

    exclude_airline_file = os.path.join(navigate,
        'excludeAirlineList.JSON')

    with open(exclude_airline_file, "r") as json_file3:
        exclude_airline_list = json.load(json_file3)

    unique_exclude_airline_list = []
    for airline in exclude_airline_list:
        unique_exclude_airline_list.append(airline)
    return unique_exclude_airline_list

def search_string_capture(text, ignore_case=True):
    if ignore_case:
        return re.compile("^({})$|^({})\W.*$|^.*\W({})$|.*\W({})\W.*".format(
            text, text, text, text), re.IGNORECASE)
    return re.compile("^({})$|^({})\W.*$|^.*\W({})$|.*\W({})\W.*".format(
        text, text, text, text))

def search_string(text, ignore_case=True):
    if ignore_case:
        return re.compile("^{}$|^{}\W.*$|^.*\W{}$|.*\W{}\W.*".format(
            text, text, text, text), re.IGNORECASE)
    return re.compile("^{}$|^{}\W.*$|^.*\W{}$|.*\W{}\W.*".format(
        text, text, text, text))

def spaces_optional(string):
    return string.replace(" ", "\s?")

def exclude_airline(tweet):
    exclude_airline_list = variables()
    for airline in exclude_airline_list:
        airline_spaces = spaces_optional(airline)
        search_string = r'.*({}).*'.format(airline)
        airline_search = re.compile(search_string, flags=re.IGNORECASE)
        airline_match = airline_search.match(tweet)
        if airline_match:
            for match in airline_match.groups():
                if match:
                    tweet = tweet.replace(match, "")
    return tweet

def remove_stopover(tweet):
    stopover_criteria = re.compile(r'.*(stopover|layover)(.*)', re.IGNORECASE)
    stopover_match = stopover_criteria.match(tweet)
    if stopover_match:
        stopover_string = stopover_match.groups()[1]
        return tweet.replace(stopover_string, "")
    return tweet

def remove_url(tweet):
    pos = tweet.find("http")
    if pos > -1:
        return tweet[0:pos]
    return tweet

def remove_end_of_string(tweet):
    if tweet.find("\n") > -1:
        tweet = tweet.replace("\n", "")
    if tweet.find("\r") > -1:
        tweet = tweet.replace("\r", "")
    return tweet

def remove_specific(tweet):
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

def vice_versa_check(from_keywords, to_keywords, tweet):
    vice_versa_search = re.compile(r'.*(vice\Wversa).*',
                                   flags=re.IGNORECASE)
    vice_versa_results = vice_versa_search.match(tweet)
    if vice_versa_results:
        from_keywords.extend(to_keywords)
        return from_keywords, from_keywords
    return from_keywords, to_keywords

def build_parsed_tweet(from_keywords, to_keywords, tweet):
    from_keywords = extract_keywords(from_keywords)
    to_keywords = extract_keywords(to_keywords)
    if from_keywords == to_keywords:
        return None
    from_keywords, to_keywords = vice_versa_check(
        from_keywords, to_keywords, tweet)
    parsed_tweet = {
        "from": from_keywords,
        "to":   to_keywords}
    return parsed_tweet


def find_keywords(string, keywords_to_find=None):
    keywords = namedtuple("keywords", ["case_sensitive", "case_insensitive"])
    found_case_sensitive_keyword_list = []
    found_case_insensitive_keyword_list = []
    if not keywords_to_find:
        keywords_to_find = keywords(case_sensitive_keywords(),
                                    case_insensitive_keywords())

    for keyword in keywords_to_find.case_sensitive:
        keyword_search = search_string_capture(keyword, ignore_case=False)
        keyword_found = keyword_search.match(string)
        if keyword_found:
            for string_part in keyword_found.groups():
                if string_part:
                    string = string.replace(string_part, "")
            found_case_sensitive_keyword_list.append(keyword)

    for keyword in keywords_to_find.case_insensitive:
        keyword_search = search_string_capture(keyword)
        keyword_found = keyword_search.match(string)
        if keyword_found:
            for string_part in keyword_found.groups():
                if string_part:
                    string = string.replace(string_part, "")
            found_case_insensitive_keyword_list.append(keyword)

    found_keyword_list = keywords(found_case_sensitive_keyword_list,
                                found_case_insensitive_keyword_list)
    return found_keyword_list

def extract_keywords(keyword_tuple):
    keywords = []
    keywords.extend(keyword_tuple.case_sensitive)
    keywords.extend(keyword_tuple.case_insensitive)
    return keywords

def is_keyword_none(keyword_tuple):
    if not keyword_tuple.case_sensitive and not keyword_tuple.case_insensitive:
        return True
    return False

def parse_tweet(tweet):
    # First do some tweet cleanup
    tweet_to_parse = encode(tweet)
    tweet_to_parse = remove_url(tweet_to_parse)
    tweet_to_parse = exclude_airline(tweet_to_parse)
    tweet_to_parse = remove_specific(tweet_to_parse)
    tweet_to_parse = remove_stopover(tweet_to_parse)
    tweet_to_parse = remove_end_of_string(tweet_to_parse)
    # This finds all the keywords in the whole tweet
    found_keywords = find_keywords(tweet_to_parse)
    if is_keyword_none(found_keywords):
        return None

    # Now we have the keywords, but we need to know where they are to establish
    # the to/from relationship
    from_to_search = re.compile(r'.*from\s(.*?)\sto\s(.*)', flags=re.IGNORECASE)
    from_to_results = from_to_search.match(tweet_to_parse)
    if from_to_results:
        from_string = from_to_results.groups()[0]
        to_string = from_to_results.groups()[1]
        if from_string and to_string:
            from_keywords = find_keywords(from_string, found_keywords)
            to_keywords = find_keywords(to_string, found_keywords)
            if not is_keyword_none(from_keywords) \
                and not is_keyword_none(to_keywords):
                return build_parsed_tweet(from_keywords, to_keywords,
                                          tweet_to_parse)

    to_from_search = re.compile(r'.*to\s(.*?)from\s(.*)', flags=re.IGNORECASE)
    to_from_results = to_from_search.match(tweet_to_parse)
    if to_from_results:
        from_string = to_from_results.groups()[1]
        to_string = to_from_results.groups()[0]
        if from_string and to_string:
            from_keywords = find_keywords(from_string, found_keywords)
            to_keywords = find_keywords(to_string, found_keywords)
            if not is_keyword_none(from_keywords) \
                and not is_keyword_none(to_keywords):
                return build_parsed_tweet(from_keywords, to_keywords,
                                          tweet_to_parse)
    to_search = re.compile(r'(.*?)\sto\s(.*)', flags=re.IGNORECASE)
    to_results = to_search.match(tweet_to_parse)
    if to_results:
        from_string = to_results.groups()[0]
        to_string = to_results.groups()[1]
        if from_string and to_string:
            from_keywords = find_keywords(from_string, found_keywords)
            to_keywords = find_keywords(to_string, found_keywords)
            if not is_keyword_none(from_keywords) \
                and not is_keyword_none(to_keywords):
                return build_parsed_tweet(from_keywords, to_keywords,
                                          tweet_to_parse)

    from_search = re.compile(r'(.*?)\sfrom\s(.*)', flags=re.IGNORECASE)
    from_results = from_search.match(tweet_to_parse)
    if from_results:
        from_string = from_results.groups()[1]
        to_string = from_results.groups()[0]
        if from_string and to_string:
            from_keywords = find_keywords(from_string, found_keywords)
            to_keywords = find_keywords(to_string, found_keywords)
            if not is_keyword_none(from_keywords) \
                and not is_keyword_none(to_keywords):
                return build_parsed_tweet(from_keywords, to_keywords,
                                          tweet_to_parse)

    # assume that the place we're looking for doesn't have dashes if the tweet
    # is using dashes to separate the origin and destination
    dashes = ["- -","--","-"]
    for dash in dashes:
        if tweet_to_parse.find(dash) > -1:
            parts = tweet_to_parse.split(dash)
            number_parts = len(parts)
            for n in range(number_parts-1):
                from_string = parts[n]
                to_string = parts[n+1]
                from_keywords = find_keywords(from_string, found_keywords)
                to_keywords = find_keywords(to_string, found_keywords)
                if not is_keyword_none(from_keywords) \
                    and not is_keyword_none(to_keywords):
                    return build_parsed_tweet(from_keywords, to_keywords, tweet)

    both_way_search = re.compile(r'(.*)to/from\s(.*)', flags=re.IGNORECASE)
    both_way_result = both_way_search.match(tweet_to_parse)
    if both_way_result:
        from_string = both_way_result.groups()[0]
        to_string = both_way_result.groups()[1]
        if from_string and to_string:
            from_keywords = find_keywords(from_string, found_keywords)
            to_keywords = find_keywords(to_string, found_keywords)
            if not is_keyword_none(from_keywords) \
                and not is_keyword_none(to_keywords):
                keywords = []
                keywords.extend(extract_keywords(from_keywords))
                keywords.extend(extract_keywords(to_keywords))
                parsed_tweet= {
                    "from": keywords,
                    "to":   keywords}
                return parsed_tweet

    between_search = re.compile(r'.*between(.*)', flags=re.IGNORECASE)
    between_result = between_search.match(tweet_to_parse)
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
    forward_slash_results = forward_slash_search.match(tweet_to_parse)
    if forward_slash_results:
        from_string = forward_slash_results.groups()[0]
        to_string = forward_slash_results.groups()[1]
        if from_string and to_string:
            from_keywords = find_keywords(from_string, found_keywords)
            to_keywords = find_keywords(to_string, found_keywords)
            if not is_keyword_none(from_keywords) \
                and not is_keyword_none(to_keywords):
                return build_parsed_tweet(from_keywords, to_keywords,
                                          tweet_to_parse)
    return None
