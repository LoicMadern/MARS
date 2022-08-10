#!/usr/bin/env bash
cd Extractor/
sudo python3 ./main.py --project $1 --url $2
cd ../Detector
python3 main.py --project_name $1 --metamodel ../../projects/$1/metamodel.json | tee ../../projects/$1/output.txt
cd ../.
$SHELL
