
<template>
<cluster-diagram :url="url"></cluster-diagram>
</template>

<script>

import Vue from "vue";
import ClusterDiagram from "./ClusterDiagram.vue";
import * as api from "../js/tpa-api";

export default Vue.extend({
    name: "cluster-editor",
    data: () => ({
        url: api.window_model().api_url
    }),
    components: {
        ClusterDiagram
    }
});

</script>

<style scoped>
</style>
