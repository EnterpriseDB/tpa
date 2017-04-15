<template>
    <div id="cluster-carousel" class="carousel slide" data-ride="carousel">

        <div class="carousel-inner" role="listbox">
            <div v-for="cluster in clusters" :class="'item '+active(cluster)">
                <div class="carousel_cluster_diagram cluster_diagram" :href="cluster.url">
                    <p>Loading...</p>
                </div>
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
import {show_cluster_diagram} from "../js/cluster-diagram.js";

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
    mounted() {
        let self = this;
        $("#cluster-carousel").on("slid.bs.carousel", () => {
            let viewing = self.viewing_cluster;
            if(self.current_cluster != viewing) {
                self.current_cluster = viewing;
            }
        });
    },
    updated() {
        let containers = d3.select(this.$el)
            .selectAll("div.carousel_cluster_diagram");

        containers.each(function() {
            let container = d3.select(this);
            container.selectAll("p").remove();
            show_cluster_diagram(container, container.attr('href'));
        });
    },
    methods: {
        add_cluster(cluster) {
            if (this.clusters.indexOf(cluster) >= 0) { return; }

            this.clusters.push(cluster);
            if(!this.current_cluster) {
                this.current_cluster = cluster;
            }
        },
        active(cluster) {
            return (cluster == this.current_cluster) ? "active": "";
        }
    }
});

</script>

<style scoped>
</style>
