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
            $(".content").css("visibility", "hidden");
            $("span").css("visibility", "hidden");
        },
        onUnload: function onUnload() {
            $(".content").css("visibility", "visible");
            $("span").css("visibility", "visible");
        },
        height: 300,
        width: 400,
        template: $('.learn_base').css("display", "").html()
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
