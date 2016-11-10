"""view_helper.py - Has helper methods for views.py"""
from .models import Region, Subregion, Country, State, City, Alert
from .utilities import encode
from collections import namedtuple

def get_name(user_profile):
    """Makes best attempt to pull a name from python social auth User object"""
    full_name = user_profile.user.get_full_name()
    if full_name:
        return full_name
    username = user_profile.user.username
    if username:
        return username
    return user_profile.email


def parse_ajax(data):
    """This method parses the data sent via ajax to the create_alert view, and returns the objects

    Format of the keys in the dictionary
    {<to/from>[<scope/Country/CityState/CountrySubregionRegion>]: [<value>]}
    - the to/from part before the brackets is, well, whether it's to or from
    - If the part in the brackets is scope, there are two possible values: CountrySubregionRegion or CityState.  It indicates which possible model the value is part of
    - If the part in the brackets is Country, the value is the country
    - If the part in the brackets is CityState, the value is either a city or state
    - If the part in the brackets is CountrySubregionRegion, the value is either a country, subregion, regions

    Ex. of data coming in
    {u'from[scope]': [u'CountrySubregionRegion'], u'from[CountrySubregionRegion]': [u'North America'],
    u'to[scope]': [u'CityState'],
    u'to[Country]': [u'Spain'],
    u'to[CityState]': [u'Malaga']}

    {u'from[scope]': [u'CityState'],
    u'from[Country]': [u'United States'],
    u'from[CityState]': [u'Alaska']}

    The countries/subregions/regions coming in are more straightforward.  If the scope is CountrySubregionRegion, we just run the Django manager filter operation until the object is found

    cities/states are more complicated since it's possible for a city to share the same name as its country.  So we run the Django manager with the state or city and the country passed in from ajax.
    """
    directions = ["from", "to"]
    results = []
    place_tuple = namedtuple("place_tuple", "scope value original_name")
    for direction in directions:
        scope = data.get(direction+"[scope]")
        if scope == 'CityState':
            raw_city_state = data.get(direction+"[CityState]")
            city_state = encode(raw_city_state)
            country = encode(data.get(direction+"[Country]"))
            country = Country.objects.get(name=country)
            city = City.objects.filter(name=city_state, country=country)
            if city:
                results.append(place_tuple(
                    scope="city",
                    value=city[0],
                    original_name=raw_city_state))
            else:
                state = State.objects.filter(
                    name=city_state, country=country)
                results.append(place_tuple(
                    scope="state",
                    value=state[0],
                    original_name=raw_city_state))
        if scope == 'CountrySubregionRegion':
            raw_country_subregion_region = \
                data.get(direction+"[CountrySubregionRegion]")
            country_subregion_region = encode(raw_country_subregion_region)
            country = Country.objects.filter(name=country_subregion_region)
            if country:
                results.append(place_tuple(
                    scope="country",
                    value=country[0],
                    original_name=raw_country_subregion_region))
            else:
                subregion = Subregion.objects.filter(
                    name=country_subregion_region)
                if subregion:
                    results.append(place_tuple(
                        scope="subregion",
                        value=subregion[0],
                        original_name=raw_country_subregion_region))
                else:
                    region = Region.objects.filter(
                        name=country_subregion_region)
                    if region:
                        results.append(place_tuple(
                            scope="region",
                            value=region[0],
                            original_name=raw_country_subregion_region))
                    else:
                        results.append(place_tuple(
                            scope=None,
                            value=None,
                            original_name=None))
        if not scope:
            results.append(place_tuple(
                scope=None,
                value=None,
                original_name=None))
    return results[0], results[1]


def does_alert_exist(alerts, from_value, from_scope, to_value, to_scope):
    if from_scope == "region":
        alerts = alerts.filter(from_region=from_value)
    if from_scope == "subregion":
        alerts = alerts.filter(from_subregion=from_value)
    if from_scope == "country":
        alerts = alerts.filter(from_country=from_value)
    if from_scope == "state":
        alerts = alerts.filter(from_state=from_value)
    if from_scope == "city":
        alerts = alerts.filter(from_city=from_value)
    if to_scope:
        if to_scope == "region":
            alerts = alerts.filter(to_region=to_value)
        if to_scope == "subregion":
            alerts = alerts.filter(to_subregion=to_value)
        if to_scope == "country":
            alerts = alerts.filter(to_country=to_value)
        if to_scope == "state":
            alerts = alerts.filter(to_state=to_value)
        if to_scope == "city":
            alerts = alerts.filter(to_city=to_value)
    else:
        alerts = alerts.filter(to_region__isnull=True).\
            filter(to_subregion__isnull=True).\
            filter(to_country__isnull=True).\
            filter(to_state__isnull=True).\
            filter(to_city__isnull=True)
    if alerts:
        return True
    return False

def create_alert_object(user_profile, from_value, from_scope, to_value,
                        to_scope):
    new_alert = Alert(user=user_profile)
    if from_scope == "region":
        new_alert.from_region = from_value
    if from_scope == "subregion":
        new_alert.from_subregion = from_value
    if from_scope == "country":
        new_alert.from_country = from_value
    if from_scope == "state":
        new_alert.from_state = from_value
    if from_scope == "city":
        new_alert.from_city = from_value
    if to_scope == "region":
        new_alert.to_region = to_value
    if to_scope == "subregion":
        new_alert.to_subregion = to_value
    if to_scope == "country":
        new_alert.to_country = to_value
    if to_scope == "state":
        new_alert.to_state = to_value
    if to_scope == "city":
        new_alert.to_city = to_value

    new_alert.save()
    return new_alert
