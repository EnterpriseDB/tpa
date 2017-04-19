<template>
<div id="attribute-edit-popup" class="modal fade">
    <div class="modal-dialog">
        <div class="modal-content">
                <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
                    <h4 class="modal-title">Editing <span class="name">{{ object_name }}</span></h4>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <p class="col-xs-2">{{ name }}</p>
                        <component :class="'attribute-value-editor value-editor-'+model" ref="editor" :is="model" :object="object" :name="name"></component>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-default" @click="reset">Reset</button>
                    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                    <button type="submit" class="btn btn-success attr-save" @click="save">Save</button>
                </div>
            </form>
        </div>
    </div>
</div>
</template>
<script>

import * as d3 from "d3";
import $ from "jquery";
import * as tpa from "../js/tpa-api";
import Vue from "vue";

let ValueEditor = Vue.extend({
    props: ['object', 'name'],
    template:
`<input v-model="selected_value" :name="name" class="col-xs-4"></input>`,
    data() {
        return {
            prev_object: null,
            value: null,
        }
    },
    computed: {
        selected_value: {
            get() {
                if (this.value) {
                    if (this.prev_object == this.object) {
                        return this.value;
                    }
                    else {
                        this.prev_object = this.object;
                        this.value = null;
                    }
                }

                return this.get_current_value();
            },
            set(v) {
                if(v == this.selected_value) { return; }

                this.value = v;
                this.prev_object = this.object;
            }
        }
    },
    methods: {
        reset() {
            this.value = null;
            this.prev_object = null;
        },
        get_current_value() {
            return this.object[this.name.toLowerCase()];
        },
        save() {
            this.object[this.name.toLowerCase()] = this.value;
            this.value = null;
            this.prev_object = null;
        }
    }
});


let ZoneEditor = ValueEditor.extend({
    template:
`<div><select v-model="selected_region">
    <option disabled value="">Select a region...</option>
    <option v-for="region in available_regions" :value="region.uuid">{{ region.name }}</option>
</select>
<select v-model="selected_value">
    <option disabled value="">Select a zone...</option>
    <option v-for="zone in available_zones" :value="zone.uuid">{{ zone.name }}</option>
</select></div>`,
    data() {
        return {
            selected_region: null,
        }
    },
    computed: {
        available_regions() {
             return tpa.default_provider[0].regions;
        },
        curr_region() {
            return this.available_regions.filter(r => r.uuid == this.selected_region)[0];
        },
        available_zones() {
            if (!this.curr_region) { return []; };
            return this.curr_region.zones;
        },
    },
    mounted() {
        if(!this.object) {return;}
        this.selected_region = this.object.subnet.zone.region.uuid;
    },
    methods: {
        get_current_value() {
            if(!this.object) { return null; }
            return this.object.subnet.zone.uuid;
        },
        save() {
        }
    }
});


let InstanceTypeEditor = ValueEditor.extend({
    template:
`<div><select v-model="selected_value">
    <option disabled value="">Select a type...</option>
    <option v-for="itype in available_types" :value="itype.uuid">{{ itype.name }}</option>
</select></div>`,
    computed: {
        available_types() {
            if(!this.object) { return []; };
             return this.object.subnet.zone.instance_types;
        },
    },
    methods: {
        get_current_value() {
            return this.object.instance_type.uuid;
        },
        save() {
            this.object.instance_type =
                this.available_types.filter(
                    t => t.uuid == this.selected_value)[0];
        }
    }
});


export default Vue.extend({
    name: 'inline-attr-editor',
    data: () => ({
        object: null,
        name: null,
        model: null,
    }),
    computed: {
        object_name() { return this.object ? this.object.name: "<none>";
        }
    },
    methods: {
        reset() {
            this.$refs.editor.reset();
        },
        show_modal(object, name, value, model) {
            this.object = object;
            this.name = name;
            this.model = model;
            $(this.$el).modal("show");
            this.$forceUpdate();
        },
        save() {
            this.$refs.editor.save(this.object);
            $(this.$el).modal("hide");
            this.$emit("saved");

            this.object = null;
            this.name = null;
            this.model = null;
        }
    },
    components: {
        'text-value': ValueEditor,
        'zone': ZoneEditor,
        'instance_type': InstanceTypeEditor
    }
});
</script>
