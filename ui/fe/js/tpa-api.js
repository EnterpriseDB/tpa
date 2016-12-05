
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

/**
 * Tools for accessing the TPA API via the REST server.
 */

var tpa = (function() {
    var api = {};


    api.url = "/api/v1/tpa/";
    api.provider = null;
    api.url_cache = {};


    api.TEST_TENANT = api.url + "tenant/d9073da2-138f-4342-8cb8-3462be0b325a/";
    api.TEST_CLUSTER = api.url + "cluster/3beb6124-a95d-4625-8d2f-48835803ff2b/";


    api.model_class = function(d) {
        if ( d && d.url) {
            var api_idx = d.url.indexOf(api.url);
            if (api_idx >= 0) {
                obj_path = d.url.slice(api_idx+api.url.length);
                next_slash = obj_path.indexOf("/");
                return obj_path.slice(0, next_slash);
            }
        }

        return null;
    };

    api.get_obj_by_url = function(url, _then) {
        if (api.url_cache[url]) {
            _then(api.url_cache[url]);
            return;
        }

        if (!api.provider) {
            d3.json(api.url+'provider/', function(pdata, e) {
                if(e) throw e;
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

        d3.json(url, function(o, e) {
            if (e) throw(e);
            api.url_cache[o.url] = o;
            _then(o);
        });
    };

    api.get_obj = function(o) {
        return api.get_obj_by_url(o.url);
    };


    // Used by selections
    api.data_class = function(d) {
        return api.model_class(d.data);
    };

    api.method = function() {
        return multimethod().dispatch(api.model_class);
    };

    api.class_method = function() {
        return multimethod().dispatch(api.data_class);
    };

    api.load_provider = function() {
        return ; // TODO
    };

    return api;
}());
