<template>
<div id="cluster-carousel" class="carousel slide" data-ride="carousel">

    <div class="carousel-inner" role="listbox">
        <div v-for="cluster in clusters" :class="'item '+active(cluster)">
            <cluster-diagram :url="cluster.url" class="carousel_cluster_diagram">
            </cluster-diagram>
            <div class="carousel-caption">
                <h3>{{ cluster.name }}</h3>
                <p v-if="cluster.description">{{ cluster.description }}</p>
            </div>
        </div>
    </div>

    <ol class="carousel-indicators">
        <template v-for="(cluster, index) in clusters">
            <li data-target="#cluster-carousel" :data-slide-to="index" :class="active(cluster)">
            </li>
        </template>
    </ol>

    <a class="left carousel-control col-sm-2" href="#cluster-carousel" role="button" data-slide="prev">
        <span class="glyphicon glyphicon-chevron-left" aria-hidden="true"></span>
        <span class="sr-only">Previous</span>
    </a>
    <a class="right carousel-control col-sm-2" href="#cluster-carousel" role="button" data-slide="next">
        <span class="glyphicon glyphicon-chevron-right" aria-hidden="true"></span>
        <span class="sr-only">Next</span>
    </a>
</div>
</template>

<script>

import * as d3 from "d3";
import $ from "jquery";
import Vue from "vue";

import * as api from "../js/tpa-api";

import ClusterDiagram from "./ClusterDiagram.vue";

export default Vue.extend({
    name: "cluster-carousel",
    data: () => ({
        clusters: [],
        current_cluster: null
    }),
    computed: {
        viewing_cluster() {
            let idx = $("#cluster_carousel").find("div.active").index();
            if (idx < 0) { return null; }
            return this.clusters[idx];
        }
    },
    created() {

    },
    mounted() {
        let self = this;
        $("#cluster-carousel").on("slid.bs.carousel", () => {
            let viewing = self.viewing_cluster;
            if(self.current_cluster != viewing) {
                self.current_cluster = viewing;
            }
        });
        this.load_templates();
    },
    methods: {
        load_templates() {
            api.object_list("template", "",
                (error, clusters) => {
                    if (error) {
                        //TODO Display load error state.
                        return;
                    }
                    this.clusters = clusters;
                    if( clusters &&
                        (!this.current_cluster ||
                        (this.clusters.indexOf(this.current_cluster) < 0))) {

                        this.current_cluster = clusters[0];
                    }
                });
        },
        active(cluster) {
            return (cluster == this.current_cluster) ? "active": "";
        }
    },
    components: {
        ClusterDiagram
    }
});

</script>

<style scoped>
</style>
