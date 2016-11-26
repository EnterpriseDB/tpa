
//var test_data_url = "/api/v1/tpa/provider/c2b1c094-03fd-5d95-b7f3-656fc9f62d72/"
var test_data_url = "/test-cluster.json"
var diameter = 960;
var width = 300;
var height = 300;

var root = null;

d3.json(test_data_url,
    function(model_object, error) {
        if (error) throw error;
        draw_cluster(model_object)
});


var draw_cluster = function (cluster) {
    console.log(cluster);

    root = d3.hierarchy([cluster], function(d) {
        console.log("hier for", d)

        if (d.instance_set && d.instance_set.length > 0) {
            return d.instance_set;
        }

        if (d.role_set && d.role_set.length > 0) {
            return d.role_set;
        }

        if (d.length && d.length > 0) {
            return d;
        }

        return null;
    });

    tree(root);

    var svg = d3.select(".treeview")
    .attr('class', 'treeview')
    .attr('width', diameter)
    .attr('height', diameter)

    g = svg.append("g").attr("transform", "translate(60,0)");

    //var stratify = d3.stratify()
    //    .parentId(function(d) { return d.id.substring(0, d.id.lastIndexOf(".")); });

    var link = g.selectAll(".link")
        .data(root.descendants().slice(1))
        .enter().append("path")
        .attr("class", "link")
        .attr("d", function(d) {
            return "M" + d.y + "," + d.x
                + "C" + (d.parent.y + 100) + "," + d.x
                + " " + (d.parent.y + 100) + "," + d.parent.x
                + " " + d.parent.y + "," + d.parent.x;
        });

    var node = g.selectAll(".node")
        .data(root.descendants().slice(1))
        .enter().append("g")
        .attr("class", function(d) { return "node" + (d.children ? " node--internal" : " node--leaf"); })
        .attr("transform", function(d) {
            return "translate(" + d.y + "," + d.x + ")";
        })

    node.append("circle")
        .attr("r", function(d) {
            return 5.0;
        });

    node.append("text")
        .attr("dy", 3)
        .attr("x", function(d) { return d.children ? -8 : 8; })
        .style("text-anchor", function(d) { return d.children ? "end" : "start"; })
        .text(function(d) {
            console.log(d.data);
            return d.data.name;
        });
};
