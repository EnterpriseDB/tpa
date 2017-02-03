
/**
 * JWT authentication for TPA API.
 *
 * A user signs in with JWT. This is stored in localstorage
 * with the refresh date so that it can be refreshed or expired as necessary.
 * 
 * On the server side, the user's current tenant
 *
 */

import {request} from "d3-request";

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
        let that = this;
        console.log("Signing in:", username, this);

        request(this.auth_url_base+'login/')
            .header("Content-Type", "application/json")
            .on('load', function(xhr) {
                var json_response = JSON.parse(xhr.responseText);

                console.log("Login success:", json_response.token);
                that.set_token(username, json_response.token);
                callback(null, json_response.token);
            })
            .on('error', function(error) {
                console.log("Login failed:", error);
                that.set_token(null, null);
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

        console.log("Bearer:", bearer);

        return request(url)
            .mimeType("application/json")
            .header("Authorization", bearer)
            .response(r => JSON.parse(r.responseText));
    }
}
