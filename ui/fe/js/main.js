
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8


/**
 * Primary entry point for TPA UI app.
 */

import "./styles";
import * as api from "./tpa-api";
import * as tpa_diagram from "./tpa-d3";
import * as d3 from "d3";

var current_tenant = api.TEST_TENANT;

export function display_cluster_diagram() {
    document.addEventListener("DOMContentLoaded", function(e) {
        var next_cluster = tpa_diagram.show_clusters(current_tenant,
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

            api.auth.login(username, password, function(error, result) {
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
