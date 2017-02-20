
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

/**
 * Misc utilities.
 */

// Read a page's GET URL variables and return them as an associative array.
export function get_url_vars()
{
    var vars = [], pair;
    var pairs = window.location.href.slice(
            window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < pairs.length; i++)
    {
        pair = pairs[i].split('=');
        vars.push(pair[0]);
        vars[pair[0]] = pair[1];
    }
    return vars;
}



export class Accumulator {
    constructor () {
        this.dict = {};
        this.keys = [];
    }

    add(key, value) {
        if ( !(key in this.dict) ) {
            this.dict[key] = [value];
            this.keys.push(key);
        }
        else if (this.dict[key].indexOf(value) < 0) {
            this.dict[key].push(value);
        }
    }
}


export function sort_by_attr(array, attr) {
    array.sort((obj_a, obj_b) => {
        if (obj_a[attr] < obj_b[attr]) return -1;
        if (obj_a[attr] > obj_b[attr]) return 1;
        return 0;
    });
}
