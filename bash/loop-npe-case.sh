#!/bin/bash
for i in `seq 1 20`;
do
    python/create-case.py $i cases/cdir$i
	mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-init-only -sl -w wdir$i cases/cdir$i/case.conf"
done   
