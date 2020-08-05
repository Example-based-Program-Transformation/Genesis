#!/usr/bin/env python
import MySQLdb
from sys import argv
import getopt
from os import system
from repo_handler import create_repo_handler
from time import sleep
import random

host = "127.0.0.1";
passwd = "genesis";
user = "root";
opts, args = getopt.getopt(argv[1:], "", ["host=", "passwd=", "user=", "github-user=", "github-passwd="]);
github_user = "";
github_passwd = "";

for (o, a) in opts:
    if (o == "--host"):
        host = a;
    elif (o == "--passwd"):
        passwd = a;
    elif (o == "--user"):
        user = a;
    elif (o == "--github-user"):
        github_user = a;
    elif (o == "--github-passwd"):
        github_passwd = a;

db = MySQLdb.connect(user = user, host = host, passwd=passwd, db= "genesis");
c = db.cursor();
c.execute("""SELECT id, github_accname, github_reponame, github_url FROM application""");
for row in c:
    idx = row[0];
    accname = row[1];
    reponame = row[2];
    repourl = row[3];
    c2 = db.cursor();
    c2.execute("""SELECT id, github_prepatch_rev, github_postpatch_rev FROM patch WHERE app_id = %s""", (idx,));
    if (c2.rowcount > 0):
        try:
            system("rm -rf __tmp");
            tmpdir = "__tmp";
            if (github_user != ""):
                tmprepourl = repourl[0:8] + github_user + ":" + github_passwd + "@" + repourl[8:];
            system("git clone " + tmprepourl + " " + tmpdir);
            repo = create_repo_handler(tmpdir, "git");
        except:
            print "give up on this repo, try next";
            continue;
        for row2 in c2:
            revid = row2[2];
            try:
                lines = repo.get_commit_log(revid);
            except:
                print "give up this repo, break out";
                break;
            nullFix = False;
            for line in lines:
                if (line.find("null") != -1 or line.find("Null") != -1) and \
                    (line.find("deref") != -1 or line.find("Deref") != -1 or \
                    line.find("pointer") != -1 or line.find("Pointer") != -1 or \
                    line.find("exception") != -1 or line.find("Exception") != -1):
                    nullFix = True;
                    break;
            log = "\n".join(lines);
            c3 = db.cursor();
            c3.execute("""UPDATE patch SET commit_msg = %s WHERE id = %s""", (log, row2[0]));
            if (nullFix):
                print accname + " " + reponame + " " + revid;
                print repourl + "/commit/" + revid;
                c3.execute("""UPDATE patch SET is_null_fix = TRUE WHERE id = %s""", (row2[0],));
            db.commit();
    sleep(random.randint(5, 10));
db.close();
