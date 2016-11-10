"""views.py - Contains the views for Flights140. The two main views are login and main.  The rest of the views are designed for ajax calls"""

from django.contrib.auth.models import User
from django.http import JsonResponse, Http404
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, reverse, render_to_response

from .model_helpers import retrieve_random_image
from .utilities import mailgun_validate, twilio_validate, encode, chunks
from .view_helper import get_name, parse_ajax, does_alert_exist,\
    create_alert_object
from .models import UserProfile, Alert, ContactMessage, TwitterAccount,\
    Region, Subregion, Country, State, City

import json
import arrow
import dateutil.parser
from functools import wraps
from random import randrange
from collections import namedtuple

def requires_login(function):
    """This is a decorator that checks the request.user that is passed in by python social auth processes to confirm that python social auth worked.  If python social auth processes are not cleared, the decorator redirects to the login page."""

    @wraps(function)
    def decorated_function(*args, **kwargs):
        request = args[0]
        if not request.user or request.user.is_anonymous:
            return HttpResponseRedirect(reverse('flights140base:login'))
        else:
            return function(*args, **kwargs)
    return decorated_function


def login(request):
    """The view for the login page"""

    # If user is already logged in by python social auth, redirect to the main view
    try:
        if request.user and not request.user.is_anonymous:
            context = RequestContext(request,
                                    {'request': request,
                                     'user': request.user})
            return HttpResponseRedirect(reverse('flights140base:main'),
                                        context)
        else:
            # This is the html for the learn about flights140 button
            learn = render_to_string("Flights140base/learnAboutFlights140.html")
            context = RequestContext(request,
                                    {'request': request,
                                     'learn': learn})
            return render_to_response('Flights140base/login.html',
                                      context=context)
    except:
        learn = render_to_string("Flights140base/learnAboutFlights140.html")
        context = RequestContext(request,
                                {'request': request,
                                 'learn': learn})
        return render_to_response('Flights140base/login.html', context=context)


@requires_login
def main(request):
    """This is the main view of Flights140"""

    # This checks if there is a user profile object already created for this user.  If there isn't, it's created here.
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

    # This returns the alerts attached to this user
    alerts = Alert.objects.filter(user=user_profile)
    # We create an alerts_tuple to retrieve only the necessary info from the alert to pass to the template.  No need to pass the entire alert objects
    alert_tuple = namedtuple("alert_tuple", "from_name from_place_id"\
                             " to_name to_place_id use_place_id time id")
    html_alerts = []
    for alert in alerts:
        alert_id = alert.id
        from_name = alert.from_name()
        from_place_id = alert.from_place_id()
        to_name = alert.to_name()
        to_place_id = alert.to_place_id()
        use_place_id = alert.use_place_id()
        time = arrow.get(alert.timestamp).humanize()

        html_alert = alert_tuple(
            from_name=from_name,
            from_place_id=from_place_id,
            to_name=to_name,
            to_place_id=to_place_id,
            use_place_id=use_place_id,
            time=time,
            id=alert_id)
        html_alerts.append(html_alert)

    # This section prepares all the html templates that are used in the modals
    donate = render_to_string("Flights140base/donate.html")
    privacy_policy = render_to_string("Flights140base/disclaimer.html")
    contact_form = render_to_string("Flights140base/contactForm.html")
    how_it_works_form = render_to_string("Flights140base/howItWorks.html")

    email = user_profile.email
    phone_number = user_profile.phone_number
    edit_account_form = render_to_string(
        template_name="Flights140base/editAccount.html",
        context={'email': email, 'phone_number': phone_number})

    twitter_accounts = TwitterAccount.objects.all()
    twitter_account_chunks = chunks(twitter_accounts, 5)
    twitter_accounts_form = render_to_string(
        template_name="Flights140base/twitterAccounts.html",
        context={'twitter_account_chunks':twitter_account_chunks})

    name = get_name(user_profile)
    delete_account_form = render_to_string(request=request,
        template_name="Flights140base/deleteAccount.html",
        context={'name': name})

    directions = ["from", "to"] # This is a variable for the html template
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
    return render_to_response(
        template_name='Flights140base/main.html', context=context)

@requires_login
def create_alert(request):
    """This view is called via ajax and creates alert objects."""
    if request.is_ajax() and request.method == "POST":
        user_profile = UserProfile.objects.get(user=request.user)
        alerts = Alert.objects.filter(user=user_profile)
        alerts_count = alerts.count()
        max_alerts = 10
        if alerts_count >= max_alerts:
            error = "User has already created the maximum of {} alerts!".\
                format(max_alerts)
            return JsonResponse({"status": 'false', "message": error},
                status=500)

        data = request.POST
        from_tuple, to_tuple = parse_ajax(data)

        if not from_tuple.scope:
            error = "Must enter FROM criteria"
            if not to_tuple.scope:
                error = "Must enter criteria"
            return JsonResponse({"status": 'false', "message": error},
                status=500)

        if (from_tuple.scope == 'city' and to_tuple.scope == "city") or \
            (from_tuple.scope == 'state' and to_tuple.scope == 'state'):
            if from_tuple.value == to_tuple.value:
                error = "Cannot have matching cities"
                return JsonResponse({"status": 'false', "message": error},
                    status=500)

        # Lastly, check to make sure this criteria doesn't exist already
        found = does_alert_exist(alerts, from_tuple.value, from_tuple.scope,
                                 to_tuple.value, to_tuple.scope)
        if found:
            error = "An alert with this criteria already exists"
            return JsonResponse({"status": 'false', "message": error},
                status=500)

        alert = create_alert_object(user_profile, from_tuple.value,
            from_tuple.scope, to_tuple.value, to_tuple.scope)
        # Now that the alert has been created in the database, need to send back a dictionary with relevant information to the client
        new_dict = {}
        new_dict["from_value"] = from_tuple.original_name
        new_dict["id"] = alert.id # Need the alert's id for easy deletion
        new_dict["from_place_id"] =  alert.from_where().place_id
        # If the to field doesn't exist, send a random image url and tell the client not to use the place_id to find a photo
        if not to_tuple.scope:
            new_dict["to_value"] = "Anywhere"
            new_dict["to_place_id"] = retrieve_random_image()
            new_dict["use_place_id"] = False
        else:
            new_dict["to_value"] = to_tuple.original_name
            new_dict["to_place_id"] = alert.to_where().place_id
            new_dict["use_place_id"] = True
        return JsonResponse({
            'success': 'success',
            "status_code": 200,
            "data": new_dict})
    return HttpResponseRedirect(reverse('flights140base:login'))

@requires_login
def delete_alert(request):
    """This is the ajax view that deletes alerts by passing the alert id.  The action comes from clicking the 'Remove Alert' button in a card"""
    if request.is_ajax() and request.method == "POST":
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
    return HttpResponseRedirect(reverse('flights140base:login'))

@requires_login
def edit_user(request):
    """This is the ajax view that enables a user to edit their account by clicking submit in the 'Edit Contant' modal.  """
    if request.is_ajax() and request.method == 'POST':
        user_profile = UserProfile.objects.get(user=request.user)
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        error = ""
        if email:
            email_error = mailgun_validate(email)
            if email_error:
                error += "</br>{}".format(email_error)
            else:
                user_profile.email = email
        else:
            user_profile.email = ""
        if phone_number:
            phone_number_error = twilio_validate(phone_number)
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
    return HttpResponseRedirect(reverse('flights140base:login'))

@requires_login
def contact_form(request):
    """This is the ajax view that stores a contact message from the contact modal"""
    if request.is_ajax() and request.method == 'POST':
        user_profile = UserProfile.objects.get(user=request.user)
        message = request.POST.get("message")
        if message:
            new_message = ContactMessage(
                user=user_profile,
                message=message)
            new_message.save()
            return JsonResponse({'success': 'success', "status_code": 200})
    return HttpResponseRedirect(reverse('flights140base:login'))


@requires_login
def delete_user(request):
    """This is the ajax view that deletes a user's python social auth user, userprofile, and all associated alerts"""
    if request.method == 'POST':
        try:
            user_profile = UserProfile.objects.get(user=request.user)
            user_profile.user.delete()
            return HttpResponseRedirect(reverse('flights140base:login'))
        except:
            pass
    return HttpResponseRedirect(reverse('flights140base:login'))


@requires_login
def redirect_to_main(request):
    try:
        return HttpResponseRedirect(reverse('flights140base:main'))
    except:
        raise Http404("Sorry. Try reloading the page?")

@requires_login
def view404():
    try:
        return HttpResponseRedirect(reverse('flights140base:main'))
    except:
        raise Http404("Sorry. Try reloading the page?")
