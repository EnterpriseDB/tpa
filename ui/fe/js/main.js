
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8


/**
 * Primary entry point for TPA UI app.
 */


require('es6-promise').polyfill();

import "./styles";
import * as api from "./tpa-api";
import {show_cluster_diagram} from "./cluster-diagram";
import * as d3 from "d3";
import {get_url_vars} from "./utils";
import $ from "jquery";


function unhide_page_once_scripts_loaded() {
    d3.selectAll("#cover").style("visibility", "hidden");
}


function login_form() {
    d3.selectAll("form.login_form").on("submit", () => {
        let username = d3.select("input.username").node().value;
        let password = d3.select("input.password").node().value;

        d3.event.preventDefault();

        api.auth.login(username, password, (error, result) => {

            if (!error) {
                let url_vars = get_url_vars();
                if (url_vars.next) {
                    window.location = url_vars.next;
                }
                else {
                    let next = d3.select("input.on-success-redirect");
                    if (!next.empty() && next.node().value) {
                        window.location = next.node().value;
                    }
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

}


function cluster_upload() {
    d3.selectAll("form.cluster_upload").on("submit", () => {
        let tenant = d3.select("input.tenant").node().value;
        let config_yml = d3.select("input.config_yml").node().files[0];

        d3.event.preventDefault();

        api.cluster_upload(tenant, config_yml, function(error, res) {
            if (!error) {
                window.location = `/cluster.html?cluster=${res.cluster}`;
            }
            else{
                alert(error);
            }
        });
        return true;
    });
}


function cluster_list() {
    let column_names = ["Name", "Created", "Last update"];
    let root = d3.select(".cluster_list");
    if (root.empty()) { return; }

    root.append("h3").text("Clusters");

    let table = root.append("table").classed("table table-bordered", true);

    function add_cluster(selection) {
        selection.append("td")
            .append("a")
            .attr("href", d => `/cluster.html?cluster_uuid=${d.uuid}`)
            .text(d => d.name);

        selection.append("td") .text(d => Date(d.created).toLocaleString());
        selection.append("td") .text(d => Date(d.updated).toLocaleString());
    }

    table.append("tr")
        .classed("header_row", true)
        .selectAll("th")
        .data(column_names)
        .enter()
            .append("th")
            .text(d => d);

    api.get_all("cluster", null, function(clusters) {
        table.selectAll("tr.cluster_row")
            .data(clusters)
            .enter()
                .append("tr")
                .classed("cluster_row", true)
                .call(add_cluster);
    });
}

// Main entry point.
api.auth.on("login.unhide-body", () => {
    console.log("visible");
    d3.selectAll("body").style("visibility", "visible");
});

if(!d3.select("meta#login-required").empty()) {
    api.auth.logged_in_or_redirect("/index.html");
}

document.addEventListener("DOMContentLoaded", () => {
    unhide_page_once_scripts_loaded();
    login_form();
    cluster_list();
    show_cluster_diagram();
    cluster_upload();
});
