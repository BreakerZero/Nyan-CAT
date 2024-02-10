var url  = "/projet/" + id + "/train";
window.addEventListener("beforeunload", function (e) {
    navigator.sendBeacon(url)
});