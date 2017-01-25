
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

/**
* Tools for accessing the TPA API via the REST server.
*/

import * as d3 from "d3";
import {multimethod} from "./multimethod";

var api = exports;
api.url = "/api/v1/tpa/";

api.TEST_TENANT = api.url + "tenant/d9073da2-138f-4342-8cb8-3462be0b325a/";
api.TEST_CLUSTER = api.url + "cluster/3beb6124-a95d-4625-8d2f-48835803ff2b/";




api.provider = null;
api.url_cache = {};


api.model_class = function model_class(d) {
    if ( d && d.url) {
        var api_idx = d.url.indexOf(api.url);
        if (api_idx >= 0) {
            var obj_path = d.url.slice(api_idx+api.url.length);
            var next_slash = obj_path.indexOf("/");
            return obj_path.slice(0, next_slash);
        }
    }

    return null;
};

api.get_obj_by_url = function get_obj_by_url(url, _then) {
    if (api.url_cache[url]) {
        _then(api.url_cache[url]);
        return;
    }

    if (!api.provider) {
        d3.json(api.url+'provider/', function(error, pdata) {
            if(error) throw error;
            api.provider = pdata;
            console.log("provider data:", pdata);

            pdata.forEach(function(p) {
                api.url_cache[p.url] = p;
                console.log("provider:", p.name);
                p.regions.forEach(function(r) {
                    api.url_cache[r.url] = r;
                    r.zones.forEach(function(z) {
                        api.url_cache[z.url] = z;
                    });
                });
            });

            api.get_obj_by_url(url, _then);
        });
        return;
    }

    if (url in api.provider) {
        _then(api.provider, undefined);
    }

    d3.json(url, function(e, o) {
        if (e) throw(e);
        api.url_cache[o.url] = o;
        _then(o);
    });
};

api.get_obj = function get_obj(o) {
    return api.get_obj_by_url(o.url);
};


// Used by selections
api.data_class = function(d) {
    return api.model_class(d.data);
};

api.method = function method() {
    return multimethod().dispatch(api.model_class);
};

api.class_method = function class_method() {
    return multimethod().dispatch(api.data_class);
};


api.is_instance = function is_instance(filter) {
    return multimethod().dispatch(api.data_class)
        .when(filter, true).default(false);
};

api.load_provider = function load_provider() {
    return ; // TODO
};
