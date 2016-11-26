
//var test_data_url = "/api/v1/tpa/provider/c2b1c094-03fd-5d95-b7f3-656fc9f62d72/"
var api_url = "/api/v1/tpa/";
var test_data_url = "/test-cluster.json";
var width = 800;
var height = 450;
var diameter = width*2+60;

var root = null;
var tree = d3.tree().size([height, width-160])
        .separation(function(a, b) {
            switch (model_class(b)) {
                case 'role':
                    return 0.1;
                default:
                    return 1;
            }
        });

var model_class = function(d) {
    if ( d && d.url && d.url.indexOf(api_url) === 0) {
        obj_path = d.url.slice(api_url.length);
        next_slash = obj_path.indexOf("/");
        return obj_path.slice(0, next_slash);
    }

    return undefined;
};

var data_class = function(d) {
    return model_class(d.data)
}

var class_method = function() {
    return multimethod().dispatch(data_class);
}


d3.json(test_data_url,
    function(model_object, error) {
        if (error) throw error;
        draw_cluster(model_object);
});

var draw_cluster = function (cluster) {
    console.log("Cluster data:", cluster);

    root = d3.hierarchy([cluster], multimethod().dispatch(model_class)
        .when("cluster", function(c) {
            return c.instance_set;
        })
        .when("instance", function(i) {
            return i.instance_set;
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
            console.log("edge data for:", model_class(d.data), d);

            return "M" + d.y + "," + d.x
                + "C" + (d.parent.y + 200) + "," + d.x
                + " " + (d.parent.y + 200) + "," + d.parent.x
                + " " + d.parent.y + "," + d.parent.x;
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

                console.log(d, circle);
                return circle;
            }));

    node.append("text")
        .attr("class", "name")
        .attr("dy", 3)
        .attr("x", 10)
        //.attr("x", function(d) { return d.children ? -8 : 8; })
        //.style("text-anchor", function(d) { return d.children ? "end" : "start"; })
        .attr("transform", function(d) {
            return "translate(0, -20)";
        })
        .text(function(d) {
            return d.data.name;
        });
    node.append("text")
        .attr("class", "type")
        .attr("dy", -3)
        .attr("x", 20)
        //.attr("x", function(d) { return d.children ? -8 : 8; })
        //.style("text-anchor", function(d) { return d.children ? "end" : "start"; })
        .attr("transform", function(d) {
            return "translate(0, 20)";
        })
        .text(function(d) {
            return model_class(d.data);
        });

};
