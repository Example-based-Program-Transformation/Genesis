#!/usr/bin/env python
import MySQLdb
from sys import argv
import getopt
from os import system, path
from repo_handler import prepare_casedir
import subprocess

def init_test(pompath, casedir):
    system("rm -rf _workdir");
    cmds = ['timeout', '45m', 'mvn', 'exec:java', '-q', '-e', '-f', \
            pompath, '-Dexec.mainClass="genesis.repair.Main"', \
            '-Dexec.args="-init-only -sl -w _workdir ' + casedir + '/case.conf"'];
    print " ".join(cmds);
    p = subprocess.Popen(" ".join(cmds), stdout = subprocess.PIPE, \
                         stderr = subprocess.PIPE, shell = True);
    out, err = p.communicate();
    print "out:";
    print out;
    print "err:";
    print err;
    ret = p.returncode;
    system("rm -rf _workdir");
    if (ret == 0):
        return (0, []);
    if (ret == 124 or ret == 137):
        return (2, []);
    lines = out.strip().split("\n");
    ret_code = 1;
    in_fail_cases = False;
    failcases = [];
    for line in lines:
        if (line.find("Unable to compile the application!") == 0 or \
            line.find("Cannot determine whether it uses JUnit 3 or 4") == 0 or \
            line.find("Failed when setup the work directory") == 0):
            ret_code = 2;
            break;
        elif (line.find("Unexpected pass of the cases") == 0):
            in_fail_cases = True;
        elif (line.find("Unexpected failure of the cases") == 0):
            in_fail_cases = True;
        elif (in_fail_cases and line.find("Fixes testcase log file before you rerun genesis") == 0):
            in_fail_cases = False;
        elif (in_fail_cases):
            s1 = line.strip();
            idx = s1.find("#");
            failcases.append((s1[0:idx].strip(), s1[idx+1:].strip()));
    if (ret_code == 2):
        return (2, []);
    else:
        return (1, failcases);

opts, args = getopt.getopt(argv[1:], "", ["host=", "user=", "passwd=", "paracount=", "paraid=", "github-user=", "github-passwd=", "nullfix", "boundfix", "castfix"]);
host = "127.0.0.1";
user = "root";
passwd = "genesis";
paracount = 1;
paraid = 0;
github_user = "";
github_passwd = "";
nullfix = False;
boundfix = False;
for (o, a) in opts:
    if (o == "--host"):
        host = a;
    if (o == "--user"):
        user = a;
    if (o == "--passwd"):
        passwd = a;
    if (o == "--paracount"):
        paracount = int(a);
    if (o == "--paraid"):
        paraid = int(a);
    if (o == "--github-user"):
        github_user = a;
    if (o == "--github-passwd"):
        github_passwd = a;
    if (o == "--nullfix"):
        nullfix = True;
    if (o == "--boundfix"):
        boundfix = True;
    if (o == "--castfix"):
        castfix = True;

db = MySQLdb.connect(user = user, host = host, passwd = passwd, db = "genesis");
c = db.cursor();
if (nullfix):
    c.execute("""SELECT patcht.id, patcht.github_prepatch_rev, patcht.github_postpatch_rev, \
            application.github_url FROM (SELECT * from patch where has_test = 1 and is_null_fix = 1) as patcht \
            LEFT JOIN application ON patcht.app_id = application.id;""");
elif (boundfix):
    c.execute("""SELECT patcht.id, patcht.github_prepatch_rev, patcht.github_postpatch_rev, \
            application.github_url FROM (SELECT * from patch where has_test = 1 and is_bound_fix = 1) as patcht \
            LEFT JOIN application ON patcht.app_id = application.id;""");
elif (castfix):
     c.execute("""SELECT patcht.id, patcht.github_prepatch_rev, patcht.github_postpatch_rev, \
            application.github_url FROM (SELECT * from patch where has_test = 1 and is_cast_fix = 1) as patcht \
            LEFT JOIN application ON patcht.app_id = application.id;""");
else:
    c.execute("""SELECT patcht.id, patcht.github_prepatch_rev, patcht.github_postpatch_rev, \
            application.github_url FROM (SELECT * from patch where has_test = 1) as patcht \
            LEFT JOIN application ON patcht.app_id = application.id;""");
revs = [];
for row in c:
    testcases = [];
    c2 = db.cursor();
    c2.execute("""SELECT test_class, test_name, status FROM testcase WHERE patch_id = %s""", (row[0],));
    for row2 in c2:
        testcases.append((row2[0], row2[1], row2[2]));
    revs.append((row[0], row[1], row[2], row[3], testcases));
    c2.close();
c.close();
db.close();

tmpcasedir = "__tmpcasedir";
fulldir = path.abspath(path.dirname(argv[0]));
pompath = fulldir + "/../pom.xml";
results = {};
cnt = 0;
for (patchid, prerev, postrev, url, testcases) in revs:
    cnt += 1;
    if (paracount > 1):
        if (cnt % paracount != paraid):
            continue;
    system("rm -rf " + tmpcasedir);
    prepare_casedir(patchid, prerev, postrev, url, testcases, tmpcasedir, github_user, github_passwd);
    res = init_test(pompath, tmpcasedir);
    results[patchid] = res;
    print res;

f = open(args[0], "w");
for patchid in results.keys():
    (retcode, testcases) = results[patchid];
    print >> f, patchid, retcode, len(testcases);
    for (classname, name) in testcases:
        print >> f, classname, name;
f.close();
