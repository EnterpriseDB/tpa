<template>
<div id="cluster-carousel" class="carousel slide" data-ride="carousel">
  <!-- Indicators -->
  <ol class="carousel-indicators">
      <template v-for="cluster in clusters">
      <li data-target="#cluster-carousel" data-slide-to="0" :class="active(cluster)">
      </li>
      </template>
  </ol>

  <!-- Wrapper for slides -->
  <div class="carousel-inner" role="listbox">
      <div v-for="cluster in clusters" :class="'item '+active(cluster)">
          <div :class="'carousel_cluster_diagram cluster_diagram diagram_'+cluster.uuid">
          </div>
          {{ diagram(cluster) }}
          <div class="carousel-caption">
              <h3>{{ cluster.name }}</h3>
          </div>
      </div>
  </div>

  <!-- Left and right controls -->
  <a class="left carousel-control" href="#cluster-carousel" role="button" data-slide="prev">
    <span class="glyphicon glyphicon-chevron-left" aria-hidden="true"></span>
    <span class="sr-only">Previous</span>
  </a>
  <a class="right carousel-control" href="#cluster-carousel" role="button" data-slide="next">
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
    mounted: function() {
        let self = this;
        $("#cluster-carousel").on("slid.bs.carousel", () => {
            let viewing = self.viewing_cluster;
            if(self.current_cluster != viewing) {
                self.current_cluster = viewing;
            }
        });
    },
    methods: {
        add_cluster(cluster) {
            this.clusters.push(cluster);
            if(!this.current_cluster) {
                this.current_cluster = cluster;
            }
        },
        active(cluster) {
            return (cluster == this.current_cluster) ? "active": "";
        },
        diagram(cluster) {
            let el = d3.select(this.$el);
            window.setTimeout(() => {
                let container = el.selectAll("div.diagram_"+cluster.uuid);
                console.log("rendering container on:", cluster, container);
                let url = cluster.url;
                if (url.startsWith("http:")) {
                    url = "https"+url.slice(4);
                }
                show_cluster_diagram(container, url);
            }, 5);

            return '';
        }
    }
});

</script>

<style scoped>
</style>
