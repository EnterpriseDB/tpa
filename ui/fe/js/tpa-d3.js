
var global_cluster = null;

/* Renderer */

var show_clusters = function (tenant, selection, width, height) {
    var clusters = [];
    var current_cluster_idx = -1;

    d3.json(tpa.url+"cluster/", function(c, e) {
        if (e) { 
            alert("API Server communication error");
            throw e;
        }
        clusters = c;
        console.log("clusters:", c);

        if (clusters.length > 0) {
            current_cluster_idx = 0;
            draw_cluster(clusters[current_cluster_idx],
                        selection, width, height);
        }
    });

    var next_cluster = function () {
        if (clusters.length < 1) {
            return;
        }

        current_cluster_idx = current_cluster_idx+1;
        if (current_cluster_idx >= clusters.length) {
            current_cluster_idx = 0;
        }
        draw_cluster(clusters[current_cluster_idx],
                    selection, width, height);

    };

    return next_cluster;
};


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


    accum.push([cluster, ""]); // Cluster is root

    cluster.subnets.forEach(function(s) {
        accum.push([s, cluster]);
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

var draw_cluster = function (cluster, selection, width, height) {
    var [objects, parent_id] = dgm_objects(cluster);


    // MAKE TREE
    //
    var table = d3.stratify()
                    .id(function(d) { return d.url; })
                    .parentId(function(d) { return parent_id[d.url]; })
                (objects);
    var root = d3.hierarchy(table);
    var tree = d3.cluster().size([height*0.2, width*0.8])
        .separation(function(a, b) {
            return Math.min(5-b.depth, 1);
        });

    tree(root);
    var root_x = root.y, root_y = root.x;
    root.x = root_x;
    root.y = root_y;
    root.data = root.data.data;

    root.descendants().forEach(function(d) {
        // rotate 90 deg, assume root is not displayed
        var x=d.y, y=d.x;
        d.x=x-root.x;
        d.y=y;

        // remove the double-reference introduced by stratify
        d.data = d.data.data;
    });

    global_cluster = cluster;

    // RENDER IT
    selection.selectAll("svg").remove();

    var svg = selection.append('svg')
        .attr('width', width)
        .attr('height', height);

    g = svg.append("g").attr("transform", "translate(0,0) scale(1.0)");

    var node_model = d3.local();
    var node_url = d3.local();
    var node_size = d3.local();
    var node_rect = d3.local();

    // Links

    var edge = g.selectAll(".edge")
        .data(root.descendants().filter(
            tpa.class_method().when('rolelink', true).default(false)))
        .enter().append("path")
        .classed("edge", true)
        .attr("d", function(d) {
            // draw line from server instance to client instance
            if ( !d.parent ) return "";
            var path = d3.path();
            var p = d.parent, c = d.children[0];
            var y1 = p.y, y2 = c.y;
            if (y1 > y2) {
                y1 = c.y;
                y2 = p.y;
            }
            path.moveTo(p.x, p.y);
            path.bezierCurveTo(
                d.x + (d.x-c.x)/3, y1,
                p.x + (d.x-p.x)/3, y2,
                c.x, c.y);
            return path;
        });


    var node = g.selectAll(".node")
        .data(root.descendants().filter(tpa.class_method()
            .when('instance', true).default(false)
        ))
        .enter().append("g")
            .attr("class", function(d) {
                return "node" + (d.children ?
                    " node--internal" : " node--leaf"); })
            .attr("transform", function(d) {
                return "translate(" + d.x +','+d.y + ")"; })
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

    // g.selectAll(".roles").call(display_role_list);

    // ellipse
    node.append("path")
        .classed('container_shape', true)
        .attr('d', tpa.class_method()
            .when('instance', function(d) {
                var rect = node_rect.get(this);
                var path = d3.path(), n_w = node_size.get(this)[0];

                path.moveTo(rect.top_right.x, rect.top_right.y);
                path.quadraticCurveTo(rect.top_right.x+n_w/2.5, 0,
                                    rect.bottom_right.x, rect.bottom_right.y);
                path.lineTo(rect.bottom_left.x, rect.bottom_left.y);
                path.quadraticCurveTo(rect.bottom_left.x-n_w, 0,
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

    // roles
    var role_idx = d3.local();

    node.append("g")
        .classed('roles', true)
        .attr('transform', function(d) {
            var x = -20, y=-15;

            return "translate("+x+","+y+")";
        })
        .each(function(d) {
            role_idx.set(this, {idx: 1});

           d3.select(this).selectAll(".role")
                .data(d.data.roles.slice(0,3))
                .enter().append("text")
                    .classed("role", true)
                    .attr('transform', function(r) {
                        var idx = role_idx.get(this).idx;
                        var top = idx*15;
                        role_idx.get(this).idx = idx+1;
                        return "translate("+"-5"+","+top+")";
                    })
                    .text(function(r) {
                        return r.name;
                    });
        });
};
