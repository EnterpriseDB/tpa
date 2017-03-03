
/**
 * Generate SVG diagrams from TPA clusters using d3 and the TPA API.
 */

import * as d3 from "d3";

import * as tpa from "./tpa-api";
import {Accumulator, sort_by_attr} from "./utils";
import {make_rect} from "./geometry";
import {setup_viewport, tree_rotate} from "./diagram";

const MIN_NODE_HEIGHT = 20;
const MIN_NODE_WIDTH = 100;
const MAX_CIRCLE_RADIUS = MIN_NODE_HEIGHT*0.66;

const LINK_CONNECTOR_HEIGHT = 5;
const LINK_CONNECTOR_LENGTH = MIN_NODE_WIDTH;

const DG_POSTGRES_ROLES = {primary: true, replica: true};


/**
 * Display all clusters belonging to the current tenant, one at a time.
 * Displays the first cluster immediately, returns a function to cycle to
 * the next when called.
*/
export function show_clusters(viewport) {
    var clusters = [];
    var current_cluster_idx = -1;

    tpa.get_all("cluster", null, c => {
        clusters = c;

        if (clusters.length > 0) {
            current_cluster_idx = 0;
            draw_cluster(clusters[current_cluster_idx], viewport);
        }
    });

    return function next_cluster() {
        if (clusters.length < 1) {
            return;
        }

        current_cluster_idx = current_cluster_idx+1;
        if (current_cluster_idx >= clusters.length) {
            current_cluster_idx = 0;
        }
        draw_cluster(clusters[current_cluster_idx], viewport);
    };
}


export function display_cluster_by_uuid(cluster_uuid, viewport) {
    tpa.get_cluster_by_uuid(cluster_uuid, c => draw_cluster(c, viewport));
}


class ClusterDiagram {
    constructor (cluster, viewport, objects, parent_id) {
        this.viewport = viewport;
        this.cluster = cluster;
        this.objects = objects;
        this.parent_id = parent_id;

        let bbox = viewport.node().getBoundingClientRect();

        this.width = bbox.width;
        this.height = bbox.height;
        this.diagram = setup_viewport(viewport, bbox.width, bbox.height);

        this.layout_graph();

        // map obj url -> diagram item
        this.dobj_for_model = {};

        this.root.eachAfter(d => {
            this.dobj_for_model[d.data.url] = d;
        });
    }

    layout_graph() {
        var table = d3.stratify()
            .id(d => d.url)
            .parentId(d => this.parent_id[d.url])
        (this.objects);

        this.root = d3.hierarchy(table);
        this.tree = d3.tree()
                    .size([this.height, this.width])
                    .nodeSize([this.height/15, MIN_NODE_WIDTH*1.5]);

        this.tree(this.root);
        tree_rotate(this.root);

        this.root.eachAfter(d => {
            // remove the double-reference introduced by stratify
            d.data = d.data.data;

            // set y position to same as first child.
            if (d.children && d.children.length > 0) {
                d.y = d.children[0].y;
            }
        });

        console.log("LAYOUT -----------");
        console.log("objects:", this.objects);
        console.log("stratified:", table);
        console.log("root:", this.root);
    }
}


// TPA Diagram

function draw_cluster(cluster, viewport) {
    console.log("draw_cluster:", cluster, tpa.cluster_type(cluster));

    let objects, parent_id;

    if (tpa.cluster_type(cluster) == 'xl') {
        [objects, parent_id] = build_xl_graph(cluster);
    }
    else {
        [objects, parent_id] = build_tpa_graph(cluster);
    }

    let cluster_diagram = new ClusterDiagram(cluster, viewport,
                                            objects, parent_id);

    for (let d of cluster_diagram.root.descendants()) {
        if (tpa.model_class(d.data) == 'rolelink') {
            let p = cluster_diagram.dobj_for_model[d.data.server_instance.url];

            if (!p.num_children) {
                p.num_children = 1;
                d.parent_idx = 0;
            }
            else {
                d.parent_idx = p.num_children++;
            }
        }
    }

    function draw_all_of_class(c, draw) {
        cluster_diagram.diagram
            .selectAll("."+c)
            .data(cluster_diagram.root.descendants().filter(tpa.is_instance(c)))
            .enter()
            .call(d => draw(d, cluster_diagram)
                .classed(c, true)
            );
    }

    draw_all_of_class('zone', draw_zone);
    draw_all_of_class('rolelink', draw_rolelink);
    draw_all_of_class('instance', draw_instance);

    d3.selectAll(".cluster_name").text(cluster.name);
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
                    switch (r.role_type) {
                        case 'datanode-replica':
                            r.client_links.forEach(function(ln) {
                                if (ln.name == 'datanode-replica') {
                                    objects.push(ln);
                                    parent_id[ln.url] = roles[ln.server_role].url;
                                    parent_id[i.url] = ln.url;
                                }
                            });
                            break;
                        case 'coordinator':
                            r.client_links.forEach(function(ln) {
                                if (ln.name == 'gtm') {
                                    objects.push(ln);
                                    parent_id[ln.url] = roles[ln.server_role].url;
                                    parent_id[i.url] = ln.url;
                                }
                            });
                            break;
                        case 'datanode':
                            r.client_links.forEach(function(ln) {
                                if (ln.name == 'coordinator' && !(i.url in parent_id)) {
                                    objects.push(r);
                                    parent_id[r.url] = coord_center.url;
                                    parent_id[i.url] = r.url;
                                }
                            });
                            break;
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
    var tree = new Tree();

    var accum = [];
    var objects = [cluster];
    var parent_id = {};
    var role_instance = {};
    var pg_instances = [];

    var zones = [], replica_zones = [];

    function add_instance_parent(instance, parent) {
        accum.push([instance, parent]);
    }

    // Sort zones by (has primary)/name
    for(let subnet of cluster.subnets) {
        if (tpa.subnet_has_primary(subnet)) {
            zones.push(subnet.zone);
        }
        else {
            replica_zones.push(subnet.zone);
        }
    }

    sort_by_attr(zones, 'name');
    sort_by_attr(replica_zones, 'name');
    zones = zones.concat(replica_zones);

    for (let zone of zones) {
        if (!(zone.url in parent_id)) {
            accum.push([zone, cluster]);
        }
    }

    // Grammar:
    // cluster -> region -> zone -> (subnet?) -> instance
    //   (-> rolelink -> instance)*

    for (let subnet of cluster.subnets) {
        for (let instance of subnet.instances) {
            let primary_role = tpa.instance_role(instance);
            if (primary_role && DG_POSTGRES_ROLES[primary_role.role_type]) {
                pg_instances.push(instance);
                for(let role of instance.roles) {
                    role_instance[role.url] = instance;
                }
            }
        }
    }

    sort_by_attr(pg_instances, 'name');

    let dummy_idx = 0;

    for (let client_instance of pg_instances) {
        for (let r of client_instance.roles) {
            if (!(r.role_type in DG_POSTGRES_ROLES)) continue;

            for (let client_link of r.client_links) {
                let server_instance = role_instance[client_link.server_role];
                if (client_instance == server_instance) return;

                // FIXME for drawing role!
                client_link.server_instance = role_instance[client_link.server_role];

                if (server_instance.zone != client_instance.zone) {
                    server_instance = {
                        url: `dummyparent:${dummy_idx++}`,
                        zone: client_instance.zone
                    };

                    add_instance_parent(server_instance, client_instance.zone);
                }

                add_instance_parent(client_instance, client_link);
                accum.push([client_link, server_instance]);
            }
        }
    }

    // if an instance has no parent yet, the zone is its parent.
    for(let i of pg_instances) {
        if (!(i.url in parent_id)) {
            add_instance_parent(i, i.zone);
        }
    }

    // create final parent lookup
    accum.forEach(function([o, p]) {
        if (!(o.url in parent_id)) {
            objects.push(o);
            parent_id[o.url] = p.url;
        }
    });

    return [objects, parent_id];
}


function draw_zone(selection, cluster_diagram) {
    //var zone_sep_y = d3.local();

    var zone_display = selection.append('g')
        .classed('zone--empty',  d => d.children)
        .attr("transform", d => `translate(${-d.parent.x}, ${d.y})`)
        .property('model-url', d => d.data.url ? d.data.url : null);

    zone_display.append("text")
        .text(d => d.data.name);

    zone_display.append('line')
        .attr('x1', 0)
        .attr('y1', function (d) {
            return -MIN_NODE_HEIGHT*2;
        })
        .attr('x2', cluster_diagram.width)
        .attr('y2', function (d) {
            return -MIN_NODE_HEIGHT*2;
        });

    return zone_display;
}

function instance_size(instance) {
    return {width: MIN_NODE_WIDTH,
            height: MIN_NODE_HEIGHT};
}


function instance_vcpus(instance) {
    let vcpus = parseInt(instance.instance_type.vcpus);

    return Math.max(Math.sqrt(vcpus ? vcpus : 1), 1);
}

function draw_instance(selection, cluster_diagram) {
    let node_rect = d3.local();
    let node_model = d3.local();
    let node_url = d3.local();

    let node = selection.append("g")
        .attr("class", d =>
            "instance node " + (d.children ? "node--internal" : "node--leaf"))
        .attr("transform", d => `translate(${d.x}, ${d.y})`)
        .property('model-url', d => d.data.url ? d.data.url : null)
        .each(function(d) {
            let size = instance_size(d.data);
            node_model.set(this, d.data);
            node_url.set(this, d.data.url);
            node_rect.set(this, make_rect(size.width, size.height));
        });

    // icon
    node.append("path")
        .classed('icon', true)
        .attr('d', tpa.class_method()
            .default(function(d) {
                let ns = node_rect.get(this);

                let radius = MAX_CIRCLE_RADIUS*instance_vcpus(d.data);
                let diameter = 2*radius;

                return "M 0 0 " +
                    ` m -${radius}, 0` +
                    ` a ${radius},${radius} 0 1,1 ${diameter},0` +
                    ` a ${radius},${radius} 0 1,1 -${diameter},0`;
            }));

    // name
    node.append("text")
        .classed("name", true)
        .attr("transform", function(d) {
            let ns = node_rect.get(this);
            let offset = MAX_CIRCLE_RADIUS*(instance_vcpus(d.data)+0.25);
            return `translate(${offset},-${offset})`;
        })
        .text(d => d.data.name);

    return node;
}

function draw_rolelink(selection, cluster_diagram) {
    return selection.append("path")
        .classed("edge", true)
        .attr("d", function(d) {
            // draw line from server instance to client instance
            if ( !d.parent || !d.children) {
                return "";
            }
            let p = cluster_diagram.dobj_for_model[d.data.server_instance.url],
                c = d.children[0];
            let path = d3.path();

            let p_y = p.y + LINK_CONNECTOR_HEIGHT * d.parent_idx;
            let c_y = c.y;

            path.moveTo(p.x, p.y);
            path.lineTo(p.x, p_y);
            path.lineTo(p.x+LINK_CONNECTOR_LENGTH, p_y);
            path.lineTo(c.x-LINK_CONNECTOR_LENGTH, c_y);
            path.lineTo(c.x, c_y);
            return path;
        });
}


/*********
 * View and geometry helpers.
 */

class Tree {
    constructor() {
        this.objects = [];
        this.queue = [];  // [object, parent]
        this.parent = {}; // url -> parent object
    }

    add(o, parent) {
        this.queue.push([o, parent]);
    }
}

