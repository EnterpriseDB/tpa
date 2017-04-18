
<template>
<div id="detail-panel">
    <div class="navbar-fixed-bottom panel panel-default cluster_detail_panel">
        <ul class="nav nav-tabs" id="detail-panel-tabs" role="tablist">
            <li v-for="model in models" role="presentation" :class="pane_active(model)">
                <a :href="'#'+model_id(model)" :id="model_id(model)+'-tab'" role="tab" data-toggle="tab" aria-expanded="true">{{ cls(model) }}</a>
            </li>
        <div class="btn-group btn-group-xs navbar-right">
            <button type="button" class="btn navbar-btn">create</button>
            <button type="button" class="btn navbar-btn">remove</button>
        </div>
        </ul>
        <div class="tab-content" id="myTabContent">
            <div v-for="model in models" :class="'tab-pane fade in '+pane_active(model)" role="tabpanel" :id="model_id(model)">
                <div v-if="model" class="container-fluid">
                    <div :class="pane_classes(model)">
                        <div v-for="attrs in columns(model)" class="col-xs-4">
                            <detail-item v-for="attr in attrs" :attr="attr[0]" :value="attr[1]" :edit="attr[2]"></detail-item>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>

import * as d3 from "d3";
import Vue from "vue";
import * as tpa from "../js/tpa-api";

export default Vue.extend({
    name: "detail-panel",
    props: ["objects"],
    data: () => ({
    }),
    computed: {
        models() { return this.objects ? this.objects.filter(o => o) : []; }
    },
    methods: {
        cls(m) { return tpa.model_class(m); },
        model_id(m) { return tpa.model_class(m)+'-detail'; },
        pane_classes(m) {
            if (!m) {return "row"; }

            return `row detail_pane selected_${tpa.model_class(m)}_detail`;
        },
        pane_active(obj) {
            let models = this.models;
            return (models[models.length-1] == obj) ? "active" : "";
        },
        columns(model_obj) {
            if (!model_obj) { return []; };
            console.log("Detail:", model_obj);

            let result = [[
                ["Name", model_obj.name],
                ['Description', model_obj.description],
                ['Tags', model_obj.user_tags ?
                    Object.keys(model_obj.user_tags).map(
                        k => k + ": " + model_obj.user_tags[k]).join(", ")
                    : ""]
            ]];

            if(tpa.model_class(model_obj) != 'instance') {
                return result;
            }

            let instance = model_obj;
            const ins_type = instance.instance_type;
            let mem = (ins_type && ins_type.memory) ?
                `, ${ins_type.memory}g memory` : "";

            result.push([
                ['Type', `${ins_type.name} (${ins_type.vcpus} vcpus${mem})`,
                "EDIT"],
                ['Location',
                    `${instance.subnet.zone.region.name}/${instance.subnet.zone.name}`,
                    "EDIT"],
                ['Subnet', instance.subnet.name],
                ['VPC', instance.subnet.vpc.name],
                ['Ext. IP', instance.assign_eip]
            ]);

            result.push([
                ['Roles',
                    instance.roles.map(r => r.role_type).join(", ")],
                ["Volumes",
                    instance.volumes.map(vol => {
                        let p = vol.delete_on_termination ?  "" : " persistent";
                        return `${vol.name} (${vol.volume_size}g${p} ${vol.volume_type})`;
                    }).join(", ")]
            ]);

            return result;
        }
    },
    components: {
        'detail-item': {
            props: ['object', 'attr', 'value', "edit"],
            template: `
<div class="row">
    <div class="attr_name col-xs-3">{{ attr }} </div><div class="attr_value col-xs-7">{{ value }}</div>
    <div v-if="edit" class="attr_edit btn-group btn-group-xs col-xs-2"><button type="button" class="btn navbar-btn" @click="emit_edit(edit)">edit</button></div>
</div>`,
            methods: {
                emit_edit(edit) {
                    this.$emit("edit", this.object, this.attr, this.value, edit);
                }
            },
        }
    }
});

</script>

<style scoped>
</style>
