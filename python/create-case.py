#!/usr/bin/env python
import MySQLdb
from sys import argv
import getopt
from os import system, path
from repo_handler import prepare_casedir

opts, args = getopt.getopt(argv[1:], "", ["host=", "user=", "passwd=", "oobcase", "ccecase"]);
host = "127.0.0.1";
user = "root";
passwd = "genesis";
t = "for_npe_test";
for (o, a) in opts:
    if (o == "--host"):
        host = a;
    if (o == "--user"):
        user = a;
    if (o == "--passwd"):
        passwd = a;
    if (o == "--oobcase"):
        t = "for_oob_test";
    if (o == "--ccecase"):
        t = "for_cce_test";

db = MySQLdb.connect(user = user, host = host, passwd = passwd, db = "genesis");
c = db.cursor();
c.execute("""SELECT patcht.id, patcht.github_prepatch_rev, patcht.github_postpatch_rev, \
          application.github_url FROM (SELECT * from patch where """ + t + """ = 1) as patcht \
          LEFT JOIN application ON patcht.app_id = application.id;""");
case_id = int(args[0]);
outdir = args[1];
if (case_id <= 0):
    print "Must be a positive id!";
    exit(1);
if (case_id > c.rowcount):
    print "Maximum case id: ", c.rowcount;
    exit(1);
system("rm -rf " + args[1]);
system("mkdir " + args[1]);
cnt = 0;
for row in c:
    cnt += 1;
    if (case_id != cnt):
        continue;
    patchid = row[0];
    prerev = row[1];
    postrev = row[2];
    url = row[3];
    c2 = db.cursor();
    c2.execute("""SELECT test_class, test_name, status FROM testcase WHERE patch_id = %s AND """ + t + """ = 1""", (patchid,));
    testcases = [];
    for row2 in c2:
        testcases.append((row2[0], row2[1], row2[2]));
    prepare_casedir(patchid, prerev, postrev, url, testcases, outdir, "", "");
    break;
system("rm -rf __tmp");
print "Generation complete!";
if (case_id == 1 and t == "for_npe_test"):
    fulldir = path.abspath(path.dirname(argv[0]));
    case1pom = fulldir + "/case1-pom.xml";
    system("cp -rf " + case1pom + " " + outdir + "/src_orig/pom.xml");
if (case_id == 15 and t == "for_npe_test"):
    fulldir = path.abspath(path.dirname(argv[0]));
    pom1 = fulldir + "/case15-pom-gwt.xml";
    system("cp -rf " + pom1 + " " + outdir + "/src_orig/pom-gwt.xml");
    pom1 = fulldir + "/case15-pom-main.xml";
    system("cp -rf " + pom1 + " " + outdir + "/src_orig/pom-main.xml");

db.close();
