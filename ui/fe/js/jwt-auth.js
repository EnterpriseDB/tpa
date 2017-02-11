
/**
 * JWT authentication for TPA API.
 *
 * A user signs in with JWT. This is stored in localstorage
 * with the refresh date so that it can be refreshed or expired as necessary.
 * 
 * On the server side, the user's current tenant
 *
 */

import * as d3 from "d3";

import $ from "jquery";

export class JWTAuth {
    constructor(auth_url_base, local_storage=true) {
        this.auth_url_base = auth_url_base;
        this.storage = local_storage ? localStorage : sessionStorage;
    }

    set_token(username, token) {
        console.log("JWT token:", token);
        this.storage.setItem('jwt_auth_username', username);
        this.storage.setItem('jwt_auth_token', token);
        this.storage.setItem('jwt_auth_token_timestamp',
            (token === undefined || token === null) ? null : Date()
        );
    }

    login(username, password, callback) {
        let auth = this;

        d3.request(this.auth_url_base+'login/')
            .header("Content-Type", "application/json")
            .on('load', function(xhr) {
                let json_response = JSON.parse(xhr.responseText);

                auth.set_token(username, json_response.token);
                callback(null, json_response.token);
            })
            .on('error', function(error) {
                console.log("Login failed:", error);
                auth.set_token(null, null);
                callback(error);
            })
            .send('POST', JSON.stringify({
                'username': username,
                'password': password
            }));
    }

    get logged_in() {
        return (this.storage.getItem('jwt_auth_token') ? true : false);
    }

    get username() {
        return this.storage.getItem('jwt_auth_token') ?
            this.storage.getItem('jwt_auth_username')
            : "";
    }

    logout() {
        this.set_token(null, null);
    }

    json_request(url) {
        var auth_token = this.storage.getItem("jwt_auth_token");
        var bearer = (auth_token === null || auth_token === undefined) ?  ""
                : ("JWT " + auth_token);

        return d3.request(url)
            .mimeType("application/json")
            .header("Authorization", bearer)
            .response(r => JSON.parse(r.responseText));
    }

    popup_login(on_success) {
        var login_form = d3.select("form.login-form");
        var auth = this;

        login_form.on("submit", () => {
            let username = d3.select("input.username").node().value;
            let password = d3.select("input.password").node().value;

            d3.event.preventDefault();

            auth.login(username, password, function(error, result) {
                if (error) {
                    alert("Login failed, please check your credentials.");
                    auth.popup_login(on_success);
                }
                else {
                    $("#LoginForm").modal("hide");
                    if (on_success) {
                        on_success();
                    }
                }
            });

            return true;
        });

        $("#LoginForm").modal("show");
    }
}
