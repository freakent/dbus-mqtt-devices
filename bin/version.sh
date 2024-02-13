#!/bin/sh
BASE=$(dirname $(dirname $(realpath "$0")))
echo $1 > $BASE/VERSION
sed -e "s/\$VERSION/$1/g" $BASE/README.md.tmpl > $BASE/README.md