
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

export class JWTAuth {
    constructor(auth_url_base, local_storage=true) {
        this.auth_url_base = auth_url_base;
        this.storage = local_storage ? localStorage : sessionStorage;
        this.dispatch = d3.dispatch("login", "logout", "denied", "error");
        this.login_display_handler = function null_handler() {};
    }

    on(event, callback) {
        return this.dispatch.on(event, callback);
    }

    set_login_display(handler) {
        this.login_display_handler = handler;
    }

    display_login(on_success) {
        this.login_display_handler(on_success);
    }

    set_token(username, token) {
        this.storage.setItem('jwt_auth_username', username);
        this.storage.setItem('jwt_auth_token', token);
        this.storage.setItem('jwt_auth_token_timestamp',
            (token === undefined || token === null) ? null : Date()
        );
    }

    get token() {
        return this.storage.getItem('jwt_auth_token');
    }

    login(username, password, callback) {
        let auth = this;

        d3.request(this.auth_url_base+'login/')
            .header("Content-Type", "application/json")
            .on('load', function(xhr) {
                let json_response = JSON.parse(xhr.responseText);

                auth.set_token(username, json_response.token);
                auth.dispatch.call("login");
                callback(null, json_response.token);
            })
            .on('error', function(error) {
                console.log("Login failed:", error);
                auth.set_token(null, null);
                auth.dispatch.call("denied");
                callback(error);

            })
            .send('POST', JSON.stringify({
                'username': username,
                'password': password
            }));
    }

    verify(callback) {
        let auth = this;

        if (!auth.token) {
            auth.dispatch.call("logout");

            if (callback) {
                callback(false);
            }
            return;
        }

        d3.request(`${auth.auth_url_base}verify/`)
            .header("Content-Type", "application/json")
            .on('load', function(xhr) {
                let json_response = JSON.parse(xhr.responseText);
                auth.dispatch.call("login");
                if (callback) {
                    callback(null, json_response.token);
                }
            })
            .on('error', function(error) {
                auth.set_token(null, null);
                auth.dispatch.call("logout");
                if (callback) {
                    callback(error);
                }

            })
            .send('POST', JSON.stringify({
                'token': auth.token
            }));
    }

    logged_in_or_redirect(login_page) {
        let auth = this;
        auth.on("logout.redirect", () => {
            let next = encodeURIComponent(window.location);
            window.location = `${login_page}?next=${next}`;
        });

        auth.verify();
    }

    get logged_in() {
        return (this.token ? true : false);
    }

    get username() {
        return this.token ? this.storage.getItem('jwt_auth_username') : "";
    }


    logout() {
        this.set_token(null, null);
        this.dispatch.call("logout");
    }

    request(url) {
        console.log("Requested:", url);
        let req = d3.request(url);

        if (!this.logged_in) {
            return req;
        }

        return req.header("Authorization", `JWT ${this.token}`);
    }

    json_request(url) {
        return this.request(url)
            .mimeType('application/json')
            .response(r => JSON.parse(r.responseText));
    }
}
