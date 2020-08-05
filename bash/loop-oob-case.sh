#!/bin/bash
for i in `seq 1 13`;
do
    python/create-case.py --oobcase $i oobcases/cdir$i
	mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-init-only -sl -w wdir$i oobcases/cdir$i/case.conf"
done   
