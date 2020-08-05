#!/bin/bash
for i in `seq 1 23`;
do
    python/create-case.py --ccecase $i ccecases/cdir$i
	mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-init-only -sl -w wdir$i ccecases/cdir$i/case.conf"
done   
