require([
    'jquery',
    'underscore',
    'splunkjs/mvc',
    'splunkjs/mvc/simplexml/ready!'
],
function(
    $,
    _,
    mvc
) {
    require(['splunkjs/ready!'], function(){
        function submit_and_update_url() {
            submitted_tokens.set(unsubmitted_tokens.toJSON());
                mvc.Components.get('url').saveOnlyWithPrefix('form\\.', unsubmitted_tokens.toJSON(), {
                replaceState: false
            });
        }

        var unsubmitted_tokens = mvc.Components.get('default');
        var submitted_tokens = mvc.Components.get('submitted');

        var calendarheatmap = mvc.Components.get("calendarheatmap");

        calendarheatmap.on("click", function(e) {
            var earliest = e.date.getTime() / 1000;
            var latest   = earliest + 60;

            var calendarheatmap_search = mvc.Components.get("calendarheatmap_search");
            var search = calendarheatmap_search.search.get("search");
            search = /^([^|]+)/.exec(search)[1].trim() + " sourcetype=" + e.series;

            var url = "/app/SplunkForNagios/search?earliest=" + earliest + "&latest=" + latest + "&q=" + encodeURIComponent(search);

            window.open(url);
        });
    });
});
