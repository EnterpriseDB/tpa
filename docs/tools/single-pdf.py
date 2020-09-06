#!/usr/bin/env python2

from __future__ import print_function

import mimetypes
import subprocess
import re
import os
import sys
from pandocfilters import toJSONFilters, RawBlock, Header, Image

from pprint import pprint

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def headers(key, value, fmt, meta):
    if key == 'Header' and value[0] == 1:
        return [RawBlock('latex', '\\newpage'), Header(value[0], value[1], value[2])]

def links_to_local(key, value, fmt, meta):
    if key == 'Link':
        if value[2][0][-3:] == '.md':
            f = re.sub('^(\.\./)*', '', value[2][0])
            with open(f, 'r') as f:
                first_line = f.readline()
                if first_line[0] == '#':
                    value[2][0] = '#' + first_line[2:].lower().replace(' ', '-').strip()
                else:
                    value[2][0] = '#' + value[2][0][:-3]

def svg_to_pdf(key, value, fmt, meta):
    if key == 'Image':
       attrs, alt, [src, title] = value
       mimet, _ = mimetypes.guess_type(src)
       if mimet == 'image/svg+xml':
           base_name,_ = os.path.splitext(src)
           pdf_name = base_name + ".pdf"
           try:
               mtime = os.path.getmtime(pdf_name)
           except OSError:
               mtime = -1
           if mtime < os.path.getmtime(src):
               cmd_line = ['rsvg-convert', '--format', 'pdf', '-o', pdf_name, src]
               sys.stderr.write("Running %s\n" % " ".join(cmd_line))
               subprocess.call(cmd_line, stdout=sys.stderr.fileno())
           if attrs:
               return Image(attrs, alt, [pdf_name, title])
           else:
               return Image(alt, [pdf_name, title])

if __name__ == "__main__":
  toJSONFilters([headers,links_to_local, svg_to_pdf])
