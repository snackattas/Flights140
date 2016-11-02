'use strict';

$(document).ready(function () {
    $('.tlt').textillate({
        in: {
            delayScale: 1
        }
    });
    var videoPlayer = document.getElementById("video");
    videoPlayer.onpause = function (e) {
        videoPlayer.play();
    };
    $('button').avgrund({
        onLoad: function onLoad() {
            console.log('here');
            $(".content").css("visibility", "hidden");
            $("span").css("visibility", "hidden");
        },
        onUnload: function onUnload() {
            $(".content").css("visibility", "visible");
            $("span").css("visibility", "visible");
        },
        height: 300,
        width: 400,
        template: "<p>Flights140 watches Twitter for flight deals, error fares, and flash flares so you'll know when deals you care about are tweeted about, at that instant!</p></br>How it works:<ol><li>Enter an origin and/or destination</li><li>Receive an email and/or text when there's a tweet about your criteria!</li><li>Buy your tickets and travel for cheap!</li></ol><br><p>This site is designed so you can find deals for those far-off destination you'd only travel to if you found a deal!</p>"
    });
    var timeout = function timeout() {
        setTimeout(function () {
            $('body').css({ "background-image": "none" });
            $('body').css({ "background-color": "#505050" });
            $("button").removeAttr("disabled");
        }, 1500);
    };
    $("button").attr("disabled", "");
    timeout();
});