#!/usr/bin/env python
import csv;
from sys import argv;
import getopt
import MySQLdb

host = "127.0.0.1";
passwd = "genesis";
user = "root";
opts, args = getopt.getopt(argv[1:], "", ["host=", "passwd=", "user="]);

for (o, a) in opts:
    if (o == "--host"):
        host = a;
    elif (o == "--passwd"):
        passwd = a;
    elif (o == "--user"):
        user = a;

assert( len(args) > 0 );
to_remove = set();
with open(args[0], "rb") as csvfile:
    reader = csv.reader(csvfile);
    first_row = True;
    idx = -1;
    for row in reader:
        if first_row:
            first_row = False;
            for i in range(0, len(row)):
                if row[i].lower() == "remove":
                    idx = i;
                    break;
            if idx == -1:
                print row;
                print "Unable to fix remove row";
        else:
            if len(row) > idx and (row[idx].strip() == "1" or row[idx].strip() == "X"):
                to_remove.add(row[0]);

db = MySQLdb.connect(user = user, host = host, passwd = passwd, db="genesis");
c = db.cursor();
for k in to_remove:
    c.execute("""UPDATE patch SET is_cast_fix = 0 WHERE id = %s""", (str(k),));
db.commit();
