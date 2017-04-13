import * as d3 from "d3";
import {scaleLinear} from "d3-scale";

const GRID_SPACING = 50;

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

        var svg = viewport.append('svg')
            .classed("diagram-viewport", true)
            .attr('width', width)
            .attr('height', height);

        var diagram = diagram_contents.append("g")
            .classed("diagram", true)
            .attr('transform', `translate(0, ${height/2})`);

        draw_background_grid(diagram, width, height);

        return diagram;
    }

    draw_background_grid(diagram, width, height) {
        var yScale = scaleLinear()
            .domain([-height, height])
            .range([-height*2, height*2]);

        var grid = diagram.append('g')
            .classed('background-grid', true)
            .selectAll("line.horizontal")
            .data(yScale.ticks(GRID_SPACING)).enter()
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

        var gridy = diagram.append('g')
            .classed('background-grid', true)
            .selectAll("line.vertical")
            .data(xScale.ticks(GRID_SPACING)).enter()
            .append("line")
                .classed('horizontal', true)
                .attr("y1", -height*2)
                .attr("y2", height*2)
                .attr("x1", xScale)
                .attr("x2", xScale);

        var yAxis = d3.axisTop(yScale);

        gridy.call(yAxis);

    }

    draw() {
        // Layout your graph inside the viewport and populate the items map.
    }

    setup_zoom(viewport) {
        let svg = this.viewport.selectAll('svg');
        var zoom = d3.zoom()
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

    var svg = viewport.append('svg')
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

    draw_background_grid(diagram, width, height);

    return diagram;
}


export function draw_background_grid(diagram, width, height) {
    var yScale = scaleLinear()
        .domain([-height, height])
        .range([-height*2, height*2]);

    var grid = diagram.append('g')
        .classed('background-grid', true)
        .selectAll("line.horizontal")
        .data(yScale.ticks(GRID_SPACING)).enter()
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

    var gridy = diagram.append('g')
        .classed('background-grid', true)
        .selectAll("line.vertical")
        .data(xScale.ticks(GRID_SPACING)).enter()
        .append("line")
            .classed('horizontal', true)
            .attr("y1", -height*2)
            .attr("y2", height*2)
            .attr("x1", xScale)
            .attr("x2", xScale);

    var yAxis = d3.axisTop(yScale);

    gridy.call(yAxis);

}

/**
 * Rotate tree 90 degrees, converting from top-down to left-to-right.
 */
export function tree_rotate(root) {
    var diagram_left = root.y;

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
function node_yspan(d) {
    return {
        min_y: d3.min(d.descendants().map(c => c.y)),
        max_y: d3.max(d.descendants().map(c => c.y+height))
    };
}
