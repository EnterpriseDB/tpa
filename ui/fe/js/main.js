
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

export const _d3 = d3;


function login_form() {
    d3.selectAll("form.login_form").on("submit", () => {
        let username = d3.select("input.username").node().value;
        let password = d3.select("input.password").node().value;

        d3.event.preventDefault();

        api.auth.login(username, password, (error, result) => {
            if(error) {
                alert("Login failed, please check your credentials.");
                return;
            }

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
        });
    });


    api.auth.on("login.popup", () => {
        $("#LoginForm").modal("hide");
    });

    api.auth.set_login_display(() => {
        $("#LoginForm").modal("show");
    });

}

function user_invite() {
    d3.selectAll("form.user_invite").on("submit", function() {
        d3.event.preventDefault();

        let email_el = d3.select(this).select("input.email");
        let email = email_el.node().value;

        api.object_create("auth/user-invite",
            { email: email },
            (error, data) => {
                if(error) {
                    alert(`Invite Error: ${error.currentTarget.response}`);
                    return;
                }

                email_el.attr("value", "");

                alert(`Invitation sent to ${email}.`);

                $("#user_invite_dialog").modal("hide");
            });
    });

    d3.selectAll("a.user_invite").on("click", function() {
        console.log("click");
        $("#user_invite_dialog").modal("show");
    });
}

function user_invite_accept() {
    d3.selectAll("form.user_invite_accept").on("submit", function() {
        d3.event.preventDefault();

        let sub = d3.select(this);

        let invite = get_url_vars().invite;

        api.object_update('auth/user-invite', invite, {
                username: sub.select("input.username").node().value,
                password: sub.select("input.password").node().value,
                first_name: sub.select("input.first_name").node().value,
                last_name: sub.select("input.last_name").node().value,
                ssh_public_keys: 
                    JSON.stringify(sub.select("input.ssh_public_keys").node().value),
            },
            (error, data) => {
                if(error) {
                    alert(`Invite Error: ${error.currentTarget.response}`);
                    return;
                }
            window.location = "/home.html";
        });
    });
}


function cluster_import() {
    d3.selectAll("form.cluster_import").on("submit", function()  {
        d3.event.preventDefault();

        let root = d3.select(this);

        // api.cluster_upload(tenant, config_yml, function(error, res) {
        api.auth.json_request(api.class_to_url('cluster_upload_yml'))
            .post(api.json_to_form({
                tenant: root.select("input.tenant").node().value,
                config_yml: root.select("input.config_yml").node().files[0]}),
                (error, res) => {
                    if (error) {
                        alert(`Import Error: ${error.currentTarget.responseText}`);
                        return;
                    }
                    window.location = `/cluster.html?cluster=${res.cluster}`;
        });
        return true;
    });

    d3.selectAll("button.cluster_import").on("click", function() {
        $("#cluster_import_dialog").modal("show");
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
            .attr("href", d => `/cluster.html?cluster=${d.uuid}`)
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

    api.object_list("cluster", "", (error, clusters) => {
        if (error) {
            table.append("h4").text("(Load error)");
            return;
        }
        table.selectAll("tr.cluster_row")
            .data(clusters)
            .enter()
                .append("tr")
                .classed("cluster_row", true)
                .call(add_cluster);
    });
}

function cluster_create() {
    // TODO
}

// Main entry point.
d3.select("meta#login-required").call((s) => {
    if ( !s.empty()  ) {
        api.auth.logged_in_or_redirect("/login.html");
    }
});

api.auth.on("login.unhide-body", () => {
    d3.selectAll("body").style("visibility", "visible");
});

document.addEventListener("DOMContentLoaded", () => {
    unhide_page_once_scripts_loaded();

    // Login page
    login_form();

    // User home
    user_invite();
    user_invite_accept();
    cluster_list();
    cluster_import();
    cluster_create();

    // Cluster page
    show_cluster_diagram();
});
