
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

/**
* Tools for accessing the TPA API via the REST server.
*/


import {multimethod} from "./multimethod";
import {JWTAuth} from "./jwt-auth";


// Constants and Globals

const API_URL = "/api/v1/tpa/";
const AUTH_URL = API_URL+"auth/";

const ROLES_BY_PRIORITY = [
        'primary',
        'replica',
        'barman',
/* TODO Roles require further specification.

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

// Model

export function model_class(d) {
    if ( !(d && d.url) ) { return null; }

    let api_idx = d.url.indexOf(API_URL);
    if (api_idx < 0) { return null; }

    let obj_path = d.url.slice(api_idx+API_URL.length);
    let next_slash = obj_path.indexOf("/");
    return obj_path.slice(0, next_slash);
}

export function class_to_url(cls) {
    return `${API_URL}${cls}/`
}

export function uuid_to_url(cls, uuid) {
    return `${API_URL}${cls}/${uuid}/`
}

export function method() {
    return multimethod().dispatch(model_class);
}

// Turn the url into a model name and maybe an object uuid
export function window_model() {
    let dir_names = window.location.pathname.split('/');

    let info = {
        model: dir_names[1],
        uuid: dir_names[2],
    };

    let api_path = dir_names.slice(1, 3).filter(d => d).map(d => d+"/").join("");

    if (api_path) {
        info.api_url = `${API_URL}${api_path}`;
    }

    return info;
}

// API authentication
//

export const auth = new JWTAuth(AUTH_URL);


// Basic API Operations
//

export function object_get(cls, uuid, callback) {
    return auth.json_request(`${API_URL}${cls}/${uuid}/`)
        .get(callback);
}

export function object_setattr(obj, attr, value, callback) {
    let cls = model_class(obj), uuid = obj.uuid;
    return auth.json_request(`${API_URL}${cls}/${uuid}/`)
        .header("Content-Type", "application/json")
        .send("PATCH", JSON.stringify({[attr]: value}), callback);
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

export function object_list(cls, filter, callback) {
    let filter_text = filter ? `?${filter}` : "";
    return auth.json_request(`${API_URL}${cls}/${filter_text}`)
        .header("Content-Type", "application/json")
        .get(callback);
}

export function json_to_form(json_object) {
    let form = new FormData();
    for (let key in json_object) {
        if (json_object.hasOwnProperty(key)) {
            form.append(key, json_object[key]);
        }
    }
    return form;
}


// TPA operations providing linking when fetching deeply serialized objects.
//

const link_object = method();
const url_cache = {};
export var default_provider = null;


export function get_obj_by_url(url, _then, allow_cache=true) {
    if (allow_cache && url_cache[url]) {
        if (_then) {
            _then(url_cache[url]);
        }
        return;
    }

    auth.logged_in_or_redirect('/login/');

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
            if (error.currentTarget.status == 403) {
                auth.display_login(() => get_obj_by_url(url, _then));
            }
            else if (error.currentTarget.status == 404) {
                alert("No such object.");
            }
            else {
                console.log("Server error", error);
                alert("Server load error. Please try again later.");
            }

            return;
        }

        if (o.url) {
            link_object(o);
        }

        url_cache[o.url] = o;
        if (_then) {
            _then(o);
        }
    });
}


export function get_all(klass, filter, _then) {
    // TODO: implement filtering.
    return get_obj_by_url(class_to_url(klass), objects => {
        objects.each(link_object);
        _then(objects);
    });
}


// Provider data

export function load_provider(callback) {
    auth.json_request(`${API_URL}provider/`).get((error, providers) => {
        if(error) {
            if (error.currentTarget.status == 403) {
                auth.display_login(() => load_provider(callback));
            }
            else {
                console.log(error);
            }
            return;
        }

        default_provider = providers;
        providers.forEach(link_object);
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

    return provider;
}

link_object.when('provider', link_provider);


// Cluster data

function link_cluster(cluster) {
    for (let subnet of cluster.subnets) {
        subnet.zone = url_cache[subnet.zone];
        for (let instance of subnet.instances) {
            instance.subnet = subnet;
            instance.zone = subnet.zone;
            instance.instance_type = url_cache[instance.instance_type];
        }
    }

    return cluster;
}

link_object.when('cluster', link_cluster);


export function cluster_create(json_object, callback) {
    return auth.json_request(class_to_url('cluster')+"import")
        .post(json_to_form(json_object), callback);
};


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

// Instance

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

// Subnet

export function subnet_has_primary(subnet) {
    for (let instance of subnet.instances) {
        if (instance_role(instance).role_type == 'primary') {
            return true;
        }
    }

    return false;
}
