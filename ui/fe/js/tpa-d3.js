
import * as d3 from "d3";
import * as tpa from "./tpa-api";
import {scaleLinear} from "d3-scale";

//const d3_scale = require('d3-scale');


function show_clusters(tenant, selection, width, height) {
    var clusters = [];
    var current_cluster_idx = -1;


    tpa.get_obj_by_url(tpa.url+"cluster/", function(c, e) {
        if (e) {
            alert("API Server communication error");
            throw e;
        }
        clusters = c;

        if (clusters.length > 0) {
            current_cluster_idx = 0;
            draw_cluster(clusters[current_cluster_idx],
                        selection, width, height);
        }
    });

    function next_cluster() {
        if (clusters.length < 1) {
            return;
        }

        current_cluster_idx = current_cluster_idx+1;
        if (current_cluster_idx >= clusters.length) {
            current_cluster_idx = 0;
        }
        draw_cluster(clusters[current_cluster_idx], selection, width, height);

    }

    return next_cluster;
}


/**
 * Returns the minimum and maximum Y values for the descendants of this
 * diagram element.
 */
function node_yspan(d) {
    return {min_y: d3.min(d.descendants().map(c => c.y)),
            max_y: d3.max(d.descendants().map(c => c.y+height))
            };
}


/**
 * Returns the objects and their parents relevant to drawing a cluster
 * as a tree.
 */
function dgm_objects(cluster) {
    var accum = [], objects = [], parent_id = {};

    var regions = [];
    var instances_in_zone = [];

    var roles = {};
    var instance_parents = {};

    cluster.subnets.forEach(s =>
        s.instances.forEach(i =>
            i.roles.forEach(function(r) { roles[r.url] = i; })
        ));

    accum.push([cluster, ""]); // Cluster is root

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

    cluster.subnets.forEach(
        s => s.instances.filter(i => !(i.url in instance_parents))
            .forEach(function(i) {
                accum.push([i, s]);
                instance_parents[i] = s.url;
            }));

    accum.filter(v => (v[0] in parent_id? false : true))
        .forEach(function([o, p]) {
            objects.push(o);
            parent_id[o.url] = p.url;
        });

    return [objects, parent_id];
}


function tree_layout(objects, parent_id, width, height) {
    var table = d3.stratify().id(d=> d.url).parentId(d => parent_id[d.url])
                (objects);
    var root = d3.hierarchy(table);
    var tree = d3.cluster()
                .size([height, width])
                .nodeSize([height/10, width/10]);


    tree(root);

    var diagram_left = root.y;

    root.descendants().forEach(function(d) {
        // rotate 90 deg, assume root is not displayed
        let x = (d.y ? d.y : 0),
            y = (d.x ? d.x : 0);

        d.x = x - diagram_left;
        d.y = y;

        // remove the double-reference introduced by stratify
        d.data = d.data.data;
    });

    console.log("objects:", objects);
    console.log("parents:", parent_id);
    console.log("root:", root);

    return {tree: tree, root: root};
}


function setup_viewport(selection, width, height) {
    var vp_size = {width: width*2, height: height*2};
    selection.selectAll("svg").remove();

    var svg = selection.append('svg')
        .classed("diagram-viewport", true)
        .attr('width', width)
        .attr('height', height);

    var viewport_contents = svg.append('g');

    // Zoom

    var zoom = d3.zoom()
        //.scaleExtent([0.5, 40])
        .translateExtent([[-width/2, -height/2], [width*2, height*2]])
        .on("zoom", () => viewport_contents.attr("transform", d3.event.transform));

    svg.call(zoom);

    var diagram = viewport_contents.append("g")
        .classed("diagram", true)
        .attr('transform', `translate(${width/2}, ${height/2})`);

    return {svg: svg, diagram: diagram};
}



function draw_cluster(cluster, selection, width, height) {
    console.log("draw_cluster:", cluster, width, height);

    var viewport = setup_viewport(selection, width, height);

    var [objects, parent_id] = dgm_objects(cluster);
    var layout = tree_layout(objects, parent_id, width, height);
    var tree = layout.tree;
    var root = layout.root;

    var g = viewport.diagram;
    draw_background_grid(g, root.y, width, height);

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
            let path = d3.path();
            let p = d.parent, c = d.children[0];
            let y1 = p.y, y2 = c.y;
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


    // Zone
    var zone_display = g.selectAll(".diagram--zone")
        .data(root.descendants().filter(tpa.class_method()
            .when('zone', true).default(false)
        ))
        .enter().append('g')
            .attr("class", d => "diagram--zone" +
                (d.children ? "" : " diagram--zone--empty"))
            .attr("transform", d => `translate(${-root.x}, ${d.y})`)
            .property('model-url', d => d.data.url ? d.data.url : null);

    zone_display.append("text")
            .text(d => tpa.url_cache[d.data.url].name);

    var zone_sep_y = d3.local();

    zone_display.append('line')
        .classed('diagram--zonesep', true)
        .attr('x1', 0)
        .attr('y1', function (d) {
            let desc = d.descendants();
            let y = d.y + desc[desc.length-1].y + (10 + tree.nodeSize[0]) ;
            zone_sep_y.set(this, y);
            return  y;
        })
        .attr('x2', width)
        .attr('y2', function (d) { return zone_sep_y.get(this); });

    // Instances

    var node = g.selectAll(".node")
        .data(root.descendants().filter(tpa.class_method()
            .when('instance', true).default(false)
        ))
        .enter().append("g")
            .attr("class", d => "node" +
                (d.children ? " node--internal" : " node--leaf"))
            .attr("transform", d => `translate(${d.x}, ${d.y})`)
            .property('model-url', d => d.data.url ? d.data.url : null)
        .each(function(d) {
            var h = 25+14*(d.data.roles.length+1),
                w = 8*(d.data.name.length+1);
            node_model.set(this, d.data);
            node_url.set(this, d.data.url);
            node_size.set(this, {width: w, height: h});
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
                var ns = node_size.get(this);
                var path = d3.path();
                var pointy_size = d3.min(ns.height, ns.width*3.0/4.0);

                path.moveTo(rect.top_right.x, rect.top_right.y);

                path.quadraticCurveTo(rect.top_right.x+ns.height/2.5, 0,
                                    rect.bottom_right.x, rect.bottom_right.y);
                path.lineTo(rect.bottom_left.x, rect.bottom_left.y);

                path.quadraticCurveTo(rect.bottom_left.x-ns.height/2.3, 0,
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
                var radius = ns.height/4;
                var circle = "M "+ (-(ns.width/2+ns.height/2)) +" 0 " +
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
            return "translate("+(-ns.width/3)+", " + (-ns.height/2+20) + ")";
        })
        .text(d => d.data.name);

    // roles
    var role_idx = d3.local();

    var dgm_roles = node.append("g")
        .classed('roles', true)
        .attr('transform', function(d) {
            var x = -node_size.get(this).width/4,
                y = -node_size.get(this).height/2+25;

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

    function diagram_data_item(selection, el_name, data_class, data) {
        return selection.selectAll("."+data_class)
                .data(data).enter().append(el_name)
                .classed(data_class, true)
                .property('model:url', d => d.url);
    }

    dgm_roles.each(function(d) {
        role_idx.set(this, {idx: 1});

        diagram_data_item(d3.select(this), 'text', 'role', d.data.roles)
            .attr('transform', function(r) {
                var ns = node_size.get(this);
                var idx = role_idx.get(this).idx;
                var top = 15+(idx-1)*15;
                role_idx.get(this).idx = idx+1;
                return "translate("+"4"+","+top+")";
            })
            .text(function(r) { return r.name; });
    });
}

function draw_instance(selection, i) {
}


function draw_background_grid(selection, cy, width, height) {
    var yScale = scaleLinear()
        .domain([-height/2, height*1.5])
        .range([cy-500, cy+500]);

    selection.append('g')
        .classed('background-grid', true)
        .selectAll("line.horizontalGrid")
        .data(yScale.ticks(50)).enter()
        .append("line")
            .classed('horizontalGrid', true)
            .attr("x1", -width)
            .attr("x2", width)
            .attr("y1", yScale)
            .attr("y2", yScale);
}


exports.show_clusters = show_clusters;

