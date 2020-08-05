#!/usr/bin/env python
import MySQLdb
from sys import argv
import getopt

host = "127.0.0.1";
passwd = "genesis";
user = "root";
opts, args = getopt.getopt(argv[1:], "", ["host=", "passwd=", "user=", "for-npe", "for-oob", "for-cce"]);

for_npe = True;
for_oob = False;
for_cce = False;
for (o, a) in opts:
    if (o == "--host"):
        host = a;
    elif (o == "--passwd"):
        passwd = a;
    elif (o == "--user"):
        user = a;
    if (o == "--for-npe"):
        for_npe = True;
        for_oob = False;
        for_cce = False;
    if (o == "--for-oob"):
        for_oob = True;
        for_npe = False;
        for_cce = False;
    if (o == "--for-cce"):
        for_oob = False;
        for_npe = False;
        for_cce = True;

assert( len(args) > 0 );
resf = args[0];
db = MySQLdb.connect(user = user, host = host, passwd = passwd, db = "genesis");
c = db.cursor();
f = open(resf, "r");
line = f.readline();
while (line != ""):
    tokens = line.strip().split();
    if (len(tokens) <= 0):
        line = f.readline();
        continue;
    patchid = tokens[0];
    retcode = int(tokens[1]);
    m = int(tokens[2]);
    if (retcode == 2):
        if for_npe:
            c.execute("""UPDATE patch SET for_npe_test = 0 WHERE id = %s""", (patchid,));
            c.execute("""UPDATE testcase SET for_npe_test = 0 WHERE patch_id = %s""", (patchid,));
        elif for_oob:
            assert(for_oob);
            c.execute("""UPDATE patch SET for_oob_test = 0 WHERE id = %s""", (patchid,));
            c.execute("""UPDATE testcase SET for_oob_test = 0 WHERE patch_id = %s""", (patchid,));
        else:
            assert(for_cce);
            c.execute("""UPDATE patch SET for_cce_test = 0 WHERE id = %s""", (patchid,));
            c.execute("""UPDATE testcase SET for_cce_test = 0 WHERE id = %s""", (patchid,));
    elif (retcode == 1):
        c.execute("""SELECT id, test_class, test_name, status FROM testcase WHERE patch_id = %s""", (patchid,));
        positive_cases = set();
        negative_cases = set();
        for row in c:
            status = int(row[3]);
            if (row[3] == 0):
                positive_cases.add((row[1], row[2]));
            else:
                negative_cases.add((row[1], row[2]));
        bad_positive = set();
        bad_negative = set();
        bad = False;
        for i in range(0, m):
            line = f.readline();
            if (line.find("[DEBUG]") == 0):
                continue;
            if (line.find("[WARN]") == 0):
                bad = True;
            if not bad:
                s = line.strip();
                idx = line.find(" ");
                testclass = line[0:idx].strip();
                testname = line[idx+1:].strip();
                if (testclass, testname) in positive_cases:
                    bad_positive.add((testclass, testname));
                else:
                    assert((testclass, testname) in negative_cases);
                    bad_negative.add((testclass, testname));
        if not bad:
            if (len(negative_cases) == len(bad_negative)):
                bad = True;
            if (len(positive_cases) <= len(bad_positive) * 5):
                bad = True;
        if (bad):
            if (for_npe):
                c.execute("""UPDATE patch SET for_npe_test = 0 WHERE id = %s""", (patchid,));
                c.execute("""UPDATE testcase SET for_npe_test = 0 WHERE patch_id = %s""", (patchid,));
            elif for_oob:
                c.execute("""UPDATE patch SET for_oob_test = 0 WHERE id = %s""", (patchid,));
                c.execute("""UPDATE testcase SET for_oob_test = 0 WHERE patch_id = %s""", (patchid,));
            else:
                assert(for_cce);
                c.execute("""UPDATE patch SET for_cce_test = 0 WHERE id = %s""", (patchid,));
                c.execute("""UPDATE testcase SET for_cce_test = 0 WHERE patch_id = %s""", (patchid,));
        else:
            if (for_npe):
                c.execute("""UPDATE patch SET for_npe_test = 1 WHERE id = %s""", (patchid,));
            elif (for_oob):
                c.execute("""UPDATE patch SET for_oob_test = 1 WHERE id = %s""", (patchid,));
            else:
                c.execute("""UPDATE patch SET for_cce_test = 1 WHERE id = %s""", (patchid,));

            for (testclass, testname) in (positive_cases | negative_cases):
                if (testclass, testname) in bad_positive or \
                    (testclass, testname) in bad_negative:
                    v = "0";
                else:
                    v = "1";
                if (for_npe):
                    c.execute("""UPDATE testcase SET for_npe_test = %s WHERE test_class = %s AND test_name = %s""", (v, testclass, testname));
                elif (for_oob):
                    c.execute("""UPDATE testcase SET for_oob_test = %s WHERE test_class = %s AND test_name = %s""", (v, testclass, testname));
                else:
                    c.execute("""UPDATE testcase SET for_cce_test = %s WHERE test_class = %s AND test_name = %s""", (v, testclass, testname));
    else:
        assert(retcode == 0);
        if (for_npe):
            c.execute("""UPDATE patch SET for_npe_test = 1 WHERE id = %s""", (patchid,));
            c.execute("""UPDATE testcase SET for_npe_test = 1 WHERE patch_id = %s""", (patchid,));
        elif (for_oob):
            c.execute("""UPDATE patch SET for_oob_test = 1 WHERE id = %s""", (patchid,));
            c.execute("""UPDATE testcase SET for_oob_test = 1 WHERE patch_id = %s""", (patchid,));
        else:
            c.execute("""UPDATE patch SET for_cce_test = 1 WHERE id = %s""", (patchid,));
            c.execute("""UPDATE testcase SET for_cce_test = 1 WHERE patch_id = %s""", (patchid,));
    line = f.readline();
f.close();
db.commit();
db.close();
