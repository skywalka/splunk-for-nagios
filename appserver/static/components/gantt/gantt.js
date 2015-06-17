// Gantt Chart
// this displays information as a gantt chart

define(function(require, exports, module) {

    var _ = require('underscore');
    var d3 = require("../d3/d3");
    var d3tip = require("./d3.tip");
    var SimpleSplunkView = require("splunkjs/mvc/simplesplunkview");
    var Drilldown = require('splunkjs/mvc/drilldown');
    var TokenUtils = require('splunkjs/mvc/tokenutils');
    var ResultsLinkView = require("splunkjs/mvc/resultslinkview");
    var mvc = require("splunkjs/mvc");

    // Try to load this module (needed for 6.0 and 6.1 backwards compatibility)
    var ReportModel;
    require(['models/Report'], function(model) { ReportModel=model;}, function() { ReportModel=false;});

    require("css!./gantt.css");

    var margin = {top: 10, right: 10, bottom: 10, left: 10};

    _cleanClass = function(n) {
        return n.replace(/[^A-Za-z0-9\-\_]/g, "_")+"-"+n.split("").reduce(function(a,b){a=((a<<5)-a)+b.charCodeAt(0);return a&a},0);
    }

    var GanttChart = SimpleSplunkView.extend({

        className: "custom-ganttchart",

        options: {
            managerid: null,
            data: "preview",
            startField: null,
            endField: null,
            durationField: null,
            categoryLabel: "Category",
            categoryField: null,
            categorySearch: null,
            seriesLabel: "Series",
            seriesField: null,
            extrasField: null,
            drilldownField: null,
            highlightField: null,
            showLegend: "true",
            compact: "false"
        },

        output_mode: "json",

        events: {
            'click': function(e) {
                e.preventDefault();
                if (this.settings.get('tokenName') && this.settings.get('tokenField')) {
                    var data = $(e.target).data('raw');
                    var unsubmittedTokens = mvc.Components.getInstance('default');
                    var submittedTokens = mvc.Components.getInstance('submitted');

                    unsubmittedTokens.set(this.settings.get('tokenName'), data[this.settings.get('tokenField')]);
                    submittedTokens.set(unsubmittedTokens.toJSON());

                    // The chart will be lost when the HTML block gets updated, so let's try to get it back
                    require("splunkjs/ready")();
                } else if (this.settings.get('drilldownSearch')) {
                    // Cook our own drilldown search
                    var search = this.settings.get('drilldownSearch');
                    var data   = $(e.target).data('raw');

                    search   = TokenUtils.replaceTokenNames(search, data);
                    earliest = parseInt($.trim($(e.target).data('time')))-1;
                    latest   = earliest + parseInt($.trim($(e.target).data('span')))+2;

                    Drilldown.redirectToSearchPage({
                        q: search,
                        earliest: earliest,
                        latest: latest,
                    }, false);
                } else {
                    if (this.settings.get('drilldownField')) {
                        // If we were given a drilldownField, use it
                        var data = {
                            name:  this.settings.get('drilldownField'),
                            value: $.trim($(e.target).data('field'))
                        }
                    } else {
                        // otherwise, drill down by time
                        var data = {
                            name: '_time',
                            _span: parseInt($.trim($(e.target).data('span')))+2,
                            value: parseInt($.trim($(e.target).data('time')))-1
                        }
                    }
                    Drilldown.autoDrilldown(data, this.manager, {drilldownType: 'all'});
                }
            }
        },

        initialize: function() {
            SimpleSplunkView.prototype.initialize.apply(this, arguments);

            this.settings.enablePush("value");

            this.settings.on("change:categoryLabel",  this.render, this);
            this.settings.on("change:categoryField",  this.render, this);
            this.settings.on("change:categorySearch", this.render, this);
            this.settings.on("change:seriesLabel",    this.render, this);
            this.settings.on("change:seriesField",    this.render, this);
            this.settings.on("change:extrasField",    this.render, this);
            this.settings.on("change:drilldownField", this.render, this);
            this.settings.on("change:highlightField", this.render, this);
            this.settings.on("change:showLegend",     this.render, this);
            this.settings.on("change:compact",        this.render, this);

            var unsubmittedTokens = mvc.Components.getInstance('default');
            unsubmittedTokens.on("change", function() {
                // The chart will be lost when tokens get updated, so let's try to get it back
                require("splunkjs/ready")();
            });

            // Set up resize callback. The first argument is a this
            // pointer which gets passed into the callback event
            $(window).resize(this, _.debounce(this._handleResize, 20));
        },

        _handleResize: function(e){

            var availableWidth  = parseInt(e.data.$el.width()) - margin.left - margin.right;
            var availableHeight = parseInt(e.data.$el.height()- margin.top - margin.bottom);

            var svg = d3.select(e.data.el)
                .select("svg")
                .attr("width", availableWidth + margin.left + margin.right)
                .attr("height", availableHeight + margin.top + margin.bottom);

            e.data._viz.height = availableHeight;
            e.data._viz.width  = availableWidth;

            e.data.render();
        },

        createView: function() {
            // Here we set up the initial view layout

            var availableWidth = parseInt(this.$el.width()) - margin.left - margin.right;
            var availableHeight = parseInt(this.$el.height() - margin.top - margin.bottom);

            this.$el.html("");

            var svg = d3.select(this.el)
                .append("svg")
                .attr("width", availableWidth + margin.left + margin.right)
                .attr("height", availableHeight + margin.top + margin.bottom)
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
                .attr("pointer-events", "all");

            var footer = $(".panel-footer", this.$el.parent());
            if (footer.length == 0) {
                this.$el.after("<div class='panel-footer'></div>");
                this.resultsLink = new ResultsLinkView(_.extend({}, {}, this.options, {
                                    id: _.uniqueId(this.id + '-resultslink'),
                                    el: $('<div class="view-results pull-left"></div>').appendTo($('.panel-footer', this.$el.parent())),
                                    managerid: this.manager.id,
                                    model: (ReportModel ? new ReportModel(): false)
                                })).render();
            }

            // The returned object gets passed to updateView as viz
            return { container: this.$el, svg: svg, height: availableHeight, width: availableWidth};
        },


        formatData: function(data) {
            var startField     = this.settings.get('startField');
            var endField       = this.settings.get('endField');
            var durationField  = this.settings.get('durationField');
            var categoryField  = this.settings.get('categoryField');
            var categorySearch = this.settings.get('categorySearch');
            var seriesField    = this.settings.get('seriesField');
            var extrasField    = this.settings.get('extrasField');
            var drilldownField = this.settings.get('drilldownField');
            var highlightField = this.settings.get('highlightField');

	        if (categorySearch && !this.categorySeed) {
                var that = this;
                this.categorySeed = [];

		        // Run a oneshot search that returns the job's results
		        this.manager.service.oneshotSearch(
                    categorySearch,
                    { earliest_time: this.manager.job.properties().searchEarliestTime,
                      latest_time: this.manager.job.properties().searchLatestTime },
                    function(err, results) {
                        // Collect the results
                        var fields = results.fields;
                        var rows = results.rows;

                        for(var i = 0; i < rows.length; i++) {
                            var values = rows[i];
                            for(var j = 0; j < values.length; j++) {
                                if (fields[j] == categoryField) {
                                    that.categorySeed.push(values[j]);
                                }
                            }
                        }
                        that.render();
                    });
            }

            var taskArray = [];

            // We need two out of these three fields, so make sure they're set
            if ((startField? 1: 0) + (endField? 1: 0) + (durationField? 1: 0) < 2) {
                this.displayMessage({
                    level: "error",
                    icon: "warning-sign",
                    message: "Must specify at least two of: startField, endField, durationField."
                });
                return false;
            }

            _(data).each(function(d) {

                // Make sure we're not dealing with mv fields
                d[startField] = [].concat(d[startField])[0];
                d[endField]   = [].concat(d[endField])[0];
                d[durationField] = [].concat(d[durationField])[0];
                d[extrasField] = [].concat(d[extrasField])[0];
                d[categoryField] = _([].concat(d[categoryField])).uniq().sort().join(',');
                d[seriesField] = _([].concat(d[seriesField])).uniq().sort().join(',');
                d[highlightField] = _([].concat(d[highlightField])).uniq().sort().join(',');

                try {
                    var extras = JSON.parse(d[extrasField]);
                } catch (SyntaxError) {
                    var extras = d[extrasField];
                }

                var start = new Date(isNaN(d[startField]) ? Date.parse(d[startField]) : d[startField]*1000);
                var end   = new Date(isNaN(d[endField])   ? Date.parse(d[endField])   : d[endField]*1000);
                var dur   = d[durationField];

                if (startField && durationField && !endField) {
                    end = new Date(+start+dur*1000);
                } else if (endField && durationField && !startField) {
                    start = new Date(+end-dur*1000);
                } else if (startField && endField) {
                    dur = (end-start)/1000;
                }

                // If we don't have a duration by now, skip this result
                if (isNaN(dur)) {
                    console.warn("Unable to format event:", d);
                    return;
                }

                taskArray.push({
                    "id"        : {'time': Date.parse(d['_time'])/1000, 'span': dur, 'field': d[drilldownField]},
                    "startTime" : start,
                    "endTime"   : end,
                    "duration"  : dur,
                    "category"  : d[categoryField],
                    "series"    : d[seriesField],
                    "highlight" : (highlightField? d[highlightField] : d[seriesField]),
                    "extras"    : extras,
                    "raw"       : d
                })
            });

            return taskArray; // this is passed into updateView as 'data'
        },

        updateView: function(viz, data) {
            var that = this;

            var showLegend     = (this.settings.get('showLegend') === 'true');
            var compact        = (this.settings.get('compact')    === 'true');
            var categoryLabel  = this.settings.get('categoryLabel');
            var seriesLabel    = this.settings.get('seriesLabel');
            var timeAxisMode   = this.settings.get('timeAxisMode');
            var sortCategories = (this.settings.get('categorySort') !== 'false'); // default to 'true'
            var sortSeries     = (this.settings.get('seriesSort')   !== 'false'); // default to 'true'


            if (compact) {
                var barHeight  = 5;
                var barSpacing = 1;
                var barRound   = 0;
            } else {
                var barHeight  = 20;
                var barSpacing = 4;
                var barRound   = 3;
            }
            var rowMinHeight = 10;
            var gap = barHeight + barSpacing;

            var width  = viz.width;
            var height = viz.height;

            // Clear svg
            var svg = $(viz.svg[0]);
            svg.empty();

            var seed = [];
            if (this.categorySeed) {
                seed = this.categorySeed;
            }
            var categories = _(_(data).pluck('category').concat(seed)).uniq();
            if (sortCategories) {
                categories = categories.sort();
            }

            var series     = _(_(data).pluck('series')).uniq();
            if (sortSeries) {
                series = series.sort();
            }

            // Prepare the color scale for the series
            var colorScale = d3.scale.category20()
                .domain(series);


            // First we need to make an initial Y axis, mostly to get the width right
            var y = d3.scale.ordinal()
                .domain(categories)
                .rangeRoundBands([0, categories.length*gap]);

            var yAxisBBox = makeYaxis(viz, y, gap, categoryLabel);


            // Now make the X axis
            var timeRange;
            if (timeAxisMode === 'DATA_RANGE') {
                timeRange = [d3.min(data, function(d) {return d.startTime;}),
                             d3.max(data, function(d) {return d.endTime;})];
            }
            else {  // SEARCH_RANGE
                timeRange = [new Date(this.manager.job.properties().searchEarliestTime * 1000),
                             new Date(this.manager.job.properties().searchLatestTime * 1000)];
            }
            var x = d3.time.scale()
                .domain(timeRange)
                .range([0, width - yAxisBBox.width - margin.left]);

            var xAxis = viz.svg.append("g")
                .attr("id", "xAxis")
                .attr("class", "axis");

            // Figure out how many ticks we want based on the space available (the 70 is a heuristic value)
            var ticks = Math.ceil((width - yAxisBBox.width - margin.left)/70);

            xAxis.call(d3.svg.axis()
                        .scale(x)
                        .tickSubdivide(true)
                        .ticks(ticks)
                        .orient("bottom"));

            xAxis.append("text")
                    .text("Time")
                    .attr("class", "title")
                    .attr("x", function(d) {
                        var xAxisBBox = viz.svg.select("#xAxis")[0][0].getBBox();
                        return (xAxisBBox.width + this.getBBox().width) / 2;
                    })
                    .attr("y", function(d) {
                        var xAxisBBox = viz.svg.select("#xAxis")[0][0].getBBox();
                        return xAxisBBox.height + 5;
                    });


            // Create the tooltip
            var tip = d3tip()
                .attr('class', 'd3-tip')
                .offset([-10, 0])
                .html(function(d) {
                    var tag = "<table>" +
                        "<tr><td>Start time</td><td>" + dateStr(d.startTime) + "</td></tr>" +
                        "<tr><td>End time</td><td>" + dateStr(d.endTime) + "</td></tr>" +
                        "<tr><td>Duration</td><td>" + durationStr(d.duration) + "</td></tr>" +
                        "<tr><td>" + seriesLabel + "</td>" +
                            "<td style='color: " + d3.rgb(colorScale(d.series)) + "'>" + d.series + "</td></tr>" +
                        "<tr><td>" + categoryLabel + "</td><td>" + d.category + "</td></tr>";
                    if (_.isObject(d.extras)) {
                        for (k in d.extras) {
                            tag += "<tr><td>" + k + "</td><td>" + d.extras[k] + "</td></tr>";
                        }
                    } else if (_.isString(d.extras)) {
                        tag += "<tr><td colspan='2'>" + d.extras + "</td></tr>";
                    }

                    return tag + "</table>";
            })
            viz.svg.call(tip);



            //Create the legend
            if (showLegend) {
                var keyPadding = {top: 2, right: 10, bottom: 2, left: 10, spacing: 10};

                var rectangles = viz.svg.append('g')
                    .attr("id", "legend")
                    .attr("class", "legend")
                    .selectAll("rect")
                    .data(series)
                    .enter()
                        .append("g");

                var text = rectangles.append("text")
                    .attr("class", function(d) { return "mos mos-"+_cleanClass(d);})
                    .text(function(d) { return d; })
                    .attr("x", function(d, i) {
                        var x = keyPadding.left;
                        if (this.parentElement.previousSibling) {
                            var prevBox = d3.select(this.parentElement.previousSibling)[0][0].getBBox();
                            x += prevBox.x + prevBox.width + keyPadding.right + keyPadding.spacing;
                        }
                        var max = d3.select(this.parentElement.parentElement.parentElement)[0][0].getBBox().width;
                        if (x + this.getBBox().width + keyPadding.right + keyPadding.spacing >= max - keyPadding.spacing) {
                            x = keyPadding.left;
                        }
                        return x;
                    })
                    .attr("y", function(d) {
                        var siblings = this.parentElement.parentElement.children;

                        var meBox = this.getBBox();
                        if (this.parentElement.previousSibling) {
                            var y = parseInt(this.parentElement.previousSibling.childNodes[0].getAttribute('y'));
                        } else {
                            var y = meBox.height + keyPadding.top - keyPadding.bottom*2;
                        }

                        var me = { left  : meBox.x - keyPadding.spacing/2,
                                   top   : y,
                                   right : meBox.x + meBox.width + keyPadding.spacing/2,
                                   bottom: y + meBox.height
                                 }

                        for(var i=0; i<siblings.length; i++) {
                            var child = siblings[i].childNodes[0];
                            if (this == child) {
                                break;
                            }

                            var cBox = child.getBBox();
                            var cB = { left  : cBox.x - keyPadding.spacing/2,
                                       top   : cBox.y,
                                       right : cBox.x + cBox.width + keyPadding.spacing/2,
                                       bottom: cBox.y + cBox.height
                                     }

                            if (me.left <= cB.right  &&
                                cB.left  <= me.right &&
                                me.top  <  cB.bottom &&
                                cB.top   <  me.bottom) {

                                // Move down one line
                                me.top = me.bottom + keyPadding.bottom + keyPadding.spacing;
                                me.bottom = me.top + meBox.height;
                                // Start looking again
                                i = 0;
                            }
                        }
                        return me.top;
                    })
                    .attr("fill", "white")
                    .attr("text-anchor", "start")
                    .on("mouseover", function(d) {
                        $(".mos", $(this).closest('svg')).css("opacity", 0.1);
                        $(".mos-"+_cleanClass(d), $(this).closest('svg')).css("opacity", 1);
                    })
                    .on("mouseout", function(d) {
                        $(".mos", $(this).closest('svg')).css("opacity", 1);
                    });

                var rects = rectangles.insert("rect", "text")
                    .attr("class", function(d) { return "mos mos-"+_cleanClass(d);})
                    .attr("rx", 3)
                    .attr("ry", 3)
                    .attr("x", function(d) {
                        var tBox = d3.select(this.parentElement).select("text")[0][0].getBBox();
                        return tBox.x - keyPadding.left;
                    })
                    .attr("y", function(d) {
                        var tBox = d3.select(this.parentElement).select("text")[0][0].getBBox();
                        return tBox.y - keyPadding.top;
                    })
                    .attr("width", function(d) {
                        var tBox = d3.select(this.parentElement).select("text")[0][0].getBBox();
                        return tBox.width + keyPadding.left + keyPadding.right;
                    })
                    .attr("height", function(d) {
                        var tBox = d3.select(this.parentElement).select("text")[0][0].getBBox();
                        return tBox.height + keyPadding.top + keyPadding.bottom;
                    })
                    .attr("fill", function(d) { return d3.rgb(colorScale(d)); })
                    .on("mouseover", function(d) {
                        $(".mos", $(this).closest('svg')).css("opacity", 0.1);
                        $(".mos-"+_cleanClass(d), $(this).closest('svg')).css("opacity", 1);
                    })
                    .on("mouseout", function(d) {
                        $(".mos", $(this).closest('svg')).css("opacity", 1);
                    });
            }



            // Now, finally, add the data
            var dataArea = viz.svg.append("g")
                .attr("class", "data")
                .attr("transform", "translate(" + yAxisBBox.width + ", " + (barSpacing/2) + ")");

            var actualRange = [];
            _(categories).each(function(c) {
                var cData = _(_(data).where({ 'category': c })).sortBy(function(d) { return -d.duration; });

                // Find the colliding tasks first so we don't have to go over all of them every time
                var overlaps = [];
                _(cData).each(function(t, i) {
                    overlaps[i] = [];
                    _(_(cData).first(i)).each(function(v, j) {
                        if ((t.startTime <= v.endTime) &&
                           (v.startTime <= t.endTime)) {
                            overlaps[i].push(_(cData).indexOf(v));
                        }
                    });
                });

                dataArea.append("g")
                    .attr("class", "layer")
                    .attr("x", 0)
                    .attr("y", function(d) {
                        var y = 0;
                        if (this.previousSibling) {
                            var h = _(_(this.previousSibling.children).map(function(c) {
                                return parseFloat(c.getAttribute("y"))+parseFloat(c.getAttribute("height"));
                            }).concat([parseFloat(this.previousSibling.getAttribute("y"))+Math.max(barHeight+barSpacing, rowMinHeight)])).max();
                            y += h + barSpacing*2;
                        }

                        actualRange.push(y);
                        return y;
                    })
                    .selectAll(".bar")
                    .data(cData)
                    .enter().append("rect")
                        .attr("class", function(d) {
                            return "bar mos mos-"+_cleanClass(d.series)+" mof-"+_cleanClass(d.highlight);
                        })
                        .attr("data-time", function(d) { return d.id.time; })
                        .attr("data-span", function(d) { return d.id.span; })
                        .attr("data-field", function(d) { return d.id.field; })
                        .attr("data-raw", function(d) { return JSON.stringify(d.raw); })
                        .attr("rx", barRound)
                        .attr("ry", barRound)
                        .attr("x", function(d) { return x(d.startTime); })
                        .attr("width", function(d) { return x(d.endTime)-x(d.startTime); })
                        .attr("height", barHeight)
                        .attr("y", function(d, i) {
                            var yPos = parseInt(this.parentNode.getAttribute("y"));

                            if (overlaps[i].length > 0) {
                                // Get previous siblings
                                var prevs = [];
                                var elem = this;
                                while(elem = elem.previousSibling) { prevs.push(elem); }

                                var myBox = $(this);
                                var me = { left  : parseFloat(myBox.attr("x")),
                                           top   : yPos,
                                           right : parseFloat(myBox.attr("x")) + parseFloat(myBox.attr("width")),
                                           bottom: yPos + parseFloat(myBox.attr("height"))
                                         }

                                // Get all the other tasks boxes once
                                // Don't use getBBox(), it kills performance
                                var pBoxes = [];
                                for(j = 0; j < overlaps[i].length; j++) {
                                    // prevs is backwards, and this is better than sorting it
                                    var pBox = $(prevs[prevs.length-1-overlaps[i][j]]);

                                    pBoxes.push({ left  : parseFloat(pBox.attr("x")),
                                                  top   : parseFloat(pBox.attr("y")),
                                                  right : parseFloat(pBox.attr("x")) + parseFloat(pBox.attr("width")),
                                                  bottom: parseFloat(pBox.attr("y")) + parseFloat(myBox.attr("height"))
                                                });
                                }

                                var clean = false;
                                while(!clean) {
                                    var j;
                                    for(j = 0; j < overlaps[i].length; j++) {
                                        var p  = pBoxes[j];

                                        if (me.left < p.right  &&
                                            p.left  < me.right &&
                                            me.top  < p.bottom &&
                                            p.top   < me.bottom) {

                                            // Move to the next row down and try again
                                            yPos = me.bottom + barSpacing;
                                            me.top = yPos;
                                            me.bottom = yPos + parseFloat(myBox.attr("height"));
                                            break;
                                        }
                                    }
                                    if (j == overlaps[i].length) {
                                        // If we made it all the way through the for, we didn't overlap with anyone
                                        clean = true;
                                    }
                                }
                            }

                            return yPos;
                        })
                        .attr("fill", function(d) { return d3.rgb(colorScale(d.series)); })
                        .on("mouseover", function(d) {
                            $(".mos", $(this).closest('svg')).css("opacity", 0.1);
                            $("#legend .mos-"+_cleanClass(d.series), $(this).closest('svg')).css("opacity", 1);
                            if (d.highlight != d.series) {
                                $(".mof-"+_cleanClass(d.highlight), $(this).closest('svg')).css("opacity", 1);
                            }
                            $(this).css("opacity", 1);

                            tip.show(d);
                        })
                        .on("mouseout", function(d) {
                            $(".mos", $(this).closest('svg')).css("opacity", 1);

                            tip.hide(d)
                        });
            });

            // Get the height of the last layer, but don't use BBox
            var h = _(_(_(dataArea.selectAll(".layer")[0]).last().children).map(function(c) {
                return parseFloat(c.getAttribute("y"))+parseFloat(c.getAttribute("height"));
            }).concat([parseFloat(_(dataArea.selectAll(".layer")[0]).last().getAttribute("y"))+Math.max(barHeight+barSpacing, rowMinHeight)])).max();
            actualRange.push(h + barSpacing*2);

            // Now that all that's done, we can go make the real Y Axis, because we know the actual position of each layer

            y = d3.scale.ordinal()
                .domain(categories)
                .range(actualRange);

            // Out with the old...
            viz.svg.select("#yAxis").remove();
            // ... in with the new
            yAxisBBox = makeYaxis(viz, y, gap, categoryLabel);

            // Move the X axis to it's place
            xAxis.attr("transform", "translate(" + yAxisBBox.width + ", " + yAxisBBox.height + ")");

            if (showLegend) {
                // Now move the legend to it's place
                var xAxisBBox = viz.svg.select("#xAxis")[0][0].getBBox();
                var center = yAxisBBox.width + xAxisBBox.width/2 - viz.svg.select("#legend")[0][0].getBBox().width/2
                viz.svg.select("#legend").attr("transform", "translate(" + center + ", " + (yAxisBBox.height + xAxisBBox.height + margin.bottom) + ")");
            }


            // Now that we know how big the chart is, we can set the real height
            svg.parent().attr("height", viz.svg.node().getBBox().height + margin.top + margin.bottom);
        }

    });

    function makeYaxis(viz, y, gap, categoryLabel) {

        var yAxis = viz.svg.append("g")
            .attr("id", "yAxis")
            .attr("class", "axis");

        yAxis.call(d3.svg.axis().scale(y).orient("left"))
            .append("text");

        // Move the category labels down to the middle of the first row
        var yPos = Math.max(gap/2, $(".tick text", viz.container)[0].getBBox().height/2);
        yAxis.selectAll(".tick text")
            .attr("y", yPos);

        var yAxisBBox = viz.svg.select("#yAxis")[0][0].getBBox();

        // If we have a categoryLabel other than the default, label the axis
        if (categoryLabel != "Category") {
            yAxis.append("text")
                .text(categoryLabel)
                .attr("class", "title")
                .attr("transform", function(d) {
                    return "rotate(-90)";
                })
                .attr("x", function(d) {
                    return -(yAxisBBox.height + this.offsetHeight) / 2;
                })
                .attr("y", function(d) {
                    return -yAxisBBox.width - 10;
                });
            yAxisBBox = viz.svg.select("#yAxis")[0][0].getBBox();
        }

        // Move the Y axis into position
        viz.svg.select("#yAxis").attr("transform", "translate(" + yAxisBBox.width + ", 0)");

        return yAxisBBox;
    }

    function dateStr(d) {
        var str = $.datepicker.formatDate('M d, yy', d);

        if (0 != d.getHours() || 0 != d.getMinutes() || 0 != d.getSeconds()) {
            if (0 == d.getSeconds()) {
                str += ' ' + d.toTimeString().substr(0, 5);
            } else {
                str += ' ' + d.toTimeString().substr(0, 8);
            }
        }

        return str;
    }

    function durationStr(t) {

        var days    = parseInt(t / 86400);
        var hours   = parseInt(t / 3600)  % 24;
        var minutes = parseInt(t / 60)    % 60;
        var seconds = t % 60;

        return (days    > 0 ? ("0" + days   ).slice(-2) + "d " : "") +
               (hours   > 0 ? ("0" + hours  ).slice(-2) + "h " : "") +
               (minutes > 0 ? ("0" + minutes).slice(-2) + "m " : "") +
               (seconds > 0 ? ("0" + seconds).slice(-2) + "s"  : "");
    }

    return GanttChart;
});
