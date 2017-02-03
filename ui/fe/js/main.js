
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8


/**
 * Primary entry point for TPA UI app.
 */


require('./styles.js');
var d3 = require("d3");

var tpa = require("./tpa-api");
var tpa_d3 = require("./tpa-d3");
var jwt_auth = require("./jwt-auth");

var current_tenant = tpa.TEST_TENANT;

// require("./diagram");
// require("./utils");
//

export function display_cluster_diagram() {
    document.addEventListener("DOMContentLoaded", function(e) {
        var next_cluster = tpa_d3.show_clusters(current_tenant,
                                        d3.select(".cluster_view"),
                                        1000, 1000);
        d3.select("button.next-cluster").on("click", () => next_cluster());
    });
}




export function register_login() {
    function do_login() {
        d3.select("form.login-form").on("submit", () => {
            let username = d3.select("input.username").node().value;
            let password = d3.select("input.password").node().value;

            d3.event.preventDefault();

            tpa.auth.login(username, password, function(error, result) {
                console.log("error:", error, "result:", result);
                if (!error) {
                    window.location = "/cluster.html";
                }
                else {
                    // error
                    alert("Login failed, please check your credentials.");
                }
            });

            return true;
        });
    }

    document.addEventListener("DOMContentLoaded", do_login);
}
