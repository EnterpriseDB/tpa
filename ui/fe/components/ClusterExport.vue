<template>
<!-- Cluster upload -->
<div id="cluster_export_dialog" class="modal fade">
    <div class="modal-dialog">
        <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h4 class="modal-title">Export a cluster design</h4>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <p>{{ user_message }}</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-failure">Cancel</button>
                    <a :href="config_yml" class="btn btn-success">Download</a>
                </div>
            </form>
        </div>
    </div>
</div>
</template>

<script>

import * as d3 from "d3";
import $ from "jquery";
import * as api from "../js/tpa-api";

module.exports = {
    el: "#cluster-export",
    data: () => ({
        user_message: "Downloading cluster in export format, please wait.",
        config_yml: ""
    }),

    methods: {
        show_modal() {
            let self = this;
            console.log("this:", this);

            api.auth.json_request(api.window_model().api_url+"export")
                .get((error, cluster) => {
                    if(error) {
                        alert("Export error.");
                        return;
                    }

                    self.config_yml = cluster.config_yml;
                });

            $("#cluster_export_dialog").modal("show");
        }
    }
}
</script>

<style scoped>
</style>
