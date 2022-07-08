#!/usr/bin/env bash
cd Extractor/
sudo python3 ./main.py 
cd ../Detector
python3 main.py --metamodel ../metamodel.json | tee ../output.txt
cd ../.
$SHELL
