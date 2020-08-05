#!/usr/bin/env python
import getopt
import os
from sys import argv
from os import system, path, getcwd, chdir
from repo_handler import create_repo_handler
import MySQLdb

collect_cnt = 0;

def marshal_reponame(repoaddr):
    s = "_";
    for c in repoaddr:
        if (c == "/"):
            s += "_";
        else:
            s += c;
    return s;

def unmarshal_reponame(reponame):
    ret = "";
    for c in reponame[1:]:
        if (c == "_"):
            ret +="/";
        else:
            ret += c;
    return ret;

def build_pair(repo_dir1, repo_dir2, src_file, file1, file2):
    cmd = 'timeout 5m mvn exec:java -q -e -f ' + pompath + ' -Dexec.mainClass="genesis.learning.TreeDiffer" -Dexec.args="';
    cmd += repo_dir1 + " ";
    cmd += repo_dir2 + " ";
    cmd += repo_dir1 + "/" + src_file + " ";
    cmd += repo_dir2 + "/" + src_file + " "+ file1 + " " + file2 + '"';
    print "Executing cmd: " + cmd;
    ret = system(cmd);
    return (ret == 0);

def rewrite_pair(repo_dir1, repo_dir2, src_file, file1, file2):
    cmd = 'timeout 5m mvn exec:java -q -e -f ' + pompath + ' -Dexec.mainClass="genesis.rewrite.RewritePassManager" -Dexec.args="';
    cmd += repo_dir1 + " ";
    cmd += repo_dir2 + " ";
    cmd += repo_dir1 + "/" + src_file + " ";
    cmd += repo_dir2 + "/" + src_file + " "+ file1 + " " + file2 + '"';
    print "Executing cmd: " + cmd;
    ret = system(cmd);
    if (ret != 0):
        return 2;
    elif (os.path.exists(file1)):
        return 1;
    else:
        return 0;

def analyze_repo(repo_dir, outlogf, outdir, repo_type, fix_only, year_limit, revrec = None):
    global collect_cnt;
    repo = create_repo_handler(repo_dir, repo_type);
    if (revrec == None):
        revs = repo.get_revs(fix_only, year_limit);
    else:
        print "Going for existing revisions:";
        print revrec;
        revs = revrec;
    tmp_dir = "__tmp";
    system("rm -rf " + tmp_dir);
    system("mkdir " + tmp_dir);
    tmp_repo1 = tmp_dir + "/src1";
    tmp_repo2 = tmp_dir + "/src2";
    system("cp -rf " + repo_dir + " " + tmp_repo1);
    system("cp -rf " + repo_dir + " " + tmp_repo2);
    system("rm -rf " + outdir);
    system("mkdir " + outdir);

    repo1 = create_repo_handler(tmp_repo1, repo_type);
    repo2 = create_repo_handler(tmp_repo2, repo_type);
    f = open(outlogf, "w");
    cnt = 0;
    for rev, parent_rev, _ in revs:
        print "Processing rev: ", rev;
        # FIXME: This only works for git
        if (parent_rev == ""):
            parent_rev = rev + "^1";
        diff_res = repo.get_diff_for_java(parent_rev, rev);
        realsrcf = [];
        for srcf in diff_res.keys():
            if (srcf.find("test") != -1) or (srcf.find("Test") != -1):
                continue;
            realsrcf.append(srcf);
        if (len(realsrcf) == 0):
            print "No source file changed!";
            continue;
        if (len(realsrcf) > 1):
            print "Too many file modified!";
            continue;
        src_file = realsrcf[0];
        print "src file: ", src_file;
        print "diff size: ", diff_res[src_file][0];
        repo1.switch_to_rev(parent_rev);
        repo2.switch_to_rev(rev);
        tmp1f = "/tmp/__rewritebefore.java";
        tmp2f = "/tmp/__rewriteafter.java";
        tmp1f_backup = "/tmp/__backupbefore.java";
        tmp2f_backup = "/tmp/__backupafter.java"
        system("rm -rf " + tmp1f + " " + tmp2f + " " + tmp1f_backup + " " + tmp2f_backup);
        rewrite_ret = rewrite_pair(tmp_repo1, tmp_repo2, src_file, tmp1f, tmp2f);
        print "Rewrite RET: " + str(rewrite_ret);
        if rewrite_ret == 1:
            print "Rewrite and store backup!";
            system("cp " + tmp_repo1 + "/" + src_file + " " + tmp1f_backup);
            system("cp " + tmp_repo2 + "/" + src_file + " " + tmp2f_backup);
            system("cp " + tmp1f + " " + tmp_repo1 + "/" + src_file);
            system("cp " + tmp2f + " " + tmp_repo2 + "/" + src_file);

        if (rewrite_ret == 2 or not build_pair(tmp_repo1, tmp_repo2, src_file, outdir + "/b_" + rev + ".po", outdir + "/a_" + rev + ".po")):
            print "Cannot extract pair " + parent_rev;
            if (rewrite_ret == 1):
                print "Restore back!";
                system("cp " + tmp1f_backup + " " + tmp_repo1 + "/" + src_file);
                system("cp " + tmp2f_backup + " " + tmp_repo2 + "/" + src_file);
            cnt += 1;
            if cnt > 50:
                print "Not being able to extract for more than 50 revs in a row, ABORT this project!";
                break;
            continue;

        if rewrite_ret == 1:
            print "Restore back!";
            system("cp " + tmp1f_backup + " " + tmp_repo1 + "/" + src_file);
            system("cp " + tmp2f_backup + " " + tmp_repo2 + "/" + src_file);
        cnt = 0;
        print >> f, rev;
        f.flush();
        collect_cnt += 1;
        if (collect_limit != 0):
            if (collect_cnt >= collect_limit):
                print "Already collected enough revisions, going to terminate!";
                f.close();
                system("rm -rf " + tmp_dir);
                exit(0);

    f.close();
    system("rm -rf " + tmp_dir);

def process_repo(repoaddr, rname, out_dir, revrec):
    system("rm -rf " + rname);
    if github_user == "":
        system("git clone https://github.com" + repoaddr + " " + rname);
    else:
        system("git clone https://" + github_user + ":" + github_passwd + "@github.com" + repoaddr + " " + rname);
    if revrec == None:
        system("rm -rf __tmp");
        system("cp -rf " + rname + " __tmp");
        chdir("__tmp");
        ret = system("mvn compile");
        chdir(ori_dir);
        system("rm -rf __tmp");
        if ret != 0:
            print "Initial Compilation filed!";
            return;
    out_f = out_dir + "/" + rname + "_revs";
    out_src_dir = out_dir + "/" + rname + "_po";
    analyze_repo(rname, out_f, out_src_dir, "git", False, 2010, revrec);

fulldir = path.abspath(path.dirname(argv[0]));
classpath = fulldir + "/../target/classes";
pompath = fulldir + "/../pom.xml";

opts, args = getopt.getopt(argv[1:], "", ["update=", "limit=", "dbhost=", "passwd=", "user=", "nullfix-only", "boundfix-only", "castfix-only", "github-user=", "github-passwd="]);
update_dir = "";
dbhost = "";
user = "root";
passwd = "genesis";
nullfix_only = False;
boundfix_only = False;
castfix_only = False;
collect_limit = 0;
github_user = "";
github_passwd = "";
for (o, a) in opts:
    if (o == "--update"):
        update_dir = a;
    if (o == "--limit"):
        collect_limit = int(a);
    if (o == "--dbhost"):
        dbhost = a;
    if (o == "--user"):
        user = a;
    if (o == "--passwd"):
        passwd = a;
    if (o == "--nullfix-only"):
        nullfix_only = True;
    if (o == "--boundfix-only"):
        boundfix_only = True;
    if (o == "--castfix-only"):
        castfix_only = True;
    if (o == "--github-user"):
        github_user = a;
    if (o == "--github-passwd"):
        github_passwd = a;

assert( len(args) > 1 or update_dir != "" or dbhost != "");
out_dir = args[0];
if (not path.exists(out_dir)):
    system("mkdir " + out_dir);


ori_dir = getcwd();
if update_dir == "" and dbhost == "":
    for repofile in args[1:]:
        f = open(repofile, "r");
        lines = f.readlines();
        for line in lines:
            repoaddr = line.strip();
            print "======================================================";
            print "Start to process REPO: " + repoaddr;
            rname = marshal_reponame(repoaddr);
            if rname == "":
                print "repo with bad character, ABORT this repo!"
                continue;
            process_repo(repoaddr, rname, out_dir, None);
        f.close();
elif update_dir != "":
    print "Only process revisions in the existing directory " + update_dir;
    for root, dirs, files in os.walk(update_dir):
        for fname in files:
            idx = fname.find("_revs");
            if (idx == -1) or (idx + 5 != len(fname)):
                continue;
            repo_name = fname[0:idx];
            f = open(root + "/" + fname, "r");
            lines = f.readlines();
            revs = [];
            for line in lines:
                revs.append((line.strip(), "", ""));
            f.close();
            repo_addr = unmarshal_reponame(repo_name);
            print "======================================================";
            print "Start to process REPO: " + repo_addr;
            process_repo(repo_addr, repo_name, out_dir, revs);
            #analyze_repo(repo_name, out_dir + "/" + repo_name + "_revs", out_dir + "/" + repo_name + "_po", "git", False, 2010, revs);
elif dbhost != "":
    print "Only process revisions in the database!";
    db = MySQLdb.connect(user = user, host = dbhost, passwd = passwd, db="genesis");
    c = db.cursor();
    c.execute("""SELECT id, github_reponame, github_accname, github_url FROM application""");
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
        if (c2.rowcount == 0):
            continue;
        revs = [];
        for row2 in c2:
            revs.append((row2[2], row2[1], ""));
        idx = url.find("github.com");
        short_url = url[idx + 10:];
        print "==============================================================";
        print "Start to process REPO: " + url;
        process_repo(short_url, marshal_reponame(short_url), out_dir, revs);
