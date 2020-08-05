#!/bin/bash
mkdir -p cases
rm -rf cases/cdir$1
rm -rf wdir$1
python/create-case.py $1 cases/cdir$1
mvn compile
mkdir rdir$1
mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-init-only -sl -w wdir$1 cases/cdir$1/case.conf" | tee rdir$1/init.log
if [ "$2" == "oracle" ]; then
    cp npeloc-oracle/loc$1.txt wdir$1/localization.log
    echo "Used oracle localization" > rdir$1/localization.log
else
    mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-skip-init -w wdir$1 -lo" | tee rdir$1/localization.log
fi
mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-skip-init -w wdir$1 -s npe-space/space.txt -c npe-space/candidate -cp" | tee rdir$1/patch_count.log
timeout 5h mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-skip-init -w wdir$1 -s npe-space/space.txt -c npe-space/candidate" | tee rdir$1/repair.log
mv __patch* rdir$1/
