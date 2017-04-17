
<template>
<div id="cluster-diagram" class="svg-container cluster_diagram" :url="url">
<!--
<svg class=svg-content-responsive diagram-viewport" preserveAspectRatio="xMinYMin meet" viewBox="0 0 600 400">
    <g>
        <g class="diagram"></g>
    </g>
</div>
-->
</template>

<script>

import * as d3 from "d3";
import Vue from "vue";
import * as tpa from "../js/tpa-api";

import {ClusterDiagram} from "../js/cluster-diagram";

export default Vue.extend({
    name: "cluster-diagram",
    props: ["url"],
    data: () => ({cluster: null}),
    updated() { this.refresh_diagram(); },
    created() {
        let self = this;
        tpa.get_obj_by_url(self.url, c => {
            self.cluster = c;
            self.diagram = new ClusterDiagram(c, d3.select(self.$el));
            self.diagram.on_select(obj => self.$emit("selected", obj));
        });
    },
    methods: {
        refresh_diagram() {
            if(!this.cluster) return;
            this.diagram.draw();
        }
    },
});

</script>

<style scoped>
</style>
