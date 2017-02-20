
// vim:ts=4:sts=4:sw=4:et:ff=unix:fileencoding=utf-8

/**
 * 
 */

export function make_rect(w, h) {
    return {
        width: w,
        height: h,
        top_left:     { x: -w/2, y: -h/2 },
        top_right:    { x: +w/2, y: -h/2 },
        bottom_right: { x: +w/2, y: +h/2 },
        bottom_left:  { x: -w/2, y: +h/2 }
    };
}
