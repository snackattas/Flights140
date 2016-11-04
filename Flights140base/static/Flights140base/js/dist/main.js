'use strict';

// CSRF SETUP CODE
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === name + '=') {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method)
    );
}
$.ajaxSetup({
    beforeSend: function beforeSend(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            var csrftoken = getCookie('csrftoken');
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

var getJSON = function getJSON() {
    var allJSON;
    $.ajax({
        dataType: "json",
        url: "/static/Flights140base/js/JSON/placeList.JSON",
        async: false,
        success: function success(json) {
            allJSON = json;
        }
    });
    return allJSON;
};

var initializeDropdowns = function initializeDropdowns() {
    var directions = ["from", "to"];
    _.each(directions, function (direction) {
        $('.' + direction + '.dropdown').dropdown();
    });
};

var shortenSelectedAirportCodes = function shortenSelectedAirportCodes(allJSON, direction) {
    $('input[name=' + direction + ']').change(function () {
        var value = $('.' + direction + '.dropdown').dropdown("get value");
        var comma_count = (value.match(/,/g) || []).length;
        if (comma_count === 2) {
            var split = value.split(", ");
            var new_place = split[1] + ', ' + split[2];
            $('.' + direction + '.dropdown').dropdown("set selected", new_place);
        }
    });
};

var setDropdownValues = function setDropdownValues(allJSON) {
    var choices = _.map(allJSON, function (entry) {
        var comma_count = (entry.match(/,/g) || []).length;
        if (comma_count === 2) {
            return '<div class=\'item filtered\' data-value=\'' + entry + '\'></i>' + entry + '</div>';
        }
        return '<div class=\'item\' data-value=\'' + entry + '\'></i>' + entry + '</div>';
    });
    var directions = ['from', 'to'];
    _.each(directions, function (direction) {
        var dropdown_menu = '#' + direction;
        $(dropdown_menu).append(choices);
    });
};

var clearSelections = function clearSelections() {
    var directions = ['from', 'to'];
    _.each(directions, function (direction) {
        var dropdown_class = '.' + direction + '.selection.dropdown';
        $(dropdown_class).dropdown("clear");
    });
};

var setDeleteButtonAction = function setDeleteButtonAction(jQueryObjects) {
    jQueryObjects.click(function (object) {
        var id_to_delete = { id: $(object.currentTarget).attr("id") };
        $.ajax({
            url: "delete_alert/",
            type: "POST",
            dataType: 'json',
            traditional: true,
            data: id_to_delete,
            success: function success(json) {
                var deleted_id = json.data.id;
                $('#' + deleted_id).parent().remove();
                alertify.success("Alert removed!", "100ms");
                fadeOutCards(deleted_id);
            },
            error: function error(xhr, errmsg, err) {
                var error = xhr["responseJSON"]["message"];
                alertify.error(error, '1000ms');
            }
        });
    });
};

var createPost = function createPost(allJSON) {
    var max_alerts = 10;
    var from_place = $(".from.dropdown").dropdown("get value");
    var to_place = $(".to.dropdown").dropdown("get value");
    openEditAccountOnLoad();
    if (!from_place) {
        if (!to_place) {
            return;
        } else {
            return alertify.error("Must enter FROM criteria");
        };
    };
    if ($('.card').length >= max_alerts) {
        return alertify.error('User has already created the maximum of ' + max_alerts + ' alerts!');
    };
    var data = [from_place];
    if (to_place) {
        data.push(to_place);
    }
    data = _.map(data, function (place) {
        var comma_count = (place.match(/,/g) || []).length;
        if (comma_count === 0) {
            return { scope: 'CountrySubregionRegion',
                CountrySubregionRegion: place };
        }
        if (comma_count === 1) {
            var split = place.split(", ");
            return { scope: 'CityState', CityState: split[0], Country: split[1] };
        };
        if (comma_count === 2) {
            var split = place.split(", ");
            return { scope: 'CityState', CityState: split[1], Country: split[2] };
        }
    });
    if (to_place) {
        if (data[0].CityState && data[1].CityState) {
            if (data[0].CityState === data[1].CityState) {
                return alertify.error("Cannot have matching cities");
            };
        };
    };
    $.ajax({
        url: "create_alert/",
        type: "POST",
        traditional: false,
        dataType: 'json',
        data: { from: data[0], to: data[1] },
        success: function success(json) {
            if (json.data.use_place_id === false) {
                json.data.use_place_id = "False";
            };
            var string = '<div class=\'card\'><div class=\'content\'><div class=\'header\'><div class=\'container\'><div class=\'from_place place\' data-placeid=\'' + json.data.from_place_id + '\'></div><div class=\'flicker\'>' + json.data.from_value + '</div></div><div class=\'ui horizontal divider\'>to</div><div class=\'container\'><div class=\'to_place place\' data-placeid=\'' + json.data.to_place_id + '\' data-useplaceid=\'' + json.data.use_place_id + '\'></div><div class=\'flicker\'>' + json.data.to_value + '</div></div></div><div class=\'description\' align=\'right\'>added <i>just now</i></div></div><div class=\'ui bottom attached button\' id=' + json.data.id + '><input type=\'hidden\'><i class=\'remove icon\'></i>Remove Alert</div></div>';
            $(".ui.cards").prepend(string);
            setDeleteButtonAction($('#' + json.data.id));
            setBackgroundColor($(".card:first"));
            addPics($(".card:first"));
            alertify.success("Alert added!", "500ms");
            // styleCards($(".card")[0]);
            clearSelections();
            fadeInCards($(".card"));
        },
        error: function error(xhr, errmsg, err) {
            var error = xhr["responseJSON"]["message"];
            if (error) {
                alertify.error(error, '1000ms');
            } else {
                var error = "Something went wrong. Click 'Restore selections' and try again";
                alertify.error(error, '1000ms');
            }
        }
    });
};

// TRANISITIONS
var airportFlicker = function airportFlicker(cards) {
    _.each(cards, function (card) {
        _.each($(card).find(".flicker"), function (object) {
            var data_value = $(object).text();
            $(object).airport([data_value], { transition_speed: 1500, loop: false });
            setTimeout(function () {
                $(object).text(data_value);
            }, 10000);
        });
        var time = $(card).find(".description");
        $(time).removeClass("animated");
        $(time).removeClass("flash");
        $(time).css("visibility", "hidden");
        setTimeout(function () {
            $(time).css("visibility", "visible").addClass("animated flash");
        }, 2000);
    });
};

var fadeInCards = function fadeInCards(jQueryObjects) {
    _.each(jQueryObjects, function (object) {
        $(object).css("visibility", "hidden");
    });
    var sleep_value = 0;
    _.each(jQueryObjects, function (object) {
        setTimeout(function () {
            $(object).css("visibility", "visible").addClass("animated fadeInLeft");
        }, sleep_value);
        sleep_value += 75;
    });
    setTimeout(function () {
        _.each(jQueryObjects, function (object) {
            $(object).removeClass("animated");
            $(object).removeClass("fadeInLeft");
        });
    }, 2000);
};

var fadeOutCards = function fadeOutCards(id_to_delete) {
    var cards_to_fade_out = [];
    _.each($(".ui.bottom.attached.button"), function (object) {
        if (id_to_delete > object.id) {
            var card_to_fade_out = $('#' + object.id).parent();
            cards_to_fade_out.push(card_to_fade_out);
        };
    });
    _.each(cards_to_fade_out, function (object) {
        $(object).css("visibility", "hidden");
    });
    var sleep_value = 0;
    _.each(cards_to_fade_out, function (object) {
        setTimeout(function () {
            $(object).css("visibility", "visible").addClass("animated fadeInRight");
        }, sleep_value);
        sleep_value += 75;
    });
    setTimeout(function () {
        _.each(cards_to_fade_out, function (object) {
            $(object).removeClass("animated");
            $(object).removeClass("fadeInRight");
        });
    }, 2000);
};

//Set background colors of cards
var setBackgroundColor = function setBackgroundColor(cards) {
    var background_colors = ["#966FD6", "#779ECB"];
    _.each(cards, function (card) {
        var color = 0;
        _.each($(card).find(".container"), function (container) {
            $(container).css("background-color", background_colors[color]);
            color += 1;
        });
    });
};

// CODE TO LOAD PHOTOS
var initMap = function initMap() {
    var service = new google.maps.places.PlacesService($("#map")[0]);
    return service;
};

var addPicsInnerLoop = function addPicsInnerLoop(map, card) {
    _.each($(card).find(".place"), function (object) {
        var not_anywhere = true;
        if ($(object).hasClass("to_place")) {
            if ($(object).attr("data-useplaceid") === "False") {
                var url = $(object).attr("data-placeid");
                // $(object).append(`<img src="${url}">`)
                $(object).css("background-image", 'url("' + url + '")').addClass("animated fadeInRight");
                not_anywhere = false;
            }
        }
        if (not_anywhere) {
            var getPicUrl = function getPicUrl(place, status) {
                if (status === "OK") {
                    var url = place.photos[0].getUrl({ "maxWidth": 375, "maxHeight": 150 });
                    $(object).css("background-image", 'url("' + url + '")').addClass("animated fadeInRight");
                } else {
                    var random = _.random(1, 50);
                    var url = '/static/Flights140base/image/randompics/' + random + '.jpg';
                    $(object).css("background-image", 'url("' + url + '")').addClass("animated fadeInRight");
                };
            };
            var request = { placeId: $(object).attr("data-placeid") };
            map.getDetails(request, getPicUrl);
        }
    });
};

var addPicsOuterLoop = function addPicsOuterLoop(map, cards) {
    _.each(cards, function (card) {
        addPicsInnerLoop(map, card);
    });
};

var addPics = function addPics(cards_init) {
    var map = initMap();
    var delay = 0;
    var delay_increment = 3000;
    var load_this_many_cards = 3;
    var groups = _.chain(cards_init).groupBy(function (element, index) {
        return Math.floor(index / load_this_many_cards);
    }).toArray().value();
    _.each(groups, function (cards) {
        setTimeout(function () {
            addPicsOuterLoop(map, cards);
        }, delay);
        delay += delay_increment;
    });
};

// POPUP MODAL FORM CODE
var createContactForm = function createContactForm() {
    var contact_message = $("textarea:last").val();
    if (!contact_message) {
        removeAvgrund();
        return;
    };
    contact_message = { message: contact_message };
    $.ajax({
        url: "contact_form/",
        type: "POST",
        traditional: false,
        dataType: 'json',
        data: contact_message,
        success: function success(json) {
            alertify.success("Message sent!", '1000ms');
            removeAvgrund();
        },
        error: function error(xhr, errmsg, err) {
            var error = xhr["responseJSON"]["message"];
            if (error) {
                alertify.error(error, '1000ms');
                removeAvgrund();
            } else {
                var error = "Something went wrong.  Reload the page and try again";
                alertify.error(error, '1000ms');
                removeAvgrund();
            };
        }
    });
};

var editUserForm = function editUserForm() {
    var old_email = $("input[name=email]:first").val();
    var old_phone_number = $("input[name=phone_number]:first").val();
    var email = $("input[name=email]:last").val();
    var phone_number = $("input[name=phone_number]:last").val();

    if (!email && !phone_number) {
        var error = "</br>User must enter at least an email or phone number";
        errorText(error);
        return;
    }

    if (old_email == email && old_phone_number == phone_number) {
        removeAvgrund();
        return;
    }
    var user_details = {};
    if (email) {
        user_details.email = email;
    }
    if (phone_number) {
        user_details.phone_number = phone_number;
    }
    $.ajax({
        url: "edit_user/",
        type: "POST",
        traditional: false,
        dataType: 'json',
        data: user_details,
        success: function success(json) {
            $("input[name=email]:first").val(email);
            $("input[name=phone_number]:first").val(phone_number);

            alertify.success("Contact edited!", '1000ms');
            removeAvgrund();
        },
        error: function error(xhr, errmsg, err) {
            var error = xhr["responseJSON"]["message"];
            errorText(error);
        }
    });
};

var errorText = function errorText(error) {
    $('.error_msg:last').html(error).addClass("animated fadeIn");
    setTimeout(function () {
        $('.error_msg:last').addClass("fadeOut");
        setTimeout(function () {
            $('.error_msg:last').removeClass("animated");
            $('.error_msg:last').removeClass("fadeIn");
            $('.error_msg:last').removeClass("fadeOut");
            $('.error_msg:last').html("");
        }, 800);
    }, 3000);
};

var cancelEditUser = function cancelEditUser() {
    var email = $("input[name=email]:last").val();
    var phone_number = $("input[name=phone_number]:last").val();

    if (!email && !phone_number) {
        var error = "</br>User must enter at least an email or phone number";
        errorText(error);
        return;
    }
    return removeAvgrund();
};

// CODE TO REMOVE AVGRUND POPIN THROUGH A CANCEL BUTTON AND NOT BY CLICKING OUTSIDE
var removeAvgrund = function removeAvgrund() {
    $("textarea").val("");
    $("body").removeClass("avgrund-active");
    $(".avgrund-popin").remove();
};

// LINKING ALL THE MENU BUTTONS TO AVGRUND POPINS
$('.contact').avgrund({
    height: 350,
    width: 400,
    template: $(".contact_form_base").css("display", "").html()
});

$('.twitter_accounts_base').avgrund({
    height: 350,
    width: 400,
    template: $('.twitter_accounts_base').css("display", "").html()
});

$('.edit_account').avgrund({
    onLoad: function onLoad() {
        setTimeout(function () {
            $("input[name=phone_number]:last").val($("input[name=phone_number]:first").val());
            $("input[name=email]:last").val($("input[name=email]:first").val());
        }, 30);
    },
    onUnload: function onUnload() {
        setTimeout(function () {
            openEditAccountOnLoad();
        }, 600);
    },
    height: 350,
    width: 400,
    template: $('.edit_account_base').css("display", "").html()
});

$('.delete_account_base').avgrund({
    height: 350,
    width: 400,
    template: $('.delete_account_base').css("display", "").html()
});

$('.how_it_works').avgrund({
    height: 350,
    width: 400,
    template: $('.how_it_works_base').css("display", "").html()
});

$('.donate').avgrund({
    height: 350,
    width: 400,
    template: $('.donate_base').css("display", "").html()
});
$('.privacy_policy').avgrund({
    height: 350,
    width: 400,
    template: $('.privacy_policy_base').css("display", "").html()
});

// IF USER DOESN'T HAVE ACCOUNT INFOMATION IN THE SYSTEM, EDIT ACCOUNT WILL POPUP ON PAGE LOAD
var openEditAccountOnLoad = function openEditAccountOnLoad() {
    var email = $("input[name=email]").val();
    var phone_number = $("input[name=phone_number]").val();
    if (!email && !phone_number) {
        $('.edit_account').click();
    };
};

$(document).ready(function () {
    // ROLLIN OF WELCOME MESSAGE
    setTimeout(function () {
        $('.tlt').textillate({
            in: {
                effect: 'fadeInLeftBig',
                delayScale: 1
            }
        });
    }, 200);
    // IF NO ACCOUNT INFO IN SYSTEM OPEN EDIT ACCOUNT ON PAGE LOAD
    openEditAccountOnLoad();
    // CARD EFFECTS
    setBackgroundColor($(".card"));
    airportFlicker($('.card'));
    fadeInCards($(".card"));
    addPics($(".card"));
    // Initialize dropdowns
    var allJSON = getJSON();
    initializeDropdowns();
    setDropdownValues(allJSON);
    // Set up button events
    setDeleteButtonAction($(".ui.bottom.attached.button"));
    $('#restore').on('click', function () {
        clearSelections(allJSON);
    });
    // Prevent defaults for ajax requests
    $('#post_alert').submit(function (event) {
        event.preventDefault();
        createPost(allJSON);
    });
    $(".delete_alert").submit(function (event) {
        event.preventDefault();
    });
    $('#contact_form_submit').submit(function (event) {
        event.preventDefault();
        createContactForm();
    });
    $("#edit_user_submit").submit(function (event) {
        event.preventDefault();
        editUserForm();
    });
    // IF USER VIEWS DROPDOWN LIST WITHOUT TYPING, THEY SHOULDN'T SEE THE IATA CODES.  ONLY SHOULD SEE ACTUAL PLACES.  IATA CODES AVAILABLE WHEN DOING TYPING INPUT
    var directions = ['from', 'to'];
    _.each(directions, function (direction) {
        shortenSelectedAirportCodes(allJSON, direction);
    });
});
