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
        template: "<p>Flights140 tracks Twitter for airfare deals, error fares, and flash flares using a special algorithm so you will be instaneously alerted when the flight deals you care about are tweeted!</p></br>How it works:<ol><li>Enter your origin and/or destination.</li><li>Receive an alert (via email and/or text) when there is a tweet containing your  search criteria!</li><li>Buy your tickets and travel for cheap!</li></ol><br><p>This site is designed to find you airfare deals for those far-off destinations where you would only travel to if you found that perfect deal.</p>"
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
