#!/bin/bash
mkdir -p ccecases
rm -rf ccecases/cdir$1
rm -rf ccewdir$1
python/create-case.py --ccecase $1 ccecases/cdir$1
mvn compile
mkdir ccerdir$1
mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-init-only -sl -w ccewdir$1 ccecases/cdir$1/case.conf" | tee ccerdir$1/init.log
if [ "$3" == "oracle" ]; then
    cp cceloc-oracle/loc$1.txt ccewdir$1/localization.log
    echo "Used oracle localization" > ccerdir$1/localization.log
else
    mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-skip-init -w ccewdir$1 -lo" | tee ccerdir$1/localization.log
fi
mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-skip-init -w ccewdir$1 -s cce-space-tv/space.txt -c cce-space-tv/candidate -cp" | tee ccerdir$1/patch_count.log
timeout 5h mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-skip-init -w ccewdir$1 -s cce-space-tv/space.txt -c cce-space-tv/candidate" | tee ccerdir$1/repair.log
mv __patch* ccerdir$1/
tar czf cce-caseno$1.tar.gz ccewdir$1 ccerdir$1
s3cmd put -f cce-caseno$1.tar.gz $2
