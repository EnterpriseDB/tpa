
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

/**
 * Tools for accessing the TPA API via the REST server.
 */

var tpa = (function() {
    var api = {};

    api.url = "/api/v1/tpa/";

    api.TEST_TENANT = api.url + "tenant/d9073da2-138f-4342-8cb8-3462be0b325a/";
    api.TEST_CLUSTER = api.url + "cluster/8d4ad6a9-e679-4662-acac-ce25e1f4246d/";

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

    api.get_obj = function(o) {
        return d3.promise.json(o.url);
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
        return 
    };

    return api;
}());
