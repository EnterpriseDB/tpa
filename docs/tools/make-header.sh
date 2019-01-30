#!/bin/bash

if [[ -n "$VERSION" ]]; then
    v=$VERSION
    if [[ -n "$EXTRA_VERSION" ]]; then
        v="$v-$EXTRA_VERSION"
    fi
fi

if [[ -n "$SRC_GIT_DATE" ]]; then
    d=$(date -d "$SRC_GIT_DATE" +"%e %B %G")
else
    d=$(date +"%e %B %G")
fi

cat <<EOF
---
classification: internal
title: TPAexec
author: 2ndQuadrant
version: ${v}
date: $d
toc: yes
header-includes:
- \usepackage{float}
- \floatplacement{figure}{H}
- \newcommand{\passthrough}[1]{#1}
- \lstset{backgroundcolor=\color{lightgray!30},basicstyle=\fontfamily{txtt}\fontsize{11}{13.2}\selectfont,basewidth=0.53em}
---

EOF
