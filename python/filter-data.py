#!/usr/bin/env python
import getopt
import MySQLdb
from sys import argv
from os import system
import os

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

assert( len(args) > 1 );
datadir = args[0];
newdatadir = args[1];
system("mkdir " + newdatadir);
db = MySQLdb.connect(user = user, host = host, passwd = passwd, db = "genesis");
c = db.cursor();
c.execute("""SELECT ast_prepatch_path, ast_postpatch_path, id FROM patch WHERE is_null_fix = 1 or is_bound_fix = 1 or is_cast_fix = 1""");
l = [];
bad_id = set();
for row in c:
    if (len(row[0]) > 0 and len(row[1]) > 0):
        if not os.path.exists(datadir + "/" + row[0]):
            print row[0];
            print "Not exist!";
            bad_id.add(row[2]);
            continue;
        cmd1 = "cp --parent " + datadir + "/" + row[0] + " " + newdatadir + "/";
        cmd2 = "cp --parent " + datadir + "/" + row[1] + " " + newdatadir + "/";
        system(cmd1);
        system(cmd2);
for idx in bad_id:
    c.execute("""UPDATE patch SET is_null_fix = 0, is_bound_fix = 0, is_cast_fix = 0 WHERE id = %s""", (idx,));
c.close();
db.commit();
db.close();

print len(bad_id);
