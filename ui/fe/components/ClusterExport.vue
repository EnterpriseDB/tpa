<template>
<!-- Cluster upload -->
<div id="cluster-export" class="modal fade">
    <div class="modal-dialog">
        <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h4 class="modal-title">Export this cluster to config.yml</h4>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="message">{{ user_message }}</div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                    <a :href="download_data" download="config.yml" class="btn btn-success download" :style="dlb_style">Download</a>

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
import Vue from "vue";

const B64_PF = "data:text/octet-stream;base64,";

export default Vue.extend({
    name: "cluster-export",
    data: () => ({
        user_message: "Downloading cluster in export format, please wait.",
        download_data: "",
        dlb_style: "visiblity: hidden"
    }),
    mounted: function() {
        let self = this;
        d3.selectAll("button.cluster_export").on("click", () => {
            d3.event.preventDefault();
            self.show_modal();
        });

        d3.selectAll("a.download").on("click", () => {
            window.setTimeout(() => {
                self.reset_dialog();
            }, 500);
        });

    },

    methods: {
        show_modal() {
            api.auth.json_request(api.window_model().api_url+"export")
                .get((error, export_data) => {
                    if(error) {
                        alert("Export error.");
                        return;
                    }

                    this.download_data = B64_PF + btoa(export_data.config_yml);

                    this.dlb_style = "visibility: visible";
                    this.user_message="Export ready. Click the button to download.";
                });

            $("#cluster-export").modal("show");
        },
        reset_dialog() {
            $("#cluster-export").modal("hide");
            this.dlb_style = "visibility: hidden";
            this.user_message="";
        }
    }
});
</script>

<style scoped>
</style>
