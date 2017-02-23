
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8


/**
 * Primary entry point for TPA UI app.
 */

import "./styles";
import * as api from "./tpa-api";
import * as tpa_diagram from "./tpa-d3";
import * as d3 from "d3";
import {get_url_vars} from "./utils";


export function display_all_cluster_diagrams() {
    document.addEventListener("DOMContentLoaded", function(e) {
        var next_cluster = tpa_diagram.show_clusters(
                d3.select(".cluster_view"));
        d3.select("button.next-cluster").on("click", () => next_cluster());
    });
}


export function display_cluster_diagram(viewport_class) {
    document.addEventListener("DOMContentLoaded", function(e) {
        let vars = get_url_vars();

        if (vars.cluster) { 
            d3.select("button.next-cluster").style("visibility", "hidden");
            tpa_diagram.display_cluster_by_uuid(vars.cluster,
                    d3.select(viewport_class));
        }
        else {
            var next_cluster = tpa_diagram.show_clusters(d3.select(viewport_class));
            d3.select("button.next-cluster").on("click", () => next_cluster());
        }

    });
}


export function register_login(on_success) {
    function do_login() {
        var login_form = d3.select("form.login-form");

        if (!login_form) {
            return;
        }

        login_form.on("submit", () => {
            let username = d3.select("input.username").node().value;
            let password = d3.select("input.password").node().value;

            d3.event.preventDefault();

            api.auth.login(username, password, function(error, result) {
                if (!error) {
                    if (on_success) {
                        on_success();
                    }
                    else {
                        window.location = "/cluster.html";
                    }
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


document.addEventListener("DOMContentLoaded", () => {
    console.log("Called");
    d3.selectAll("#cover").style("visibility", "hidden");
});
