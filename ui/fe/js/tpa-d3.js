
//var test_data_url = "/api/v1/tpa/provider/c2b1c094-03fd-5d95-b7f3-656fc9f62d72/"
var global_cluster = null;
var width = 1000;
var height = 450;

var root = null;
var tree = d3.cluster().size([height, width-100])
        .separation(function(a, b) {
            return Math.min(5-b.depth, 1);
        });

//d3.select('.treeview').call(d3.zoom().on("zoom", zoomed));


/* Renderer */

var dgm_objects = function(cluster) {
    var accum = [], result = [], parent_id = {};

    var roles = {};
    var instance_parents = {};
    var instance_children = {};

    cluster.subnets.forEach(function(s) {
        s.instances.forEach(function(i) {
            i.roles.forEach(function(r) {
                roles[r.url] = i;
            });
        });
    });

    cluster.subnets.forEach(function(s) {
        accum.push([s, ""]);
        s.instances.forEach(function(i) {
            i.roles.forEach(function(r) {
                r.client_links.forEach(function(l) {
                    var other_end = roles[l.server_role];
                    // set my ancestor to this link
                    if (i == other_end) {
                        return;
                    }
                    if (!(i in instance_parents)) {
                        instance_parents[i] = l;
                        accum.push([i, l])
                    }
                    // set link's ancestor to other instance
                    accum.push([l, other_end]);
                });
            });
        });
        //accum.push(s.zone);
        //accum.push(s.zone.region);
    });

    cluster.subnets.forEach(function(s) {
        s.instances.forEach(function(i) {
            console.log("check instance:", i, instance_parents[i]);
            if (! (i in instance_parents[i])) {
                console.log('reparenting');
                accum.push([i, s]);
            }
        });
    });


    accum.forEach(function([o, p]) {
        if (o.url in parent_id) {
            return;
        }
        result.push(o);
        parent_id[o.url] = p.url;
    });

    console.log(roles, result, parent_id, instance_parents);
    return [result, parent_id];
};

var draw_cluster = function (cluster) {
    var [objects, parent_id] = dgm_objects(cluster);

    var table = d3.stratify()
                    .id(function(d) { return d.url; })
                    .parentId(function(d) { return parent_id[d.url]; })
                (objects);

    root = d3.hierarchy(table);
    tree(root);

    global_cluster = cluster;
    console.log("Cluster data:", cluster, 'table', table);
    d3.select('.cluster_name').text(": " + cluster.name);

    var svg = d3.select(".cluster_view")
        .append('svg')
            .attr('width', width)
            .attr('height', height);

    g = svg.append("g").attr("transform", "translate(50,0) scale(0.8)");

    var node_rect = d3.local();
    var node_model = d3.local();

    var edge = g.selectAll(".edge")
        .data(root.descendants().filter(function(d) {
            var val = tpa.class_method()
                    .when('rolelink', function(l) { return true; })
                    .default(false);
            console.log("EDGE:", d, tpa.data_class(d), val(d));
            return val;
        }))
        .enter().append("path")
        .classed("edge", true)
        .attr("d", function(d) {
            var path = d3.path();
            if ( !d.parent ) return "";
            path.moveTo(d.y, d.x);
            path.bezierCurveTo(d.parent.y+200, d.x,
                                d.y-100, d.x,
                                d.parent.y, d.parent.x);

            return path;
        });

    var node = g.selectAll(".node")
        .data(root.descendants().filter(function(d) {
            return tpa.class_method()
                .when('instance', true)
                .default(false)(d);
        }))
        .enter().append("g")
            .attr("class", function(d) {
                return "node" + (d.children ?
                    " node--internal" : " node--leaf"); })
            .attr("transform", function(d) {
                return "translate(" + d.y +','+d.x + ")"; })
            .attr('url', function(d) {
                return d.data.data.url ? d.data.data.url : null;
            });

    // ellipse
    node.append("path")
        .classed('container_shape', true)
        .attr('d', tpa.class_method()
            .when('instance', function(d) {
                var width = 100,
                    height = 80,
                    path = d3.path(),
                    radius = width/2,
                    rect = {
                        top_left: {
                            x: -width/2,
                            y: -height/2
                        },
                        top_right: {
                            x: +width/2,
                            y: -height/2
                        },
                        bottom_right: {
                            x: +width/2,
                            y: +height/2,
                        },
                        bottom_left: {
                            x: -width/2,
                            y: +height/2
                        }
                    };

                path.moveTo(rect.top_right.x, rect.top_right.y);
                path.quadraticCurveTo(rect.top_right.x+width, 0,
                                    rect.bottom_right.x, rect.bottom_right.y);
                path.lineTo(rect.bottom_left.x, rect.bottom_left.y);
                path.quadraticCurveTo(rect.bottom_left.x-width, 0,
                                    rect.top_left.x, rect.top_left.y);
                path.lineTo(rect.top_right.x, rect.top_right.y);
                path.closePath();

                return path;
            }));

    // icon
    node.append("path")
        .classed('icon', true)
        .attr('d', tpa.class_method()
            .default(function(d) {
                var radius = 16;
                var circle = "M -110 0 " +
                    " m "+radius+", 0" +
                    " a "+radius+","+radius+" 0 1,1 "+(2*radius)+",0" +
                    " a "+radius+","+radius+" 0 1,1 "+(-2*radius)+",0";
                return circle;
            }));

    // name
    node.append("text")
        .attr("class", "name")
        .attr("transform", function(d) {
            return "translate(-50, -20)";
        })
        .text(function(d) {
            return d.data.data.name;
        });

    // roles
    node.append("path")
        .classed('role', true)
         .attr("transform", function(d) {
            return "translate(-50, -20)";
        })
        .text(function(d) {
            return d.data.data.name;
        });
};
