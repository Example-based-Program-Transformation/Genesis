#!/bin/bash
mkdir -p oobcases
rm -rf oobcases/cdir$1
rm -rf oobwdir$1
python/create-case.py --oobcase $1 oobcases/cdir$1
mvn compile
mkdir oobrdir$1
mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-oob -init-only -sl -w oobwdir$1 oobcases/cdir$1/case.conf" | tee oobrdir$1/init.log
if [ "$3" == "oracle" ]; then
    cp oobloc-orcale/loc$1.txt oobwdir$1/localization.log
    echo "Used oracle localization" > oobrdir$1/localization.log
else
    mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-skip-init -w oobwdir$1 -lo" | tee oobrdir$1/localization.log
fi
mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-skip-init -w oobwdir$1 -s oob-space-tv/space.txt -c oob-space-tv/candidate -cp" | tee oobrdir$1/patch_count.log
timeout 5h mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-skip-init -w oobwdir$1 -s oob-space-tv/space.txt -c oob-space-tv/candidate" | tee oobrdir$1/repair.log
mv __patch* oobrdir$1/
tar czf oob-caseno$1.tar.gz oobwdir$1 oobrdir$1
s3cmd put -f oob-caseno$1.tar.gz $2
