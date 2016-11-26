
//var test_data_url = "/api/v1/tpa/provider/c2b1c094-03fd-5d95-b7f3-656fc9f62d72/"
var api_url = "/api/v1/tpa/";
var test_data_url = "/test-cluster-extended.json";
var width = 800;
var height = 450;
var diameter = width*2+60;

var root = null;
var tree = d3.cluster().size([height, width-160])
        .separation(function(a, b) {
                return 0.1;
        });

//d3.select('.treeview').call(d3.zoom().on("zoom", zoomed));

/* Support for json structure */

var model_class = function(d) {
    if ( d && d.url && d.url.indexOf(api_url) === 0) {
        obj_path = d.url.slice(api_url.length);
        next_slash = obj_path.indexOf("/");
        return obj_path.slice(0, next_slash);
    }

    return undefined;
};

var data_class = function(d) {
    return model_class(d.data);
};

var class_method = function() {
    return multimethod().dispatch(data_class);
};

/* Renderer */

d3.json(test_data_url,
    function(model_object, error) {
        if (error) throw error;
        draw_cluster(model_object);
});

var draw_cluster = function (cluster) {
    console.log("Cluster data:", cluster);

    d3.select('.cluster_name').text(cluster.name);

    root = d3.hierarchy([cluster], multimethod().dispatch(model_class)
        .when("cluster", function(c) {
            return c.instance_set;
        })
        .when("instance", function(i) {
            return i.role_set;
        })
        .default(function(d) {
            if (d.length && d.length > 0) {
                return d;
            }

            return null;
        }));

    tree(root);

    var svg = d3.select(".treeview")
    .attr('width', diameter)
    .attr('height', diameter);

    g = svg.append("g").attr("transform", "translate(60,0)");

    //var stratify = d3.stratify()
    //    .parentId(function(d) { return d.id.substring(0, d.id.lastIndexOf(".")); });

    var edge = g.selectAll(".edge")
        .data(root.descendants().slice(1))
        .enter().append("path")
        .attr("class", "edge")
        .attr("d", function(d) {
            var path = d3.path();
            path.moveTo(d.y, d.x);
            path.bezierCurveTo(d.parent.y+200, d.x,
                                d.y-100, d.x,
                                d.parent.y, d.parent.x);

            return path;
        });

    var node = g.selectAll(".node")
        .data(root.descendants())
        .enter().append("g")
        .attr("class", function(d) { 
            return "node" + (d.children ? 
                " node--internal" : " node--leaf"); })
        .attr("transform", function(d) {
            return "translate(" + d.y +','+d.x + ")";
        });

    node.append("path")
        .attr('url', function(d) {
            return d.data.url ? d.data.url : null;
        })
        .attr('class', function(d) {
            var cls = model_class(d.data);
            if (cls) {
                return "node " + cls;
            }
            return "node";
        })
        .attr('d', class_method()
            .default(function(d) {
                var radius = 5;

                var circle = "M 0 0 "
                    + " m "+radius+", 0"
                    + " a "+radius+","+radius+" 0 1,1 "+(2*radius)+",0"
                    + " a "+radius+","+radius+" 0 1,1 "+(-2*radius)+",0";
                return circle;
            }));

    node.append("text")
        .attr("class", "name")
        .attr("dy", 3)
        .attr("x", 10)
        .attr("transform", function(d) {
            return "scale(1.2, 1.2) translate(0, -20)";
        })
        .text(function(d) {
            return d.data.name;
        });

    node.append("text")
        .attr("class", "model_class")
        .attr("dy", -3)
        .attr("x", 20)
        .attr("transform", function(d) {
            return "translate(50, -20)";
        })
        .text(function(d) {
            return model_class(d.data);
        });

};
