
<template>
<div id="cluster-diagram" class="cluster_diagram" :url="url"></div>
</template>

<script>

import * as d3 from "d3";
import Vue from "vue";

import {show_cluster_diagram} from "../js/cluster-diagram";

export default Vue.extend({
    name: "cluster-diagram",
    props: ["url"],
    data: () => ({}),
    mounted() { this.refresh_diagram(); },
    updated() { this.refresh_diagram(); },
    methods: {
        refresh_diagram() {
            show_cluster_diagram(d3.select(this.$el), this.url);
        }
    }
});

</script>

<style scoped>
</style>
