
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
                    if (!(i.url in instance_parents)) {
                        instance_parents[i.url] = l;
                        accum.push([i, l]);
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
            if (!(i.url in instance_parents)) {
                accum.push([i, s]);
                instance_parents[i] = s.url;
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

    return [result, parent_id];
};

var draw_cluster = function (cluster) {
    var [objects, parent_id] = dgm_objects(cluster);

    var table = d3.stratify()
                    .id(function(d) { return d.url; })
                    .parentId(function(d) { return parent_id[d.url]; })
                (objects);

    root = d3.hierarchy(table);

    // remove the double-reference introduced by stratify
    root.data = root.data.data;
    root.descendants().forEach(function(d) {
        d.data = d.data.data;
    });

    tree(root);

    global_cluster = cluster;
    console.log("Cluster data:", cluster, 'table', table);
    d3.select('.cluster_name').text(": " + cluster.name);

    var svg = d3.select(".cluster_view")
        .append('svg')
            .attr('width', width)
            .attr('height', height);

    g = svg.append("g").attr("transform", "translate(50,0) scale(0.8)");

    var node_model = d3.local();
    var node_url = d3.local();
    var node_size = d3.local();
    var node_rect = d3.local();

    var role_idx = d3.local();

    var display_role_list = function(s) {
        s.data(root.descendants().filter(tpa.class_method()
            .when('instance', true).default(false)))
        .enter().append('g')
        .classed('roles', true)
        .attr('transform', function(d) {return "translate("+d.y+","+d.x+")";})
        .each(function(d) {
            node_model.set(this, d);
            role_idx.set(this, {idx: 0});

            var sel = d3.select(this).selectAll(".role")
                .data(d.data.roles)
                .enter().append("text");

            sel.classed("role", true)
                .attr('transform', function(r) {
                    var idx = role_idx.get(this).idx;
                    var top = idx*15;
                    role_idx.get(this).idx = idx+1;
                    return "translate("+0+","+top+")";
                })
                .text(function(r) {
                    return r.name;
                });
        });
        return s;
    };

    var node = g.selectAll(".node")
        .data(root.descendants().filter(tpa.class_method()
            .when('instance', true).default(false)
        ))
        .enter().append("g")
            .attr("class", function(d) {
                return "node" + (d.children ?
                    " node--internal" : " node--leaf"); })
            .attr("transform", function(d) {
                return "translate(" + d.y +','+d.x + ")"; })
            .property('model-url', function(d) {
                return d.data.url ? d.data.url : null;
            })
        .each(function(d) {
            var h = 80, w = 100;
            node_model.set(this, d.data);
            node_url.set(this, d.data.url);
            node_size.set(this, [w, h]);
            node_rect.set(this, {
                 top_left:       {   x:   -w/2,   y:   -h/2    },
                 top_right:      {   x:   +w/2,   y:   -h/2    },
                 bottom_right:   {   x:   +w/2,   y:   +h/2,   },
                 bottom_left:    {   x:   -w/2,   y:   +h/2    }
            });

        });

    g.selectAll(".roles").call(display_role_list);

    // ellipse
    node.append("path")
        .classed('container_shape', true)
        .attr('d', tpa.class_method()
            .when('instance', function(d) {
                var rect = node_rect.get(this);
                var path = d3.path(), width, height, radius;
                [width, height] = node_size.get(this);
                radius = width/2;

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
        .classed("name", true)
        .attr("transform", function(d) {
            return "translate(-50, -20)";
        })
        .text(function(d) {
            return d.data.name;
        });

    // EDGES

    var edge = g.selectAll(".edge")
        .data(root.descendants().filter(function(d) {
            var val = tpa.class_method()
                    .when('rolelink', function(l) { return true; })
                    .default(false);
            return val;
        }))
        .enter().append("path")
        .classed("edge", true)
        .attr("d", function(d) {
            // draw line from server instance to client instance
            var path = d3.path();
            if ( !d.parent ) return "";
            path.moveTo(d.y, d.x);
            path.bezierCurveTo(d.parent.y+200, d.x,
                                d.y-100, d.x,
                                d.parent.y, d.parent.x);

            return path;
        });
};
