
/**
 * Generate SVG diagrams from TPA clusters using d3 and the TPA API.
 */

import * as d3 from "d3";
import * as tpa from "./tpa-api";
import {scaleLinear} from "d3-scale";

var MIN_NODE_WIDTH = 100;


function show_clusters(tenant, selection) {
    var clusters = [];
    var current_cluster_idx = -1;

    var bbox = selection.node().getBoundingClientRect();
    var width = bbox.width;
    var height = bbox.height;

    tpa.get_obj_by_url(tpa.API_URL+"cluster/", function(c, e) {
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


function draw_cluster(cluster, selection, width, height) {
    console.log("draw_cluster:", cluster, width, height,
                tpa.cluster_type(cluster));

    var viewport = setup_viewport(selection, width, height);
    var diagram = viewport.diagram;

    var graph = null;

    if (tpa.cluster_type(cluster) == 'xl') {
        graph = build_xl_graph(cluster);
    } 
    else {
        graph = build_tpa_graph(cluster);
    }

    var [objects, parent_id] = graph; 
    var layout = tree_layout(objects, parent_id, width, height);
    var tree = layout.tree;
    var root = layout.root;

    var dom_context = d3.local();

    draw_background_grid(diagram, root.y, width, height);

    function draw_all_of_class(c, draw) {
        diagram.selectAll("."+c)
        .data(root.descendants().filter(tpa.is_instance(c)))
        .enter()
        .call(d => draw(d, diagram, {width: width, height: height})
            .classed(c, true)
        );
    }

    draw_all_of_class('zone', draw_zone);
    draw_all_of_class('rolelink', draw_rolelink);
    draw_all_of_class('instance', draw_instance);

    d3.select("span.cluster_name").text(cluster.name);
}

function build_xl_graph(cluster) {
    var parent_id = {};
    var objects = [cluster];
    var gtm_instances = [];
    var coord_instances = [];
    var roles = {}; // role url -> instance

    parent_id[cluster.url] =  "";

    cluster.subnets.forEach(function(s) {
        objects.push(s);
        parent_id[s.url] = cluster.url;

        s.instances.forEach(function(i) {
            objects.push(i);

            i.roles.forEach(function(r) {
                roles[r.url] = i;
                if (r.role_type == "gtm") {
                    gtm_instances.push(i);
                    parent_id[i.url] = s.url;
                }
                if (r.role_type == "coordinator") {
                    coord_instances.push(i);
                }
            });
        });
    });

    var gtm_center = gtm_instances[Math.floor(gtm_instances.length/2)];
    var coord_center = (coord_instances.length > 0) ?
            coord_instances[Math.floor(coord_instances.length/2)]
            : gtm_center;

    cluster.subnets.forEach(s =>
        s.instances.filter(i => !(i.url in parent_id))
            .forEach(function(i) {
                i.roles.forEach(function(r) {
                    if (r.role_type == 'datanode-replica') {
                        r.client_links.forEach(function(ln) {
                            if (ln.name == 'datanode-replica') {
                                objects.push(ln);
                                parent_id[ln.url] = roles[ln.server_role].url;
                                parent_id[i.url] = ln.url;
                            }
                        });
                    }
                    else if (r.role_type == 'coordinator') {
                        r.client_links.forEach(function(ln) {
                            if (ln.name == 'gtm') {
                                objects.push(ln);
                                parent_id[ln.url] = roles[ln.server_role].url;
                                parent_id[i.url] = ln.url;
                            }
                        });
                    }
                    else if (r.role_type == 'datanode') {
                        r.client_links.forEach(function(ln) {
                            if (ln.name == 'coordinator' && !(i.url in parent_id)) {
                                objects.push(r);
                                parent_id[r.url] = coord_center.url;
                                parent_id[i.url] = r.url;
                            }
                        });
                    }
                });
                if ( !(i.url in parent_id)) {
                    parent_id[i.url] = coord_center.url;
                }
            }));

    return [objects, parent_id];
}


/**
 * Returns the objects and their parents relevant to drawing a cluster
 * as a tree.
 * 
 * Cluster -> Region -> Zone -> Subnet -> Instance(root) -> 
 * (-> rolelink -> instance)*
 */
function build_tpa_graph(cluster) {
    var accum = [], objects = [], parent_id = {};

    var roles = {};
    var instance_parents = {};

    // Grammar:
    // cluster -> region -> zone -> (subnet?) -> instance 
    //   (-> rolelink -> instance)*

    accum.push([cluster, ""]); // Cluster is root

    // TODO this is needed until the model linker is written
    cluster.subnets.forEach(s =>
        s.instances.forEach(i =>
            i.roles.forEach(function(r) { 
                roles[r.url] = i;
            })
        ));

    cluster.subnets.forEach(function(subnet) {
        var subnet_zone = {url: subnet.zone};
        accum.push([subnet_zone, cluster]);
        accum.push([subnet, subnet_zone]);

        subnet.instances.forEach(function(i) {
            i.roles.forEach(function(r) {
                r.client_links.forEach(function(l) {
                    var server_instance = roles[l.server_role];
                    // set my ancestor to this link
                    if (i == server_instance) {
                        // Client and server on same instance.
                        return;
                    }
                    if (!(i.url in instance_parents)) {
                        instance_parents[i.url] = l;

                        accum.push([i, l]);
                    }
                    // set link's parent to other instance
                    accum.push([l, server_instance]);
                });
            });
        });
    });

    // if an instance has no parent yet, the subnet is its parent.
    cluster.subnets.forEach(
        s => s.instances
            .filter(function(i) { return !(i.url in instance_parents);})
            .forEach(function(i) {
                accum.push([i, s]);
                instance_parents[i] = s.url;
            }));

    // dedupe
    console.log('Accum before dedupe:', accum);

    accum.filter(v => (v[0] in parent_id? false : true))
        .forEach(function([o, p]) {
            objects.push(o);
            parent_id[o.url] = p.url;
        });

    return [objects, parent_id];
}


function draw_zone(selection, zone, size) {
    var zone_sep_y = d3.local();

    var zone_display = selection.append('g')
        .classed('zone--empty',  d => d.children)
        .attr("transform", d => `translate(${-d.parent.x}, ${d.y})`)
        .property('model-url', d => d.data.url ? d.data.url : null);

    zone_display.append("text")
        .text(d => tpa.url_cache[d.data.url].name);

    // display a line between each zone
    /*
    zone_display.append('line')
        .attr('x1', 0)
        .attr('y1', function (d) {
            let y = d3.max(d.descendants().map(e => e.y)) + 20;
            zone_sep_y.set(this, y);
            return  y;
        })
        .attr('x2', size.width)
        .attr('y2', function (d) { return zone_sep_y.get(this); });
    */

    return zone_display;
}

function instance_size(instance) {
    var max_role_length = d3.max(instance.roles.map( r => r.name.length));
    var h = 25+14*(instance.roles.length+1),
        w = d3.max([8*(instance.name.length+1),
                    6*(max_role_length+4),
                    MIN_NODE_WIDTH]);

    return {"width": w, "height": h};
}


function draw_instance(selection, instance) {
    var node_rect = d3.local();
    var node_model = d3.local();
    var node_url = d3.local();
    var MIN_NODE_WIDTH = 100;

    var node = selection.append("g")
        .attr("class", d => "instance node" +
            (d.children ? " node--internal" : " node--leaf"))
        .attr("transform", d => `translate(${d.x}, ${d.y})`)
        .property('model-url', d => d.data.url ? d.data.url : null)
        .each(function(d) {
            var size = instance_size(d.data);
            node_model.set(this, d.data);
            node_url.set(this, d.data.url);
            node_rect.set(this, make_rect(size.width, size.height));
        });

    // ellipse
    node.append("path")
        .classed('container_shape', true)
        .attr('d', function(d) {
            var rect = node_rect.get(this);
            var path = d3.path();
            var pointy_size = d3.min(rect.height, rect.width*3.0/4.0);

            path.moveTo(rect.top_right.x, rect.top_right.y);

            path.quadraticCurveTo(rect.top_right.x+rect.height/2.5, 0,
                                rect.bottom_right.x, rect.bottom_right.y);
            path.lineTo(rect.bottom_left.x, rect.bottom_left.y);

            path.quadraticCurveTo(rect.bottom_left.x-rect.height/2.3, 0,
                                rect.top_left.x, rect.top_left.y);
            path.lineTo(rect.top_right.x, rect.top_right.y);

            path.closePath();

            return path;
            });

    // icon
    node.append("path")
        .classed('icon', true)
        .attr('d', tpa.class_method()
            .default(function(d) {
                var ns = node_rect.get(this);
                var radius = Math.min(ns.height/5, ns.width/5, 10);
                var circle = "M "+ (-(ns.width/2+ns.height/3)) +" 0 " +
                    " m "+radius+", 0" +
                    " a "+radius+","+radius+" 0 1,1 "+(2*radius)+",0" +
                    " a "+radius+","+radius+" 0 1,1 "+(-2*radius)+",0";
                return circle;
            }));

    // name
    node.append("text")
        .classed("name", true)
        .attr("transform", function(d) {
            var ns = node_rect.get(this);
            return "translate("+(-ns.width/3)+", " + (-ns.height/2+20) + ")";
        })
        .text(d => d.data.name);

    // roles
    var role_idx = d3.local();

    var dgm_roles = node.append("g")
        .classed('roles', true)
        .attr('transform', function(d) {
            var x = -node_rect.get(this).width/5,
                y = -node_rect.get(this).height/2+25;

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
                var ns = node_rect.get(this);
                var idx = role_idx.get(this).idx;
                var top = 15+(idx-1)*15;
                role_idx.get(this).idx = idx+1;
                return "translate("+"4"+","+top+")";
            })
            .text(function(r) { return r.name; });
    });

    return node;
}

function draw_rolelink(selection, rolelink) {
    return selection.append("path")
        .classed("edge", true)
        .attr("d", function(d) {
            // draw line from server instance to client instance
            if ( !d.parent || !d.children) return "";
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
}


/*********
 * View and geometry helpers.
 */

function tree_layout(objects, parent_id, width, height) {
    var table = d3.stratify().id(d=> d.url).parentId(d => parent_id[d.url])
                (objects);
    var root = d3.hierarchy(table);
    var tree = d3.tree()
                .size([height, width])
                .nodeSize([height/10, MIN_NODE_WIDTH*1.5]);

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

    console.log("LAYOUT -----------");
    console.log("objects:", objects);
    console.log("stratified:", table);
    console.log("root:", root);

    return {tree: tree, root: root};
}


/**
 * Returns the minimum and maximum Y values for the descendants of this
 * diagram element.
 */
function node_yspan(d) {
    return {
        min_y: d3.min(d.descendants().map(c => c.y)),
        max_y: d3.max(d.descendants().map(c => c.y+height))
    };
}


function make_rect(w, h) {
    return {
        width: w,
        height: h,
        top_left:     { x: -w/2, y: -h/2 },
        top_right:    { x: +w/2, y: -h/2 },
        bottom_right: { x: +w/2, y: +h/2 },
        bottom_left:  { x: -w/2, y: +h/2 }
    };
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
        .attr('transform', `translate(0, ${height/2})`);

    return {svg: svg, diagram: diagram};
}


function draw_background_grid(selection, cy, width, height) {
    var yScale = scaleLinear()
        .domain([-height, height])
        .range([-height*2, height*2]);

    var grid = selection.append('g')
        .classed('background-grid', true)
        .selectAll("line.horizontal")
        .data(yScale.ticks(50)).enter()
        .append("line")
            .classed('horizontal', true)
            .attr("x1", -width*2)
            .attr("x2", width*2)
            .attr("y1", yScale)
            .attr("y2", yScale);

    var xAxis = d3.axisLeft(yScale);

    grid.call(xAxis);

    var xScale = scaleLinear()
        .domain([-width, width])
        .range([-width*2, width*2]);

    var gridy = selection.append('g')
        .classed('background-grid', true)
        .selectAll("line.vertical")
        .data(xScale.ticks(50)).enter()
        .append("line")
            .classed('horizontal', true)
            .attr("y1", -height*2)
            .attr("y2", height*2)
            .attr("x1", xScale)
            .attr("x2", xScale);

    var yAxis = d3.axisTop(yScale);

    gridy.call(yAxis);

}


exports.show_clusters = show_clusters;
