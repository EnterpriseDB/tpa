
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

/**
 * Tracks user selected objects for the target elements.
 * Expects a d3 selection.
 */
export class UserSelection {
    constructor(target, name="target", enabled=true) {
        this.target = target;
        this.name = name;
        this._enabled = enabled;
        this._current = null;
        this.dispatch = d3.dispatch("selected", "deselected");
    }

    set_selectable(selection) {
        let self = this;
        selection.on("click.selection", function() {
            self.current = this;
        });
    }

    on(event, callback) {
        return this.dispatch.on(event+'.'+this.name, callback);
    }

    get current() { return this._current; }

    set current(o) {
        let self = this;
        if(!self._enabled) return;

        if(self._current) {
            d3.select(self._current).classed("selected", false);
            self.dispatch.call("deselected", self._current);
            self._current = null;
        }

        self._current = o;

        if(self._current) {
            d3.select(self._current).classed("selected", true);
            self.dispatch.call("selected", self._current);
        }
    }

    set enabled(v) {
        if(!v && this._current) {
            this.current = null;
        }

        this._enabled = v;
    }
};
