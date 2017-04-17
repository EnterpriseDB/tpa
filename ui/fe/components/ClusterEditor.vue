
<template>
<cluster-diagram :url="url" @selected="set_panel_detail">
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
        url: api.window_model().api_url
    }),
    created() {
        // spawn detail panel outside the main_content container.
        d3.select("body").append("div").attr("id", "detail-panel");
        this.detail_panel = new DetailPanel({
            el: "#detail-panel",
            master: this.url,
            detail: this.url,
        });
    },
    mounted() {
        this.set_panel_detail(this.url);
    },
    components: {
        ClusterDiagram,
        DetailPanel,
    },
    methods: {
        set_panel_detail(obj) {
            this.detail_panel.detail = obj ? obj : this.url;
        }
    }
});

</script>

<style scoped>
</style>
