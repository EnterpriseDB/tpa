
<template>
<cluster-diagram ref="diagram" :url="url" @selected="set_panel_detail" @cluster="set_cluster">
</cluster-diagram>
</template>

<script>

import * as d3 from "d3";
import Vue from "vue";
import ClusterDiagram from "./ClusterDiagram.vue";
import DetailPanel from "./DetailPanel.vue";
import * as api from "../js/tpa-api";

export default Vue.extend({
    name: "cluster-editor",
    data: () => ({
        url: api.window_model().api_url,
        cluster: null
    }),
    created() {
        // spawn detail panel outside the main_content container.
        d3.select("body")
            .append("div")
                .attr("id", "detail-panel")
                .attr("v-on:object_changed", "refresh_object");
        this.detail_panel = new DetailPanel({
            el: "#detail-panel",
        });
    },
    mounted() {
        this.detail_panel.objects = [this.cluster];
    },
    components: {
        ClusterDiagram,
        DetailPanel,
    },
    methods: {
        set_cluster(c) {
            this.cluster = c;
            this.$forceUpdate();
        },
        set_panel_detail(obj) {
            this.detail_panel.objects = [this.cluster, obj];
        },
        refresh_object(c) {
            console.log("refresh!");
            this.$refs.diagram.reload_cluster();
        }
    }
});

</script>

<style scoped>
</style>
