
<template>
<div id="detail-panel" :master="master">
    <div class="navbar-fixed-bottom panel panel-default cluster_detail_panel">
        <ul class="nav nav-tabs" id="detail-panel-tabs" role="tablist">
            <li role="presentation">
                <a href="#cluster-detail" id="cluster-detail-tab" role="tab" data-toggle="tab" aria-controls="Instance" aria-expanded="true">Cluster</a>

            </li>
            <li role="presentation" class="active">
                <a href="#instance-detail" id="instance-detail-tab" role="tab" data-toggle="tab" aria-controls="Instance" aria-expanded="true">Instance</a>
            </li>
        </ul>
        <div class="tab-content" id="myTabContent">
            <div class="tab-pane fade in" role="tabpanel" id="cluster-detail" aria-labelledby="cluster-detail-tab">
                <div class="container-fluid">
                    <div class="row selected_cluster_detail"></div>
                </div>
            </div>

            <div class="tab-pane fade in active" role="tabpanel" id="instance-detail" aria-labelledby="instance-detail-tab">
                <div class="container-fluid">
                    <div class="row selected_instance_detail"></div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

import * as d3 from "d3";
import Vue from "vue";

export default Vue.extend({
    name: "detail-panel",
    props: ["master", "detail"],
    data: () => ({}),
    mounted() {},
    updated() {},
    methods: {
    }
});

</script>

<style scoped>
</style>
