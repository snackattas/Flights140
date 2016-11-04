from django.shortcuts import render, reverse, render_to_response
from django.http import JsonResponse
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.core import serializers
from django.views.decorators.csrf import csrf_protect
from social.apps.django_app.utils import psa

from .models import UserProfile, Alert, ContactMessage, TwitterAccount
from .models import Region, Subregion, Country, State, City
from .models import mailgun_validate, twilio_validate

from functools import wraps
from unidecode import unidecode
import dateutil.parser
from django.utils.encoding import smart_unicode
import arrow
import json
from random import randrange
from collections import namedtuple


def encode(words):
    return unidecode(smart_unicode(words))

def twitter_created_at_to_python(twitter_created_at):
    return dateutil.parser.parse(twitter_created_at).\
                                     replace(tzinfo=dateutil.tz.tzutc())

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def requires_login(function):
    """"""
    @wraps(function)
    def decorated_function(*args, **kwargs):
        # import pdb; pdb.set_trace()
        request = args[0]
        if not request.user or request.user.is_anonymous:
            return HttpResponseRedirect(reverse('flights140base:login'))
        else:
            return function(*args, **kwargs)
    return decorated_function


def login(request):
    try:
        if request.user and not request.user.is_anonymous:
            context = RequestContext(request,
                                    {'request': request,
                                     'user': request.user})
            return HttpResponseRedirect(reverse('flights140base:main'),
                                        context)
        else:
            return render_to_response('Flights140base/login.html')
    except:
        return render_to_response('Flights140base/login.html')

def get_name(user_profile):
    full_name = user_profile.user.get_full_name()
    if full_name:
        return full_name
    username = user_profile.user.username
    if username:
        return username
    return user_profile.email

@requires_login
def main(request):
    directions = ["from", "to"]
    user_profile = UserProfile.objects.filter(user=request.user)
    if not user_profile:
        if request.user.email:
            user_profile = UserProfile(
                user=request.user,
                email=request.user.email)
            user_profile.save()
        else:
            user_profile = UserProfile(user=request.user)
            user_profile.save()
    else:
        user_profile = user_profile[0]

    alert_objects = Alert.objects.filter(user=user_profile).\
        extra(order_by=['-timestamp'])
    name = get_name(user_profile)
    alerts = []
    alert_tuple = namedtuple("alert_tuple", "from_name from_place_id"\
                             " to_name to_place_id use_place_id time id")
    for alert_object in alert_objects:
        alert_id = alert_object.id
        from_name = alert_object.from_name()
        from_place_id = alert_object.from_place_id()
        to_name = alert_object.to_name()
        to_place_id, use_place_id = alert_object.to_place_id()
        time = arrow.get(alert_object.timestamp).humanize()

        alert = alert_tuple(from_name=from_name, from_place_id=from_place_id,\
            to_name=to_name, to_place_id=to_place_id,\
            use_place_id=use_place_id, time=time, id=alert_id)
        alerts.append(alert)
    contact_form = render_to_string("Flights140base/contactForm.html")
    twitter_accounts = TwitterAccount.objects.all().order_by("full_name")
    twitter_account_chunks = chunks(twitter_accounts, 5)
    twitter_accounts_form = render_to_string(\
        "Flights140base/twitterAccounts.html",
        {'twitter_account_chunks':twitter_account_chunks})
    how_it_works_form = render_to_string("Flights140base/howItWorks.html")
    email = user_profile.email
    phone_number = user_profile.phone_number
    edit_account_form = render_to_string("Flights140base/editAccount.html",
                                    {'email': email,
                                    'phone_number': phone_number})
    delete_account_form = render_to_string(request=request,
        template_name="Flights140base/deleteAccount.html",
        context={'name': name})

    donate = render_to_string("Flights140base/donate.html")
    privacy_policy = render_to_string("Flights140base/disclaimer.html")
    context = RequestContext(request,
                            {'request':            request,
                             'user':               request.user,
                             'name':               name,
                             'directions':         directions,
                             'alerts':             alerts,
                             'contact_form':       contact_form,
                             'how_it_works':       how_it_works_form,
                             'twitter_accounts':   twitter_accounts_form,
                             'edit_account':       edit_account_form,
                             'delete_account':     delete_account_form,
                             'donate':             donate,
                             'privacy_policy':     privacy_policy})
    return render_to_response('Flights140base/main.html',
                              context=context)

def retrieve_place_object(data):
    directions = ["from", "to"]
    results = []
    for direction in directions:
        scope = data.get(direction+"[scope]")
        if scope == 'CityState':
            city_state_original = data.get(direction+"[CityState]")
            city_state = encode(city_state_original)
            country = encode(data.get(direction+"[Country]"))
            country = Country.objects.get(name=country)
            city = City.objects.filter(name=city_state, country=country)
            if city:
                results.append(city[0])
                results.append("city")
                results.append(city_state_original)
            else:
                state =State.objects.filter(
                    name=city_state, country=country)[0]
                results.append(state)
                results.append('state')
                results.append(city_state_original)
        if scope == 'CountrySubregionRegion':
            country_subregion_region_original = \
                data.get(direction+"[CountrySubregionRegion]")
            country_subregion_region = encode(country_subregion_region_original)
            country = Country.objects.filter(name=country_subregion_region)
            if country:
                results.append(country[0])
                results.append("country")
                results.append(country_subregion_region_original)
            else:
                subregion = Subregion.objects.filter(
                    name=country_subregion_region)
                if subregion:
                    results.append(subregion[0])
                    results.append("subregion")
                    results.append(country_subregion_region_original)
                else:
                    region = Region.objects.filter(
                        name=country_subregion_region)
                    if region:
                        results.append(region[0])
                        results.append("region")
                        results.append(country_subregion_region_original)
        if not scope:
            results.append(None)
            results.append(None)
            results.append(None)
    return results[0],results[1],results[2],results[3],results[4],results[5]


def add_filter(alerts, from_value, from_scope, to_value, to_scope):
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
    return alerts

def create_alert_object(user_profile, from_value, from_scope, to_value,
                        to_scope):
    alert = Alert(user=user_profile)
    if from_scope == "region":
        alert.from_region = from_value
    if from_scope == "subregion":
        alert.from_subregion = from_value
    if from_scope == "country":
        alert.from_country = from_value
    if from_scope == "state":
        alert.from_state = from_value
    if from_scope == "city":
        alert.from_city = from_value
    if to_scope == "region":
        alert.to_region = to_value
    if to_scope == "subregion":
        alert.to_subregion = to_value
    if to_scope == "country":
        alert.to_country = to_value
    if to_scope == "state":
        alert.to_state = to_value
    if to_scope == "city":
        alert.to_city = to_value
    alert.from_keywords = from_value.searchable_keywords()
    alert.from_place_id = from_value.place_id
    if to_value and to_scope:
        alert.to_keywords = to_value.searchable_keywords()
        alert.to_place_id = to_value.place_id
    alert.save()
    return alert

@requires_login
def create_alert(request):
    if request.method == "POST":
        user_profile = UserProfile.objects.get(user=request.user)
        user_alerts = Alert.objects.filter(user=user_profile)
        count = user_alerts.count()
        max_alerts = 10
        if count >= max_alerts:
            error = "User has already created the maximum of {} alerts!".\
                format(max_alerts)
            return JsonResponse({"status": 'false', "message": error},
                status=500)
        data = request.POST
        from_value, from_scope, from_original_name, \
            to_value, to_scope, to_original_name = retrieve_place_object(data)
        if not from_value and not from_scope:
            error = "Must enter FROM criteria"
            if not to_value and not to_scope:
                error = "Must enter criteria"
            return JsonResponse({"status": 'false', "message": error},
                status=500)
        if (from_scope == 'city' and to_scope == "city") or \
            (from_scope == 'state' and to_scope == 'state'):
            if from_value == to_value:
                error = "Cannot have matching cities"
                return JsonResponse({"status": 'false', "message": error},
                    status=500)
        # Lastly, check to make sure this criteria doesn't exist already

        found = add_filter(user_alerts, from_value, from_scope, to_value,
                           to_scope)
        if found:
            error = "An alert with this criteria already exists"
            return JsonResponse({"status": 'false', "message": error},
                status=500)
        alert = create_alert_object(user_profile, from_value, from_scope,
                                    to_value, to_scope)
        new_dict = {}

        new_dict["from_value"] = from_original_name
        new_dict["id"] = alert.id
        new_dict["from_place_id"] =  from_value.place_id
        if not to_value and not to_scope:
            url = "/static/Flights140base/image/randompics/{}.jpg".format(randrange(1,51))
            new_dict["to_value"] = "Anywhere"
            new_dict["to_place_id"] = url
            new_dict["use_place_id"] = False
        else:
            new_dict["to_value"] = to_original_name
            new_dict["to_place_id"] = to_value.place_id
            new_dict["use_place_id"] = True
        return JsonResponse({
            'success': 'success',
            "status_code": 200,
            "data": new_dict})


@requires_login
def delete_alert(request):
    if request.method == "POST":
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            delete_id = request.POST.get("id")
            alert_to_delete = Alert.objects.get(id=delete_id, user=user_profile)
            if alert_to_delete:
                alert_to_delete.delete()
                new_dict = {"id": delete_id}
                return JsonResponse({
                    'success': 'success',
                    "status_code": 200,
                    "data": new_dict})
            else:
                error = "An error occurred.  Try again later"
                return JsonResponse({"status": 'false', "message": error},
                    status=500)
        except:
            error = "An error occurred.  Try again later"
            return JsonResponse({"status": 'false', "message": error},
                status=500)

@requires_login
def edit_user(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.is_ajax() and request.method == 'POST':
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        error = ""
        if email:
            email_error = mailgun_validate(email, initial=False)
            if email_error:
                error += "</br>{}".format(email_error)
            else:
                user_profile.email = email
        else:
            user_profile.email = ""
        if phone_number:
            phone_number_error = twilio_validate(phone_number, initial=False)
            if phone_number_error:
                error += "</br>{}".format(phone_number_error)
            else:
                user_profile.phone_number = phone_number
        else:
            user_profile.phone_number = ""
        if error:
            return JsonResponse({"status": 'false', "message": error},
                status=500)
        user_profile.save()
        return JsonResponse({'success': 'success', "status_code": 200})



@requires_login
def contact_form(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if request.is_ajax() and request.method == 'POST':
        message = request.POST.get("message")
        if message:
            new_message = ContactMessage(
                user=user_profile,
                message=message)
            new_message.save()
            return JsonResponse({'success': 'success', "status_code": 200})
    error = "An error occurred.  Try again later"
    return JsonResponse({"status": 'false', "message": error},
        status=500)


@requires_login
def delete_user(request):
    if request.method == 'POST':
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.user.delete()
            return HttpResponseRedirect(reverse('flights140base:login'))
        except:
            pass
    return HttpResponseRedirect(reverse('flights140base:login'))
