
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8


/**
 * Primary entry point for TPA UI app.
 */


require('./styles.js');

var d3 = require("d3");

var tpa = require("./tpa-api");
var tpa_d3 = require("./tpa-d3");
// require("./diagram");
// require("./utils");

// XXX This is for testing the cluster diagram.

document.addEventListener("DOMContentLoaded", function(e) {
    var next_cluster = tpa_d3.show_clusters(tpa.TEST_TENANT,
                                    d3.select(".cluster_view"),
                                    1000, 1000);
    d3.select("button.btn-primary").on("click", () => next_cluster());
});
