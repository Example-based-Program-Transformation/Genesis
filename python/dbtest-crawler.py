#!/usr/bin/env python
import getopt
from sys import argv
from os import system, path
import MySQLdb
from maven_testinfo import maven_testinfo
from repo_handler import prepare_repodir

def myhash(s):
    ret = 0;
    for c in s:
        ret += ord(c);
    return ret;

fulldir = path.abspath(path.dirname(argv[0]));
classpath = fulldir + "/../target/classes";
pompath = fulldir + "/../pom.xml";

opts, args = getopt.getopt(argv[1:], "", ["dbhost=", "passwd=", "user=", "github-user=", "github-passwd=", "paracount=", "paraid=", "boundfix", "nullfix", "castfix"]);
dbhost = "127.0.0.1";
user = "root";
passwd = "genesis";
nullfix_only = False;
boundfix_only = False;
github_user = "";
github_passwd = "";
paracount = 1;
paraid = 0;
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
    if (o == "--paracount"):
        paracount = int(a);
    if (o == "--paraid"):
        paraid = int(a);
    if (o == "--boundfix"):
        boundfix_only = True;
    if (o == "--nullfix"):
        nullfix_only = True;
    if (o == "--castfix"):
        castfix_only = True;
outfname = args[0];

db = MySQLdb.connect(user = user, host = dbhost, passwd = passwd, db="genesis");
c = db.cursor();
c.execute("""SELECT id, github_reponame, github_accname, github_url FROM application""");
apps = [];
for row in c:
    appid = row[0];
    url = row[3];
    c2 = db.cursor();
    if nullfix_only:
        c2.execute("""SELECT id, github_prepatch_rev, github_postpatch_rev FROM patch WHERE app_id = %s AND is_null_fix = 1""", (appid,));
    elif boundfix_only:
        c2.execute("""SELECT id, github_prepatch_rev, github_postpatch_rev FROM patch WHERE app_id = %s AND is_bound_fix = 1""", (appid,));
    elif castfix_only:
        c2.execute("""SELECT id, github_prepatch_rev, github_postpatch_rev FROM patch WHERE app_id = %s AND is_cast_fix = 1""", (appid,));
    else:
        c2.execute("""SELECT id, github_prepatch_rev, github_postpatch_rev FROM patch WHERE app_id = %s""", (appid,));
    patches = [];
    for row2 in c2:
        patchid = row2[0];
        prepatch_rev = row2[1];
        postpatch_rev = row2[2];
        if (paracount > 1):
            # I am using this because I want it deterministic
            # system built-in one is not
            myhashid = myhash(row2[2]) % paracount;
            if (myhashid != paraid):
                continue;
        patches.append((patchid, prepatch_rev, postpatch_rev));
    apps.append((appid, url, patches));

fout = open(outfname, "w");
for (appid, url, patches) in apps:
    if (len(patches) == 0):
        continue;
    print "Processing repo: " + url;
    system("rm -rf __tmp");
    system("mkdir __tmp");
    repo_dir = "__tmp/src";
    if github_user == "":
        system("git clone " + url + " " + repo_dir);
    else:
        new_url = url[0:8] + github_user + ":" + github_passwd + "@" + url[8:];
        system("git clone " + new_url + " " + repo_dir);
    for (patchid, prepatch_rev, postpatch_rev) in patches:
        print "Processing rev: " + prepatch_rev + " " + postpatch_rev;
        pre_repo_dir = "__tmp/src1";
        post_repo_dir = "__tmp/src2";
        ret = prepare_repodir(repo_dir, "git", prepatch_rev, postpatch_rev, pre_repo_dir, post_repo_dir);
        if (not ret):
            print "Prepare repo failed, probably some directory structure change between revisions";
            system("rm -rf " + pre_repo_dir + " " + post_repo_dir);
            continue;
        pre_info = maven_testinfo(pre_repo_dir);
        post_info = maven_testinfo(post_repo_dir);
        if (pre_info.malform or post_info.malform):
            print "Pre- or Post-patch failed test cases strangely!";
            continue;
        pre_passed = pre_info.passed_cases();
        post_passed = post_info.passed_cases();
        diff = set(post_passed);
        diff -= pre_passed;
        print "Pre passed: ", len(pre_passed);
        print "Post passed: ", len(post_passed);
        print "Diff size: ", len(diff);
        # we are going to avoid strange compilation error caused by
        # copy testFiles and inferface changes
        if (post_passed > pre_passed) and (len(diff) < 10) and (len(pre_passed) > 0):
            print >> fout, appid, url;
            print >> fout, patchid, prepatch_rev, postpatch_rev, len(post_passed);
            for testcase in post_passed:
                print >>fout, testcase[0], testcase[1],
                if testcase in pre_passed:
                    print >>fout, 0;
                else:
                    print >>fout, 1;
            fout.flush();
    system("rm -rf __tmp");
fout.close();
