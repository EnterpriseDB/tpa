
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

    on(event, callback) {
        return this.dispatch.on(event+'.'+this.name, callback);
    }

    get current() { return this._current; }

    set current(o) {
        if(!self._enabled) return;

        if(this._current) {
            d3.select(this._current).classed("selected", false);
            this.dispatch.call("deselected", this._current);
            this._current = null;
        }

        this._current = o;
        d3.select(this._current).classed("selected", true);
        this.dispatch.call("selected", this._current);
    }

    set enabled(v) {
        if(!v && this._current) {
            this.current = null;
        }

        this._enabled = v;
    }
};
