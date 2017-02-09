
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8


/**
 * Primary entry point for TPA UI app.
 */

import "./styles";
import * as api from "./tpa-api";
import * as tpa_diagram from "./tpa-d3";
import * as d3 from "d3";

export function display_cluster_diagram() {
    document.addEventListener("DOMContentLoaded", function(e) {
        var next_cluster = tpa_diagram.show_clusters(
                d3.select(".cluster_view"));
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

export function register_cluster_upload() {
    function submit_cluster_upload() {
        d3.select("form.cluster_upload_yml").on("submit", () => {
            let tenant = d3.select("input.tenant").node().value;
            let config_yml = d3.select("input.config_yml").node().value;

            d3.event.preventDefault();

            api.cluster_upload(tenant, config_yml, function(error, res) {
                if (!error) {
                    window.location = "/cluster.html?cluster=" + res.cluster;
                }
                else{
                    alert(error);
                }
            });
            return true;
        });
    }

    document.addEventListener("DOMContentLoaded", submit_cluster_upload);
}
