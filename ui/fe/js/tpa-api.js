
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

/**
* Tools for accessing the TPA API via the REST server.
*/


import {multimethod} from "./multimethod";
import {JWTAuth} from "./jwt-auth.js";

const API_URL = "/api/v1/tpa/";
const AUTH_URL = API_URL+"auth/";

const ROLES_BY_PRIORITY = [
        'primary',
        'replica',
        'barman',

/*
 * TODO Roles require further specification.
 *
        'bdr',
        'control',
        'gtm',
        'coordinator',
        'datanode',
        'datanode-replica',
        'log-server',
        'monitor',
        'pgbouncer',
        'witness',
        'openvpn-server',
        'adhoc',
*/

];


// Default provider data (currently only EC2)
var default_provider = null;

export const auth = new JWTAuth(AUTH_URL);

// url -> obj
const url_cache = {};

// API Operations

export function get_obj_by_url(url, _then) {
    if (url_cache[url]) {
        if (_then) {
            _then(url_cache[url]);
        }
        return;
    }

    if (!auth.logged_in) {
        auth.display_login(() => get_obj_by_url(url, _then));
        return;
    }

    if (!default_provider) {
        load_provider(() => get_obj_by_url(url, _then));
        return;
    }

    auth.json_request(url).get(function(error, o) {
        if (error) {
            console.log("API fetch error:", error, "url:", url);
            if (error.currentTarget.status == 403) {
                auth.display_login(() => get_obj_by_url(url, _then));
            }
            else if (error.currentTarget.status == 404) {
                alert("No such object.");
            }
            else {
                alert("Server load error. Please try again later.");
            }

            return;
        }

        console.log("API get URL:", url);
        url_cache[o.url] = o;
        if (_then) {
            _then(o);
        }
    });
}

export function class_to_url(cls) {
    return `${API_URL}${cls}/`
}

export function uuid_to_url(cls, uuid) {
    return `${API_URL}${cls}/${uuid}/`
}

function json_to_form(json_object) {
    let form = new FormData();
    for (let key in json_object) {
        if (json_object.hasOwnProperty(key)) {
            console.log("key", key, "val:", json_object[key]);
            form.append(key, json_object[key]);
        }
    }
    console.log("Form:", form);
    return form;
}

export function object_get(cls, uuid, callback) {
    return auth.json_request(`${API_URL}${cls}/${uuid}/`)
        .get(callback);
}

export function object_update(cls, uuid, json_object, callback) {
    return auth.json_request(`${API_URL}${cls}/${uuid}/`)
        .header("Content-Type", "application/json")
        .post(JSON.stringify(json_object), callback);
}

export function object_create(cls, json_object, callback) {
    return auth.json_request(`${API_URL}${cls}/`)
        .header("Content-Type", "application/json")
        .post(JSON.stringify(json_object), callback);
}
}


export function load_provider(callback) {
    auth.json_request(`${API_URL}provider/`).get((error, providers) => {
        if(error) {
            if (error.currentTarget.status == 403) {
                console.log("Returned 403");
                auth.display_login(() => load_provider(callback));
            }
            else {
                console.log(error);
            }
            return;
        }

        default_provider = providers;
        providers.forEach(p => link_provider(p));
        callback();
    });
}


function link_provider(provider) {
    url_cache[provider.url] = provider;
    provider.regions.forEach(region => {
        url_cache[region.url] = region;
        region.provider = provider;
        region.zones.forEach(zone => {
            url_cache[zone.url] = zone;
            zone.region = region;
            for(let it of zone.instance_types) {
                url_cache[it.url] = it;
            }
        });
    });
}


function link_cluster(cluster) {
    for (let subnet of cluster.subnets) {
        subnet.zone = url_cache[subnet.zone];
        for (let instance of subnet.instances) {
            instance.subnet = subnet;
            instance.zone = subnet.zone;
            instance.instance_type = url_cache[instance.instance_type];
        }
    }
}


export function get_all(klass, filter, _then) {
    // TODO: implement filtering.
    return get_obj_by_url(`${API_URL}${klass}/`, objects => {
        for (let o of objects) {
            if (model_class(o) == 'cluster') {
                link_cluster(o);
            }
        }
        _then(objects);
    });
}


export function get_cluster_by_uuid(cluster_uuid, _then) {
    return get_obj_by_url(
        `${API_URL}cluster/${cluster_uuid}/`, c => {
            link_cluster(c);
            _then(c);
        });
}


export function cluster_upload(tenant, config_yml, callback) {
    var req_data = new FormData();
    req_data.append("tenant", tenant);
    req_data.append("config_yml", config_yml);

    auth.request(class_to_url('cluster_upload_yml'))
        .header("Content-Type", "application/x-www-form-urlencoded")
        .post(req_data, callback);
}


// Reflection


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


/**
 * Returns the primary role of this instance, or undefined if no relevant
 * roles are found.
 */
export function instance_role(instance) {
    for (let primary_role_name of ROLES_BY_PRIORITY) {
        for (let role of instance.roles) {
            if (role && role.role_type == primary_role_name) {
                return role;
            }
        }
    }

    return undefined;
}


export function subnet_has_primary(subnet) {
    for (let instance of subnet.instances) {
        if (instance_role(instance).role_type == 'primary') {
            return true;
        }
    }

    return false;
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

// forms


