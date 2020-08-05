#!/usr/bin/env python
import os
import MySQLdb
from sys import argv
import getopt

def split_name(fname):
    idx = fname.find("_rev");
    stem = fname[0:idx];
    idx2= stem.rfind("_");
    accname0 = stem[2:idx2];
    reponame0 = stem[idx2 + 1:];
    repourl0 = "https://github.com/" + accname0 + "/" + reponame0;
    outdir0 = stem + "_po";
    return (accname0, reponame0, repourl0, outdir0);

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
db = MySQLdb.connect(user = user, host=host, passwd=passwd, db="genesis");
c = db.cursor();
for root, dirs, files in os.walk(args[0]):
    for fname in files:
        if fname.find("_revs") != -1:
            (accname, reponame, repourl, outdir) = split_name(fname);
            c.execute("""SELECT * FROM application WHERE github_accname=%s AND github_reponame=%s""", (accname, reponame));
            if (c.rowcount == 0):
                c.execute("""INSERT INTO application (github_accname, github_reponame, github_url) \
                           VALUES (%s, %s, %s)""", (accname, reponame, repourl));
                app_id = c.lastrowid;
            else:
                res = c.fetchone();
                app_id = res[0];
                c.execute("""UPDATE application SET last_update = current_timestamp WHERE github_accname=%s AND github_reponame=%s""", (accname, reponame));
            f = open (root + "/" + fname, "r");
            lines = f.readlines();
            f.close();
            for line in lines:
                rev = line.strip();
                c.execute("""SELECT * FROM patch WHERE app_id=%s AND github_postpatch_rev=%s""", (app_id, rev));
                parent_rev = rev + "^1";
                astprepath = outdir + "/b_" + rev + ".po";
                astpostpath = outdir + "/a_" + rev + ".po";
                if (c.rowcount == 0):
                    c.execute("""INSERT INTO patch (app_id, github_prepatch_rev, github_postpatch_rev, ast_prepatch_path, ast_postpatch_path) \
                            VALUES (%s, %s, %s, %s, %s)""", (app_id, parent_rev, rev, astprepath, astpostpath));
db.commit();
