// Boxplot D3.js code taken and modified from http://bl.ocks.org/jensgrubert/7789216 by Jens Grubert

define(function(require, exports, module) {
    var d3 = require("../d3/d3");
    var box = require("./d3.box");
    var SimpleSplunkView = require("splunkjs/mvc/simplesplunkview");
    var _ = require("underscore");
    require("css!./boxplot.css");

    var BoxPlot = SimpleSplunkView.extend({
        className: "splunk-toolkit-box-plot",
        options: {
            "managerid": null,
            "data": "preview",
            "height": 400,
            "fill_color": "#d62728",
            "x_axis_label": "",
            "y_axis_label": ""
        },
        output_mode: "json",
        initialize: function() {
            SimpleSplunkView.prototype.initialize.apply(this, arguments);

            $(window).resize(this, _.debounce(this._handleResize, 20));
        },
        _handleResize: function(e) {
            // e.data is the this pointer passed to the callback.
            // here it refers to this object and we call render()
            e.data.render();
        },
        createView: function() {
            return true;
        },
        // Making the data look how we want it to for updateView to do its job
        formatData: function(data) {
            var formatted_data = [];
            var headers;

            if(typeof this.options.group_by === "undefined") {
                headers = _(data[0]).keys();
                _(headers).each(function(header, i) {
                    if(header === "_span") return true;

                    formatted_data[i] = [];
                    formatted_data[i][0] = header;
                    formatted_data[i][1] = _(data).chain().pluck(header).map(function(v) { return parseFloat(v); }).value();
                });
            }
            else {
                var group_by_field = this.options.group_by;
                var value_field = _(data[0]).chain().keys().difference(group_by_field).value()[0];

                var grouped_data = _(data).groupBy(function(o) {
                    return o[group_by_field];
                });

                headers = _(grouped_data).keys().sort();

                _(headers).each(function(header, i) {
                    formatted_data[i] = [];
                    formatted_data[i][0] = header;
                    formatted_data[i][1] = _(grouped_data[header]).chain().pluck(value_field).map(function(v) { return parseFloat(v); }).value();
                });
            }

            // Hardcoded data to compare with http://bl.ocks.org/jensgrubert/7789216
            //formatted_data = [[], [], [], []];

            //formatted_data[0][0] = "Q1";
            //formatted_data[1][0] = "Q2";
            //formatted_data[2][0] = "Q3";
            //formatted_data[3][0] = "Q4";

            //formatted_data[0][1] = [20000, 9879, 5070, 7343, 9136, 7943, 10546, 9385, 8669, 4000];
            //formatted_data[1][1] = [15000, 9323, 9395, 8675, 5354, 6725, 10899, 9365, 8238, 7446];
            //formatted_data[2][1] = [8000, 3294, 17633, 12121, 4319, 18712, 17270, 13676, 6587, 16754];
            //formatted_data[3][1] = [20000, 5629, 5752, 7557, 5125, 5116, 5828, 6014, 5995, 8905];

            // using an array of arrays with
            // data[n][2]
            // where n = number of columns in the csv file
            // data[i][0] = name of the ith column
            // data[i][1] = array of values of ith column

            return formatted_data; // this is passed into updateView as 'data'
        },
        updateView: function(viz, data) {
            var that = this;

            that.$el.html("");

            var margin = {
                "top": 10,
                "right": 50,
                "bottom": 70,
                "left": 50
            };
            var width = that.$el.width() - margin.left - margin.right;
            var height = that.options.height - margin.top - margin.bottom;

            var min = _(data).chain().flatten().min().value();
            var max = _(data).chain().flatten().max().value();

            var chart = d3.box()
            .whiskers(iqr(1.5))
            .height(height)
            .domain([min, max])
            .showLabels(true);

            var svg = d3.select(that.el).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .attr("class", "box")
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            // the x-axis
            var x = d3.scale.ordinal()
            .domain(data.map(function(d) {
                return d[0];
            }))
            .rangeRoundBands([0, width], 0.7, 0.3);

            var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom");

            // the y-axis
            var y = d3.scale.linear()
            .domain([min, max])
            .range([height + margin.top, 0 + margin.top]);

            var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left");

            // draw the boxplots
            svg.selectAll(".box")
            .data(data)
            .enter().append("g")
            .attr("transform", function(d) {
                return "translate(" + x(d[0]) + "," + margin.top + ")";
            })
            .call(chart.width(x.rangeBand()));

            // draw y axis
            svg.append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text") // and text1
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .style("font-size", "16px")
            .text(that.options.y_axis_label);

            // draw x axis
            svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + (height + margin.top + 10) + ")")
            .call(xAxis)
            .append("text") // text label for the x axis
            .attr("x", (width / 2))
            .attr("y", 25)
            .attr("dy", ".71em")
            .style("text-anchor", "middle")
            .style("font-size", "16px")
            .text(that.options.x_axis_label);

            $(".box line, .box rect, .box circle").css("fill", that.options.fill_color);
            $(".box .outlier").css("fill", "none");

            // Returns a function to compute the interquartile range.
            function iqr(k) {
                return function(d, i) {
                    var q1 = d.quartiles[0],
                    q3 = d.quartiles[2],
                    iqr = (q3 - q1) * k,
                    i = -1,
                    j = d.length;
                    while (d[++i] < q1 - iqr)
                        ;
                    while (d[--j] > q3 + iqr)
                        ;
                    return [i, j];
                };
            }
        }
    });
    return BoxPlot;
});
