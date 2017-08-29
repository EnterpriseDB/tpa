#!/bin/sh
#
# Builds a tarball of the current branch's HEAD including TPA itself,
# 2ndQuadrant/ansible, and all python dependencies bundled up into a
# virtualenv.

set -e

WORKING_DIRECTORY=$(pwd)
DIRNAME=tpa-$(git rev-parse --short HEAD)

# Export the current HEAD while respecting .gitattributes
git archive --format tar --prefix=$DIRNAME/TPA/ HEAD|tar xvf -

virtualenv $DIRNAME/tpa-virtualenv
. $DIRNAME/tpa-virtualenv/bin/activate
pip install -U pip
pip install wheel
pip install -r python-requirements.txt
pip install $ANSIBLE_HOME

perl -p -i -e "s|$WORKING_DIRECTORY|/home/tpa|" $DIRNAME/tpa-virtualenv/bin/activate

virtualenv --relocatable $DIRNAME/tpa-virtualenv

pushd $DIRNAME/TPA
git init
git add .
export GIT_AUTHOR_NAME=2ndQuadrant GIT_AUTHOR_EMAIL=info@2ndQuadrant.com
export GIT_COMMITTER_NAME=2ndQuadrant GIT_COMMITTER_EMAIL=info@2ndQuadrant.com
git commit -m "Initial commit corresponding to upstream $DIRNAME"
popd

tar czf $DIRNAME.tgz $DIRNAME
rm -rf $DIRNAME
