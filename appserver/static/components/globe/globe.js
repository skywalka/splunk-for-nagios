define(function(require, exports, module) {
    var Detector = require("../globe/Detector");
    var DAT = require("../globe/DAT");
    var TWEEN = require("../globe/Tween");

    var THREE = require("three");

    var _ = require('underscore');
    var SimpleSplunkView = require("splunkjs/mvc/simplesplunkview");
    var SplunkUtil = require('splunk.util');

    var Globe = SimpleSplunkView.extend({
        className: "splunk-toolkit-globe",
        options: {
            "managerid": null,
            "data": "preview",
            "lat_field": "latitude",
            "lon_field": "longitude",
            "group_by_field": null,
            "world_image_path": "app/custom_vizs/components/globe/world_black.jpg",
            "star_field": true,
            "height": 800,
            "spin_speed": 0
        },
        output_mode: "json",
        initialize: function() {
            SimpleSplunkView.prototype.initialize.apply(this, arguments);
            // What does this do?
            //this.settings.enablePush("value");
            // in the case that any options are changed, it will dynamically update
            // without having to refresh. copy the following line for whichever field
            // you'd like dynamic updating on
            this.settings.on("change:lat_field",      this.render, this);
            this.settings.on("change:lon_field",      this.render, this);
            this.settings.on("change:group_by_field", this.render, this);
            // Set up resize callback. The first argument is a this
            // pointer which gets passed into the callback event
            //$(window).resize(this, _.debounce(this._handleResize, 20));
        },
        //_handleResize: function(e) {
        //    // e.data is the this pointer passed to the callback.
        //    // here it refers to this object and we call render()
        //    e.data.render();
        //},
        createView: function() {
            var that = this;
            var height = parseInt(this.settings.get("height") || that.$el.height());
            var spin_speed = parseFloat(this.settings.get("spin_speed"));

            // clearing all prior junk from the view (eg. 'waiting for data...')
            that.$el.html("");

            that.$el.css({
                "color": "rgb(0, 0, 0)",
                "height": height
            });

            if(!Detector.webgl){
                Detector.addGetWebGLMessage();
            } else {
                return new DAT.Globe(that.el, {
                    img_path: SplunkUtil.make_url("/static/" + this.settings.get("world_image_path")),
                    star_field: this.settings.get("star_field"),
                    star_field_path: SplunkUtil.make_url("/static/app/custom_vizs/components/globe/star_field.png"),
                    spin_speed: spin_speed
                });
            }
        },
        // making the data look how we want it to for updateView to do its job
        formatData: function(data) {
            // getting settings
            var lat_field      = this.settings.get('lat_field');
            var lon_field      = this.settings.get('lon_field');
            var group_by_field = this.settings.get('group_by_field');

            var max_value = 0;

            var group_by_values = {};

            if(group_by_field) {
                var i = 0;

                values = _(data)
                    .chain()
                    .uniq(function(point) {
                        return point[group_by_field];
                    })
                    .map(function(o) {
                        return o[group_by_field];
                    })
                    .each(function(v) {
                        group_by_values[v] = i;
                        i++;
                    });
            }

            var feathered_data = _(data)
                .chain()
                .groupBy(function(point) {
                    var zipped = Math.round(point[lat_field]) + "," + Math.round(point[lon_field]);

                    // We eventually want the data to be formatted like
                    // [lat, lon, magnitude, lat, long, magnitude, ...]
                    // or
                    // [lat, lon, magnitude, group_1, lat, long, magnitude, group_2, ...]
                    // and group_* can only be integers
                    zipped += group_by_field ? "," + group_by_values[point[group_by_field]] : "";

                    return zipped;
                })
                .map(function(points, zipped) {
                    var re;

                    re = group_by_field ? /([^,]+),([^,]+),(\d+)/ : /([^,]+),(.+)/;
                    var lat = parseInt(re.exec(zipped)[1]);
                    var lon = parseInt(re.exec(zipped)[2]);
                    var group = group_by_field ? parseInt(re.exec(zipped)[3]) : null;

                    var magnitude = points.length;

                    max_value = Math.max(max_value, magnitude);

                    var point = [lat, lon, magnitude];

                    if(group_by_field) {
                        point.push(group);
                    }

                    return point;
                })
                .flatten()
                .value();

            var normalized_feathered_data = _(feathered_data).map(function(v, i) {
                if(
                    group_by_field && (i + 2) % 4 === 0 ||
                    !group_by_field && (i + 1) % 3 === 0
                ) {
                    // Normalized value between 0 and 1
                    v = v / max_value;
                }

                return v;
            });

            return normalized_feathered_data;
        },
        updateView: function(globe, data) {
            var group_by_field = this.settings.get('group_by_field');

            TWEEN.start();
            globe.removeAllPoints();
            if(group_by_field) {
                globe.addData(data, {format: 'legend', name: 'results', animated: false});
            }
            else {
                globe.addData(data, {format: 'magnitude', name: 'results', animated: false});
            }
            globe.createPoints();
            globe.animate();
        },
        render: function () {
            this.$el.height(this.settings.get('height'));
            return SimpleSplunkView.prototype.render.call(this);
        }
    });
    return Globe;
});
