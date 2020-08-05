#!/usr/bin/env python
import os
from os import system
import MySQLdb
from sys import argv
import getopt
from repo_handler import create_repo_handler

def unmarshal_reponame(reponame):
    ret = "";
    if (reponame[0] != "_"):
        repos = reponame;
    else:
        repos = reponame[1:];
    for c in repos:
        if (c == "_"):
            ret +="/";
        else:
            ret += c;
    return ret;

opts, args = getopt.getopt(argv[1:], "", ["dbhost=", "passwd=", "user=", "github-user=", "github-passwd=", "nomsg"]);
dbhost = "127.0.0.1";
user = "root";
passwd = "genesis";
github_user = "";
github_passwd = "";
nomsg = False;
for (o, a) in opts:
    if (o == "--dbhost"):
        dbhost = a;
    if (o == "--passwd"):
        passwd = a;
    if (o == "--user"):
        user = a;
    if (o == "--github-user"):
        github_user = a;
    if (o == "--github-passwd"):
        github_passwd = a;
    if (o == "--nomsg"):
        nomsg = True;

d = args[0];
res = {};
revset = set();
for root, dirs, files in os.walk(d):
    for fname in files:
        if (fname.find("_revs") == -1):
            continue;
        f = open(root + "/" + fname);
        lines = f.readlines();
        rurl = fname[0:len(fname) - 5];
        res[rurl] = [];
        for line in lines:
            if not (line.strip() in revset):
                res[rurl].append(line.strip());
                revset.add(line.strip())
        f.close();

diff = 0;
db = MySQLdb.connect(user = user, host = dbhost, passwd = passwd, db = "genesis");
diable = set();
for rev in revset:
    c = db.cursor();
    c.execute("""SELECT * FROM patch WHERE github_postpatch_rev like %s """, (rev + "%",));
    if c.rowcount != 0:
        diable.add(rev);
    c.close();
db.close();

res2 = [];
for rurl in res.keys():
    created = False;
    repo = None;
    revs = res[rurl];
    for rev in revs:
        if rev in diable:
            continue;
        if not created and not nomsg:
            created = True;
            system("rm -rf __tmp");
            if (github_user != ""):
                ret = system("git clone https://" + github_user + ":" + github_passwd + "@github.com/" + unmarshal_reponame(rurl) + " __tmp");
            else:
                ret = system("git clone https://github.com/" + unmarshal_reponame(rurl) + " __tmp");
            if (ret != 0):
                print "Cannot fetch the repo, give up the repo!";
                break;
            repo = create_repo_handler("__tmp", "git");
        if nomsg:
            commit_msg = "";
        else:
            commit_msg = "\n".join(repo.get_commit_log(rev))
        res2.append((rurl, rev, commit_msg));

print res2;

db = MySQLdb.connect(user = user, host = dbhost, passwd = passwd, db = "genesis");
for (rurl, rev, commit_msg) in res2:
    c = db.cursor();
    s1 = rurl[1:];
    idx = s1.find("_");
    accname = s1[0:idx];
    reponame = s1[idx+1:];
    github_url = "https://github.com/" + unmarshal_reponame(rurl);
    c.execute("SELECT * FROM application WHERE github_accname=%s AND github_reponame=%s""", (accname, reponame));
    if (c.rowcount == 0):
        c.execute("""INSERT INTO application (github_accname, github_reponame, github_url) \
                  VALUES (%s, %s, %s)""", (accname, reponame, github_url));
        app_id = c.lastrowid;
    else:
        row = c.fetchone();
        app_id = row[0];
    ast_prepatch_path = rurl + "_po/b_" + rev + ".po";
    ast_postpatch_path = rurl + "_po/a_" + rev + ".po";
    c.execute("""INSERT INTO patch (app_id, github_prepatch_rev, github_postpatch_rev, ast_prepatch_path, ast_postpatch_path, commit_msg) \
              VALUES (%s, %s, %s, %s, %s, %s)""", (app_id, rev + "^1", rev, ast_prepatch_path, ast_postpatch_path, commit_msg));
    c.close();
db.commit();
db.close();

