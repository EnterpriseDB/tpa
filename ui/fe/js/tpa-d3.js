
var global_cluster = null;

/* Renderer */

var show_clusters = function (tenant, selection, width, height) {
    var clusters = [];
    var current_cluster_idx = -1;


    tpa.get_obj_by_url(tpa.url+"cluster/", function(c, e) {
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

    var regions = [];
    var instances_in_zone = [];

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

    // Regions and zones

    cluster.subnets.forEach(function(s) {
        var subnet_zone = {url: s.zone};
        accum.push([subnet_zone, cluster]);
        accum.push([s, subnet_zone]);

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
    });

    cluster.subnets.forEach(function(s) {
        s.instances.forEach(function(i) {
            if (!(i.url in instance_parents)) {
                accum.push([i, s]);
                instance_parents[i] = s.url;
            }
        });
    });


    accum.forEach(function(v) {
        console.log("accum:", v);
        var o=v[0], p=v[1];

        var url = o.url;

        if (url in parent_id) {
            return;
        }

        result.push(o);
        parent_id[url] = p.url;
    });

    return [result, parent_id];
};

var draw_cluster = function (cluster, selection, width, height) {
    console.log("draw_cluster:", cluster);
    var dgm = dgm_objects(cluster);

    var objects = dgm[0];
    var parent_id = dgm[1];

    // MAKE TREE
    //
    var table = d3.stratify()
                    .id(function(d) { return d.url; })
                    .parentId(function(d) { return parent_id[d.url]; })
                (objects);
    var root = d3.hierarchy(table);
    var tree = d3.cluster()
                .size([height*0.2, width*0.8])
                .nodeSize([width/10, height/10]);

    tree(root);

    console.log('table', table);
    console.log("before:", root.x, root.y);

    var root_x = root.y,
        root_y = root.x;

    root.x = 0;
    root.y = root_y;

    console.log("after:", root.x, root.y);

    root.data = root.data.data;

    root.descendants().forEach(function(d) {
        // rotate 90 deg, assume root is not displayed
        var x=d.y, y=d.x;
        d.x=x-root.x;
        d.y=y;

        // remove the double-reference introduced by stratify
        d.data = d.data.data;
    });

    console.log("objects:", objects);
    console.log("parents:", parent_id);
    console.log("root:", root);

    global_cluster = cluster;

    // RENDER IT
    selection.selectAll("svg").remove();

    var svg = selection.append('svg')
        .attr('width', width)
        .attr('height', height);

    g = svg.append("g")
            .classed("diagram", true);

    // Background grid
    var yScale = d3.scale.linear()
        .domain([-height/2, height*1.5])
        .range([root.y-500, root.y+500]);

    g.selectAll("line.horizontalGrid").data(yScale.ticks(50)).enter()
        .append("line")
            .attr("class", "horizontalGrid")
            .attr("x1", -width)
            .attr("x2", width)
            .attr("y1", yScale)
            .attr("y2", yScale);

    // Zoom

    var zoom = d3.zoom()
        .scaleExtent([0.5, 40])
        .translateExtent([[-width/2, -height/2], [width*2, height*2]])
        .on("zoom", function () { g.attr("transform", d3.event.transform); });

    svg.call(zoom);

    // Locals

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


    var zone_node = g.selectAll(".diagram-zone")
        .data(root.descendants().filter(tpa.class_method()
            .when('zone', true).default(false)
        ))
        .enter().append("text")
            .attr("class", function(d) {
                console.log("zone:", d);
                return "diagram--zone" + (d.children ?
                    "" : " diagram--zone--empty"); })
            .attr("transform", function(d) {
                return "translate(" + 0 +','+d.y + ")"; })
            .property('model-url', function(d) {
                return d.data.url ? d.data.url : null;
            })
            .text(function(d) { return tpa.url_cache[d.data.url].name; });

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
            var h = 25+14*(d.data.roles.length+1),
                w = 8*(d.data.name.length+1);
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

    // ellipse
    node.append("path")
        .classed('container_shape', true)
        .attr('d', tpa.class_method()
            .when('instance', function(d) {
                var rect = node_rect.get(this);
                var path = d3.path(), n_h = node_size.get(this)[1];
                var pointy_size = d3.min(n_h, node_size.get(this)[0]*3.0/4.0);

                path.moveTo(rect.top_right.x, rect.top_right.y);
                path.quadraticCurveTo(rect.top_right.x+n_h/2.5, 0,
                                    rect.bottom_right.x, rect.bottom_right.y);
                path.lineTo(rect.bottom_left.x, rect.bottom_left.y);
                path.quadraticCurveTo(rect.bottom_left.x-n_h/2.3, 0,
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
                var ns = node_size.get(this);
                var radius = ns[1]/4;
                var circle = "M "+ (-(ns[0]/2+ns[1]/2)) +" 0 " +
                    " m "+radius+", 0" +
                    " a "+radius+","+radius+" 0 1,1 "+(2*radius)+",0" +
                    " a "+radius+","+radius+" 0 1,1 "+(-2*radius)+",0";
                return circle;
            }));

    // name
    node.append("text")
        .classed("name", true)
        .attr("transform", function(d) {
            var ns = node_size.get(this);
            return "translate("+(-ns[0]/3)+", " + (-ns[1]/2+20) + ")";
        })
        .text(function(d) {
            return d.data.name;
        });

    // roles
    var role_idx = d3.local();

    var dgm_roles = node.append("g")
        .classed('roles', true)
        .attr('transform', function(d) {
            var x = -node_size.get(this)[0]/4,
                y=-node_size.get(this)[1]/2+25;

            return "translate("+x+","+y+")";
        });

    /*
     * FIXME: needs to resize to text corectly.
    dgm_roles.append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', function (d) {
            return 8+8*d3.max(d.data.roles.map(function(r) {
                return r.name.length;
            }));
        })
        .attr('height', function (d) {
            return 20*d.data.roles.length;
        });
    */

    dgm_roles.each(function(d) {
            role_idx.set(this, {idx: 1});

           d3.select(this).selectAll(".role")
                .data(d.data.roles)
                .enter().append("text")
                    .classed("role", true)
                    .attr('transform', function(r) {
                        var ns = node_size.get(this);
                        var idx = role_idx.get(this).idx;
                        var top = 15+(idx-1)*15;
                        role_idx.get(this).idx = idx+1;
                        return "translate("+"4"+","+top+")";
                    })
                    .text(function(r) {
                        return r.name;
                    });
        });
};
