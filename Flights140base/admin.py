from __future__ import unicode_literals
from django.contrib import admin
from .models import UserProfile, Alert, TwitterAccount, Tweet, ContactMessage
# Register your models here.
from .models import Region, Subregion, Country, State, City

class UserProfileAdmin(admin.ModelAdmin):
    fields = ['user', 'email', 'phone_number']
    list_display = ('user', 'email', 'phone_number')


class AlertAdmin(admin.ModelAdmin):
    fields = ["user", "from_region", "from_subregion", "from_country",\
                "from_state", "from_city",\
                "to_region", "to_subregion", "to_country",\
                "to_state", "to_city"]
    list_display = ("user", "from_region", "from_subregion", "from_country",\
                    "from_state", "from_city",\
                    "to_region", "to_subregion", "to_country",\
                    "to_state", "to_city")

class ContactMessageAdmin(admin.ModelAdmin):
    fields = ["user", "message"]
    list_display = ["user", "message"]

class TwitterAccountAdmin(admin.ModelAdmin):
    fields = ["user_id", "full_name", "screen_name"]
    list_display = ("user_id", "full_name", "screen_name")


class TweetAdmin(admin.ModelAdmin):
    fields = ["tweet", "from_keywords", "to_keywords", "timestamp", "account"]
    list_display = ("tweet", "from_keywords", "to_keywords", "timestamp",\
                    "account")

class RegionAdmin(admin.ModelAdmin):
    fields = ["name", "plural_names", "additional_keywords", "abbreviations",\
              "place_id"]
    list_display = ("name", "plural_names", "additional_keywords",\
                    "abbreviations", "place_id")

class SubregionAdmin(admin.ModelAdmin):
    fields = ["name", "region", "plural_names", "additional_keywords",\
              "abbreviations", "place_id"]
    list_display = ("name", "region", "plural_names", "additional_keywords",\
                    "abbreviations", "place_id")

class CountryAdmin(admin.ModelAdmin):
    fields = ["name", "region", "subregion", "plural_names",\
              "additional_keywords", "abbreviations", "place_id"]
    list_display = ("name", "region", "subregion", "plural_names",\
                    "additional_keywords", "abbreviations", "place_id")

class StateAdmin(admin.ModelAdmin):
    fields = ["name", "region", "subregion", "country", "plural_names",\
              "additional_keywords", "abbreviations", "place_id"]
    list_display = ("name", "region", "subregion", "country", "plural_names",\
                    "additional_keywords", "abbreviations", "place_id")

class CityAdmin(admin.ModelAdmin):
    fields = ["name", "region", "subregion", "country", "state","plural_names",\
              "additional_keywords", "abbreviations", "iata", "place_id"]
    list_display = ("name", "region", "subregion", "country", "state",\
                    "plural_names", "additional_keywords", "abbreviations",\
                    "iata", "place_id")

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Alert, AlertAdmin)
admin.site.register(ContactMessage, ContactMessageAdmin)
admin.site.register(TwitterAccount, TwitterAccountAdmin)
admin.site.register(Tweet, TweetAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(Subregion, SubregionAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(State, StateAdmin)
admin.site.register(City, CityAdmin)
