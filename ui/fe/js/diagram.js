
import * as d3 from "d3";
import {scaleLinear} from "d3-scale";
import {multimethod} from "./multimethod";
import {model_class} from "./tpa-api";

const GRID_SPACING = 50;

// Reflection helpers.

export function data_class(d) {
    return model_class(d.data);
}

export function data_method() {
    return multimethod().dispatch(data_class);
}

export function is_instance(filter) {
    return multimethod().dispatch(data_class)
        .when(filter, true).default(false);
}


export const draw_item = multimethod(o => data_class(o.data()[0]));


// Should eventually be a vue

class Diagram {
    constructor(viewport, model) {
        this.viewport = viewport;
        this.model = model;
        this.items = {};

        this.build_diagram();
    }

    update_geometry() {
        let bbox = viewport.node().getBoundingClientRect();
        this.width = bbox.width;
        this.height = bbox.height;
    }

    setup_viewport() {
        const width = this.width, height = this.height;

        viewport.selectAll("svg").remove();

        let svg = viewport.append('svg')
            .classed("diagram-viewport", true)
            .attr('width', width)
            .attr('height', height);

        let diagram = diagram_contents.append("g")
            .classed("diagram", true)
            .attr('transform', `translate(0, ${height/2})`);

        draw_background_grid(diagram, width, height);

        return diagram;
    }

    draw_background_grid(diagram, width, height) {
        let yScale = scaleLinear()
            .domain([-height, height])
            .range([-height*2, height*2]);

        let grid = diagram.append('g')
            .classed('background-grid', true)
            .selectAll("line.horizontal")
            .data(yScale.ticks(GRID_SPACING)).enter()
            .append("line")
                .classed('horizontal', true)
                .attr("x1", -width*2)
                .attr("x2", width*2)
                .attr("y1", yScale)
                .attr("y2", yScale);

        let xAxis = d3.axisLeft(yScale);

        grid.call(xAxis);

        let xScale = scaleLinear()
            .domain([-width, width])
            .range([-width*2, width*2]);

        let gridy = diagram.append('g')
            .classed('background-grid', true)
            .selectAll("line.vertical")
            .data(xScale.ticks(GRID_SPACING)).enter()
            .append("line")
                .classed('horizontal', true)
                .attr("y1", -height*2)
                .attr("y2", height*2)
                .attr("x1", xScale)
                .attr("x2", xScale);

        let yAxis = d3.axisTop(yScale);

        gridy.call(yAxis);

    }

    draw() {
        // Layout your graph inside the viewport and populate the items map.
    }

    setup_zoom(viewport) {
        let svg = this.viewport.selectAll('svg');
        let zoom = d3.zoom()
            //.scaleExtent([0.5, 40])
            .translateExtent([[-this.width/2, -this.height/2],
                            [this.width*2, this.height*2]])
            .on("zoom", () =>
                svg.selectAll('g.diagram')
                    .attr("transform", d3.event.transform));

        svg.call(zoom);
    }
}

export function setup_viewport(viewport, width, height) {
    viewport.selectAll("svg").remove();

    let svg = viewport.append('svg')
        .classed("diagram-viewport svg-content-responsive", true);

    let viewport_contents = svg.append('g');

    // Zoom

    let zoom = d3.zoom()
        .translateExtent([[-width/2, -height/2], [width*2, height*2]])
        .on("zoom", () => viewport_contents.attr("transform", d3.event.transform));

    svg.call(zoom);

    let diagram = viewport_contents.append("g")
        .classed("diagram", true)
        .attr('transform', `translate(0, ${height/2})`);

    draw_background_grid(diagram, width, height);

    return {
        diagram: diagram,
        width: width,
        height: height
    };
}


export function draw_background_grid(diagram, width, height) {
    let yScale = scaleLinear()
        .domain([-height, height])
        .range([-height*2, height*2]);

    let grid = diagram.append('g')
        .classed('background-grid', true)
        .selectAll("line.horizontal")
        .data(yScale.ticks(GRID_SPACING)).enter()
        .append("line")
            .classed('horizontal', true)
            .attr("x1", -width*2)
            .attr("x2", width*2)
            .attr("y1", yScale)
            .attr("y2", yScale);

    let xAxis = d3.axisLeft(yScale);

    grid.call(xAxis);

    let xScale = scaleLinear()
        .domain([-width, width])
        .range([-width*2, width*2]);

    let gridy = diagram.append('g')
        .classed('background-grid', true)
        .selectAll("line.vertical")
        .data(xScale.ticks(GRID_SPACING)).enter()
        .append("line")
            .classed('vertical', true)
            .attr("y1", -height*2)
            .attr("y2", height*2)
            .attr("x1", xScale)
            .attr("x2", xScale);

    let yAxis = d3.axisTop(yScale);

    gridy.call(yAxis);

}


/**
 * Rotate tree 90 degrees, converting from top-down to left-to-right.
 */
export function tree_rotate(root) {
    let diagram_left = root.y;

    root.each(d => {
        let x = (d.y ? d.y : 0),
            y = (d.x ? d.x : 0);

        d.x = x - diagram_left;
        d.y = y;
    });
}


/**
 * Returns the minimum and maximum Y values for the descendants of this
 * diagram element.
 */
export function node_yspan(d) {
    let y_values = d.descendants().map(c => c.y);

    return {
        min_y: d3.min(y_values),
        max_y: d3.max(y_values)
    };
}
