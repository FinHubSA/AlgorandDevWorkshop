#!/bin/sh
# A simple script to compile all Tealish programs in the contracts directory.
# The resulting TEAL programs will be in contracts/build.
# To run the script, run "./compile.sh" in your terminal at the root directory of this project.
# Ensure that you are in a Python virtual environment with the dependencies
# from the requirements.txt file installed before running this script.
# If you get permission errors, run "chmod +x compile.sh" first to make the script executable.

for i in contracts/*.tl; do
    [ -f "$i" ] || continue
    tealish compile "$i"
done
