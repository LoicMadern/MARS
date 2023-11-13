#!/usr/bin/env bash
mkdir ../projects
cd GitImporter/
python3 ./main.py $1 $2
touch ../../projects/$2/metamodel.json
touch ../../projects/$2/exclude.txt
touch ../../projects/$2/calls.csv
cd ..
$SHELL
