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
    function submit_and_update_url() {
        submitted_tokens.set(unsubmitted_tokens.toJSON());
            mvc.Components.get('url').saveOnlyWithPrefix('form\\.', unsubmitted_tokens.toJSON(), {
            replaceState: false
        });
    }

    var unsubmitted_tokens = mvc.Components.get('default');
    var submitted_tokens = mvc.Components.get('submitted');

    $("#input_term, #input_category").hide();

    require(['splunkjs/ready!'], function(){
        var bubblechart = mvc.Components.get("bubblechart");

        bubblechart.on("click", function(e) {
            // Remove quotes in the value for terms that are numbers like "192" since it'll break the search query of timechart.
            var name = e.name.replace(/"/g, '');
            var category = e.category;

            unsubmitted_tokens.set("form.term", name);
            unsubmitted_tokens.set("form.category", category);
            submit_and_update_url();
        });
    });
});
