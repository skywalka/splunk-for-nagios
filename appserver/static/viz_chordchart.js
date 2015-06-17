require([
    'jquery',
    'underscore',
    'splunkjs/mvc',
    'splunkjs/mvc/simplexml/ready!'
], function(
    $,
    _,
    mvc
) {
    function submit_and_update_url() {
        submitted_tokens.set(unsubmitted_tokens.toJSON());
        mvc.Components.get('url').saveOnlyWithPrefix('form\\.', unsubmitted_tokens.toJSON(), {
            replaceState: false
        });
    }

    $("#input_selected_country").hide();

    var unsubmitted_tokens = mvc.Components.get('default');
    var submitted_tokens = mvc.Components.get('submitted');

    require(['splunkjs/ready!'], function() {
        var chordchart = mvc.Components.get("chordchart");
        var piechart   = mvc.Components.get("piechart");

        chordchart.on("click", function(e) {
            unsubmitted_tokens.set("form.selected_country", e.name);
            submit_and_update_url();
        });

        chordchart.on("colors_ready", function() {
            var src_colors = chordchart.options.src_colors;
            // From {"Belgium":"#ff0000"} to {"Belgium":0xff0000}
            // Because SimpleXML only takes the latter format
            field_colors = JSON.stringify(src_colors).replace(/:"#/g, ":0x").replace(/(0x\w{6})"/g, "$1");

            piechart.getVisualization(function(viz) {
                viz.settings.set("charting.fieldColors", field_colors);
            });
        });
    });
});
