
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8


/**
 * Primary entry point for TPA UI app.
 */


require('es6-promise').polyfill();
import * as d3 from "d3";
import $ from "jquery";

import "./styles";
import * as api from "./tpa-api";
import {show_cluster_diagram} from "./cluster-diagram";
import {get_url_vars} from "./utils";

import ClusterExport from '../components/ClusterExport.vue';

// For help with debugging.
export const _d3 = d3;
export const _api = api;


function main_app() {
    unhide_page_once_scripts_loaded();

    let w_m = api.window_model();

    // Login page
    login_form();

    // User Home page
    cluster_list();
    cluster_import();
    cluster_create();
    user_invite();

    // Cluster page
    if (w_m.model == 'cluster' && w_m.uuid) {
        d3.select(".cluster_diagram").call(show_cluster_diagram);
        new ClusterExport({el:"#cluster-export"});
    }

    // User registration page
    user_invite_accept();


}


function unhide_page_once_scripts_loaded() {
    d3.selectAll("#cover").style("visibility", "hidden");
}




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
        api.auth.logout();

        let sub = d3.select(this);
        let invite = api.window_model().uuid;
        let form = {};

        for (let field of ["username", "password", "first_name",
                            "last_name", 'ssh_public_keys']) {
            form[field] = sub.select(`input.${field}`).node().value;
        }

        form.ssh_public_keys = form.ssh_public_keys ?
            JSON.parse(form.ssh_public_keys) : [];

        api.object_update('auth/user/invite', invite, form, (error, data) => {
            if(error) {
                alert(`Invite Error: ${error.currentTarget.response}`);
                return;
            }
            window.location = "/home/";
        });
    });
}


function cluster_import() {
    d3.selectAll("form.cluster_import").on("submit", function()  {
        d3.event.preventDefault();

        let root = d3.select(this);

        api.cluster_create({
            tenant: root.select("input.tenant").node().value,
            config_yml: root.select("input.config_yml").node().files[0]
        },
            (error, res) => {
                if (error) {
                    alert(`Import Error: ${error.currentTarget.responseText}`);
                    return;
                }
                window.location = `/cluster/${res.uuid}/`;
            });
        return true;
    });

    d3.selectAll("button.cluster_import").on("click", function() {
        $("#cluster_import_dialog").modal("show");
    });
}

function cluster_create() {
    d3.selectAll("form.cluster_create").on("submit", function()  {
        d3.event.preventDefault();

        let root = d3.select(this);
        let tmpl = root.select("select.template").node();
        let template = tmpl.options[tmpl.selectedIndex].value;

        api.cluster_create({
            name: root.select("input.name").node().value,
            tenant: root.select("input.tenant").node().value,
            template: template
        },
            (error, res) => {
                if (error) {
                    alert(`Create Error: ${error.currentTarget.responseText}`);
                    return;
                }
                window.location = `/cluster/${res.uuid}/`;
            });
        return true;
    });

    d3.selectAll("button.cluster_create").on("click", function() {
        refresh_cluster_create_form();
        $("#cluster_create_dialog").modal("show");
    });
}


function refresh_cluster_create_form() {
    d3.selectAll("form.cluster_create")
        .select("select.template")
        .call(function(template_selection) {
            api.object_list("template", "",
                (error, clusters) => {
                    if (error) {
                        template_selection.text("(Load error)");
                        return;
                    }

                    template_selection
                        .selectAll("option")
                        .data(clusters)
                        .enter()
                        .append("option")
                        .attr("value", (t) => t.uuid)
                        .text((t) => t.name);
                });
        });
}


function cluster_list() {
    let column_names = ["Name"];
    let root = d3.select(".cluster_list");
    if (root.empty()) { return; }

    root.append("h3").text("Clusters");

    let table = root.append("table").classed("table table-bordered", true);

    function add_cluster(selection) {
        selection.append("td")
            .append("a")
            .attr("href", d => `/cluster/${d.uuid}/`)
            .text(d => d.name);
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

// Main entry point.
d3.select("meta#login-required").call((s) => {
    if ( !s.empty()  ) {
        api.auth.logged_in_or_redirect("/login/");
    }
});

api.auth.on("login.unhide-body", () => {
    d3.selectAll("body").style("visibility", "visible");
});

document.addEventListener("DOMContentLoaded", () => {
    main_app();
});
