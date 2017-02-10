
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

/**
* Tools for accessing the TPA API via the REST server.
*/

import {multimethod} from "./multimethod";
import {JWTAuth} from "./jwt-auth.js";

export const API_URL = "/api/v1/tpa/";
export const TEST_TENANT = API_URL + "tenant/d9073da2-138f-4342-8cb8-3462be0b325a/";

export var url_cache = {};
export var auth = new JWTAuth(API_URL+"auth/");
var provider = null;


/**
 * Returns the basic type of the cluster. Since the cluster doesn't have a type
 * tag of any kind, just use various roles.
 * Returns tpa (primary, replica etc) or xl (gtm, coord etc)
 */
export function cluster_type(cluster) {
    var cluster_type = "tpa";

    cluster.subnets.forEach(s =>
        s.instances.forEach(i =>
            i.roles.forEach(function(r) {
                if (r.role_type == "gtm" || r.role_type == "coordinator") {
                    cluster_type = "xl";
                }
            })));

    return cluster_type;
}

export function model_class(d) {
    if ( d && d.url) {
        var api_idx = d.url.indexOf(API_URL);
        if (api_idx >= 0) {
            var obj_path = d.url.slice(api_idx+API_URL.length);
            var next_slash = obj_path.indexOf("/");
            return obj_path.slice(0, next_slash);
        }
    }

    return null;
}

export function get_obj_by_url(url, _then) {
    if (url_cache[url]) {
        _then(url_cache[url]);
        return;
    }

    if (!provider) {
        auth.json_request(API_URL+'provider/')
                .get(function(error, pdata) {
            if(error) throw error;
            provider = pdata;

            pdata.forEach(function(p) {
                url_cache[p.url] = p;
                p.regions.forEach(function(r) {
                    url_cache[r.url] = r;
                    r.zones.forEach(function(z) {
                        url_cache[z.url] = z;
                    });
                });
            });

            get_obj_by_url(url, _then);
        });
        return;
    }

    if (url in provider) {
        _then(provider, undefined);
    }

    auth.json_request(url).get(function(e, o) {
        if (e) throw(e);
        url_cache[o.url] = o;
        _then(o);
    });
}

export function get_obj(o) {
    return get_obj_by_url(o.url);
}


export function cluster_upload(tenant, config_yml, callback) {

    var req_data = JSON.stringify({
            'tenant': tenant,
            'config_yml': config_yml
        });

    console.log("Uploading:", req_data);

    auth.json_request(API_URL+'cluster_upload_yml/')
        .header("Content-Type", "application/json")
        .on('load', r => callback(null, JSON.parse(r.responseText)))
        .on('error', e => callback(e, null))
        .send('POST', req_data);
}

// Used by selections
export function data_class(d) {
    return model_class(d.data);
}

export function method() {
    return multimethod().dispatch(model_class);
}

export function class_method() {
    return multimethod().dispatch(data_class);
}

export function is_instance(filter) {
    return multimethod().dispatch(data_class)
        .when(filter, true).default(false);
}

export function load_provider() {
    return ; // TODO
}
