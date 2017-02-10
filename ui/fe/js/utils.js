
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

/**
 * 
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
