#!/usr/bin/env bash
rm -r CurrentMBS/Source
cd GitImporter/
python3 ./main.py $1
cd ..
$SHELL
