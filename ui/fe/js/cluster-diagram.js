/**
 * Generate SVG diagrams from TPA clusters using d3 and the TPA API.
 */

import * as d3 from "d3";

import * as tpa from "./tpa-api";
import {Accumulator, sort_by_attr} from "./utils";
import {make_rect} from "./geometry";
import {setup_viewport, tree_rotate, data_method, data_class, is_instance}
    from "./diagram";
import {multimethod} from "./multimethod";


const DG_SIZE = {
    S_HEIGHT: 0.5,
    S_WIDTH: 0.5
};

const NODE_SIZE = {
    M_HEIGHT: 20,
    M_WIDTH: 100
};

const MAX_CIRCLE_RADIUS = NODE_SIZE.M_HEIGHT*0.66;

const EDGE_END_HEIGHT = 5;
const EDGE_END_LENGTH = NODE_SIZE.M_WIDTH;

// Fudge factors to include instance label in selection box.
const ISF = {
    O_Y: 1.6/2,
    O_X: 0.5,
    W: 1.5,
    H: 1.25
};


const DG_POSTGRES_ROLES = {
    primary: true,
    replica: true,
    barman: true
};


let draw_object = multimethod(o => data_class(o.data()[0]));


export function show_cluster_diagram(selection, cluster_url) {
    tpa.get_obj_by_url(cluster_url, c => draw_cluster(c, selection));
}


function clear_detail_panel() {
    d3.selectAll(".selected_instance_detail")
        .selectAll("*")
        .remove();
}


function display_selected_instance_detail(instance) {
    function add_detail(selection, attr_name, attr_value) {
        if ( !attr_value ) { return; }

        let g = selection.append("div")
                .classed(`${attr_name} row`, true);

        g.append("div")
            .classed("attr_name col-xs-3", true)
            .html(attr_name+" ");
        g.append("div")
            .classed("attr_value col-xs-9", true)
            .html(attr_value);

        return g;
    }

    clear_detail_panel();

    let row = d3.selectAll(".selected_instance_detail");

    function detail_column() {
        return row.append("div").attr("class", "col-xs-4");
    }

    let mem = instance.instance_type.memory ?
        `, ${instance.instance_type.memory}g memory` : "";

    detail_column()
        .call(add_detail, "Name", instance.name)
        .call(add_detail, 'Type', `${instance.instance_type.name}\
            (${instance.instance_type.vcpus} vcpus${mem})`)
        .call(add_detail, 'Description', instance.description);

    detail_column()
        .call(add_detail, 'Region', instance.subnet.zone.region.name)
        .call(add_detail, 'Zone', instance.subnet.zone.name)
        .call(add_detail, 'Subnet', instance.subnet.name)
        .call(add_detail, 'VPC', instance.subnet.vpc.name)
        .call(add_detail, 'Ext. IP', instance.assign_eip)
        .call(add_detail, 'Tags', instance.user_tags ?
            (Object.keys(instance.user_tags).map(
                k => k + ": " + instance.user_tags[k]).join(", "))
            : "");

    detail_column()
        .call(add_detail, 'Roles',
            instance.roles.map(r => r.role_type).join(", "))
        .call(add_detail, "Volumes",
            instance.volumes.map(vol => {
                let p = vol.delete_on_termination ?  "" : " persistent";
                return `${vol.name} (${vol.volume_size}g${p} ${vol.volume_type})`;
            }).join(", "));
}


function draw_cluster(cluster, viewport) {
    let cluster_diagram = new ClusterDiagram(cluster, viewport);

    cluster_diagram.draw_items_of_class('zone');
    cluster_diagram.draw_items_of_class('rolelink');
    cluster_diagram.draw_items_of_class('instance');

    d3.selectAll(".cluster_name").text(cluster.name);
}


class ClusterDiagram {
    constructor (cluster, viewport) {
        this.viewport = viewport;
        this.cluster = cluster;
        this.dobj_for_model = {};

        let bbox = viewport.node().getBoundingClientRect();
        this.width = bbox.width;
        this.height = bbox.height;

        this.dispatch = d3.dispatch("selected", "deselected");
        this.current_selection = null;
        this.setup_selection();

        this.diagram = setup_viewport(this.viewport, this.width, this.height);
        this.draw();
    }

    on(event, callback) {
        return this.dispatch.on(event, callback);
    }

    setup_selection() {
        this.on("selected", function() {
            let node = this;
            let bbox = node.getBBox();
            d3.select(node)
                .classed("selected", true)
                .append("rect")
                    .classed("selection", true)
                    .attr("transform",
                        `translate(${-bbox.width*ISF.O_X}, ${5-bbox.height*ISF.O_Y})`)
                    .attr("width", bbox.width*ISF.W)
                    .attr("height", bbox.height*ISF.H);
        });

        this.on("deselected", function() {
            d3.select(this)
                .classed("selected", false)
                .selectAll(".selection")
                .remove();
        });

        this.on("deselected.detail", function() {
            clear_detail_panel();
        });

        this.on("selected.detail", function() {
            display_selected_instance_detail(this.__data__.data);
        });

        clear_detail_panel();
    }

    get selection() {
        return this.current_selection;
    }

    set selection(d) {
        if(this.current_selection) {
            this.dispatch.call("deselected", this.current_selection);
            this.current_selection = null;
        }

        this.current_selection = d;
        this.dispatch.call("selected", this.current_selection);
    }


    draw() {
        let build_graph = build_tpa_graph;

        switch(tpa.cluster_type(this.cluster)) {
            case 'xl':
                build_graph = build_xl_graph;
                break;
        }

        [this.objects, this.parent_id] = build_graph(this.cluster);

        this.layout_graph();

        this.root.eachAfter(d => {
            this.dobj_for_model[d.data.url] = d;
        });

        // Assign numerical order to each rolelink item on in-edges to its
        // parent.

        for (let d of this.root.descendants()) {
            if (tpa.model_class(d.data) != 'rolelink') continue;

            let p = this.dobj_for_model[d.data.server_instance.url];
            if (!p.num_children) { p.num_children = 0; }
            d.parent_idx = p.num_children++;
        }
    }

    layout_graph() {
        var table = d3.stratify()
            .id(d => d.url)
            .parentId(d => this.parent_id[d.url])
        (this.objects);

        this.root = d3.hierarchy(table);
        this.tree = d3.tree()
                    .size([this.height*DG_SIZE.S_HEIGHT,
                            this.width*DG_SIZE.S_WIDTH])
                    .nodeSize([this.height/15, NODE_SIZE.M_WIDTH*1.5]);

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

        console.log("LAYOUT: o:", this.objects, "t:", table, "r:", this.root);
    }

    draw_items_of_class(klazz) {
        let self = this;

        this.diagram
            .selectAll("."+klazz)
            .data(this.root.descendants().filter(is_instance(klazz)))
            .enter()
            .each(function(c) {
                d3.select(this).call(os => {
                    let oe = draw_object(os, self);
                    if (!oe || oe.empty()) { return; }
                    oe.classed(klazz, true);
                });
            });
    }
}


// TPA Diagram

function build_xl_graph(cluster) {
    // TODO: XL graph builder is outdated.
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
    let accum = [];
    let objects = [cluster];
    let parent_id = {};
    let role_instance = {};
    let pg_instances = [];

    let zones = [], replica_zones = [];

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

    // filter relevant instances
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

    // create instance graph
    let dummy_idx = 0;

    for (let client_instance of pg_instances) {
        for (let r of client_instance.roles) {
            if (!(r.role_type in DG_POSTGRES_ROLES)) continue;

            for (let client_link of r.client_links) {
                let server_instance = role_instance[client_link.server_role];
                if (client_instance == server_instance) continue;

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


/**
 * Drawing methods for diagram items by data class.
 */

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
        .attr('y1', (d) => -NODE_SIZE.M_HEIGHT*2)
        .attr('x2', cluster_diagram.width)
        .attr('y2', (d) => -NODE_SIZE.M_HEIGHT*2)

    return zone_display;
}
draw_object.when('zone', draw_zone);

function draw_instance(selection, cluster_diagram) {
    let node_rect = d3.local();
    let node_model = d3.local();
    let node_url = d3.local();

    let node = selection.append("g")
        .attr("class", d =>
            "instance node " + (d.children ? "node--internal" : "node--leaf"))
        .attr("transform", d => `translate(${d.x}, ${d.y})`)
        .property('model-url', d => d.data.url ? d.data.url : null)
        .on("click.selection", function(d) {
            cluster_diagram.selection = this;
        })
        .each(function(d) {
            let size = instance_size(d.data);
            node_model.set(this, d.data);
            node_url.set(this, d.data.url);
            node_rect.set(this, make_rect(size.width, size.height));
        });

    // icon
    node.append("path")
        .classed('icon', true)
        .attr('d', data_method()
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
draw_object.when('instance', draw_instance);

function draw_rolelink(selection, cluster_diagram) {
    return selection.append("path")
        .classed("edge", true)
        .attr("d", function(d) {
            // draw line from server instance to client instance
            if ( !d.parent || !d.children) { return ""; }

            let p = cluster_diagram.dobj_for_model[d.data.server_instance.url],
                c = d.children[0],
                p_y = p.y + EDGE_END_HEIGHT * d.parent_idx,
                c_y = c.y,
                path = d3.path();

            path.moveTo(p.x, p.y);
            path.lineTo(p.x, p_y);
            path.lineTo(p.x+EDGE_END_LENGTH, p_y);
            path.lineTo(c.x-EDGE_END_LENGTH, c_y);
            path.lineTo(c.x, c_y);

            return path;
        });
}
draw_object.when('rolelink', draw_rolelink);


/*********
 * View and geometry helpers.
 */

function instance_size(instance) {
    return {width: NODE_SIZE.M_WIDTH,
            height: NODE_SIZE.M_HEIGHT};
}

function instance_vcpus(instance) {
    let vcpus = parseInt(instance.instance_type.vcpus);

    return Math.max(Math.sqrt(vcpus ? vcpus : 1), 1);
}
