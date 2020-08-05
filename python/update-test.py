#!/usr/bin/env python
import getopt
import MySQLdb
from sys import argv

opts, args = getopt.getopt(argv[1:], "", ["host=", "passwd=", "user="]);
host = "127.0.0.1";
passwd = "genesis";
user = "root";

for (o, a) in opts:
    if (o == "--host"):
        host = a;
    elif (o == "--passwd"):
        passwd = a;
    elif (o == "--user"):
        user = a;

assert( len(args) > 0 );
db = MySQLdb.connect(user = user, host=host, passwd=passwd, db="genesis");
for fname in args:
    f = open(fname, "r");
    line = f.readline();
    while (line != ""):
        line = f.readline();
        tokens = line.strip().split();
        patch_id = tokens[0];
        tot_cases = int(tokens[3]);
        c = db.cursor();
        c.execute("""UPDATE patch SET has_test = 1 WHERE id = %s""", (patch_id,));
        for i in range(0, tot_cases):
            line = f.readline();
            s = line.strip();
            idx1 = s.find(" ");
            idx2 = s.rfind(" ");
            className = s[0:idx1].strip();
            testName = s[idx1 + 1:idx2].strip();
            status = s[idx2+1].strip();
            c.execute("""SELECT * FROM testcase WHERE patch_id = %s AND test_class = %s \
                      AND test_name = %s""", (patch_id, className, testName));
            if (c.rowcount == 0):
                c.execute("""INSERT INTO testcase (patch_id, test_class, test_name, status) \
                        VALUES (%s, %s, %s, %s)""", (patch_id, className, testName, status));
        line = f.readline();
db.commit();
