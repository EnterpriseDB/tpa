
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8


/**
 * Primary entry point for TPA UI app.
 */

import "./styles";
import * as api from "./tpa-api";
import * as tpa_diagram from "./tpa-d3";
import * as d3 from "d3";
import {get_url_vars} from "./utils";
import $ from "jquery";


function unhide_page_once_scripts_loaded() {
    d3.selectAll("#cover").style("visibility", "hidden");
}


function process_login_form() {
    d3.selectAll("form.login-form").on("submit", () => {
        let username = d3.select("input.username").node().value;
        let password = d3.select("input.password").node().value;

        d3.event.preventDefault();

        api.auth.login(username, password, (error, result) => {
            if (!error) {
                let next = d3.select("input.on-success-redirect");
                if (!next.empty() && next.node().value) {
                    window.location = next.node().value;
                }
            }
            else {
                alert("Login failed, please check your credentials.");
            }
        });
    });


    api.auth.on("login.popup", () => {
        $("#LoginForm").modal("hide");
    });

    api.auth.set_login_display(() => {
        $("#LoginForm").modal("show");
    });

    if(!d3.select("meta#login-required").empty()) {
        api.auth.display_login();
    }
}


function display_cluster_diagram() {
    const container = d3.select(".cluster_view");
    if (container.empty()) {
        return;
    }

    let vars = get_url_vars();

    if (vars.cluster) {
        d3.select("button.next-cluster").style("visibility", "hidden");
        tpa_diagram.display_cluster_by_uuid(vars.cluster, container);
    }
    else {
        var next_cluster = tpa_diagram.show_clusters(container);
        d3.select("button.next-cluster").on("click", () => next_cluster());
    }
}


function submit_cluster_upload() {
    d3.selectAll("form.cluster_upload_yml").on("submit", () => {
        let tenant = d3.select("input.tenant").node().value;
        let config_yml = d3.select("input.config_yml").node().value;

        d3.event.preventDefault();

        api.cluster_upload(tenant, config_yml, function(error, res) {
            if (!error) {
                window.location = `/cluster.html?cluster={res.cluster}`;
            }
            else{
                alert(error);
            }
        });
        return true;
    });
}


// Main entry point.

document.addEventListener("DOMContentLoaded", () => {
    unhide_page_once_scripts_loaded();
    process_login_form();
    display_cluster_diagram();
    submit_cluster_upload();
});
