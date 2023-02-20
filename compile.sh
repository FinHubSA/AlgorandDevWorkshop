#!/bin/sh
# A simple script to compile all Tealish programs in the contracts directory.
# The resulting TEAL programs will be in contracts/build.

for i in contracts/*.tl; do
    [ -f "$i" ] || continue
    tealish compile "$i"
done
