#!/usr/bin/env python
from sys import argv, exit
from os import getcwd, system, path
import getopt
import subprocess

from repo_handler import create_repo_handler

dir = getcwd()

out_dir = "oob_data"
system("mkdir -p __tmp")
orig_src_dir = "__tmp/orig_src"
src1_dir = "__tmp/src1"
src2_dir = "__tmp/src2"
collect_cnt = 0
collect_limit = 5000

fulldir = path.abspath(path.dirname(argv[0]))
classpath = fulldir + "/../target/classes"
pompath = fulldir + "/../pom.xml"
github_user = "";
github_passwd = "";
rewrite = False;
opts, args = getopt.getopt(argv[1:], "", ["github-user=", "github-passwd=", "rewrite"]);
for (o, a) in opts:
    if (o == "--github-user"):
        github_user = a;
    if (o == "--github-passwd"):
        github_passwd = a;
    if (o == "--rewrite"):
        rewrite = True;

def main():
    f = open(args[0])
    for line in f.readlines():
        process_repo(line.split(" ")[0])

def process_repo(repo_gh_path):
    resDirName = marshal_reponame(repo_gh_path)
    # Process is:
    #   - Clone repo
    #   - git log --grep to find commits matching the oob criterion
    #   - for each of these commits, git diff --name-only & ensure only one
    #     real file
    #   - Check out both revisions and ensure that both build
    #   - Steal most of analyze_repo from crawler.py, since I'm not sure what
    #     exactly the rewrite/backup stuff is doing.
    print("* Processing project: " + repo_gh_path)
    system("rm -rf " + orig_src_dir)
    ret = 0;
    if (github_user == ""):
        ret = system("git clone https://github.com/" + repo_gh_path + " " + orig_src_dir)
    else:
        ret = system("git clone https://" + github_user + ":" + github_passwd + "@github.com/" + repo_gh_path + " " + orig_src_dir);
    if ret != 0:
        print("* Cannot clone from github, give up!");
        return;

    p = subprocess.Popen("git log -i --grep=\"array\\|index\\|check\\|fix\\|error\\|exception\\|oob\" --grep=\"bounds\\|bound \\|oob\" --all-match --oneline", stdout = subprocess.PIPE, cwd=orig_src_dir, shell=True);
    (out, err) = p.communicate();
    ret = p.returncode;

    out_f = out_dir + "/" + resDirName + "_revs"
    out_src_dir = out_dir + "/" + resDirName + "_po"
    system("rm -rf " + out_src_dir)
    system("mkdir " + out_src_dir)
    f = open(out_f, "w")

    for line in out.split("\n"):
        if line != "":
            process_commit(line.split(" ")[0], resDirName, out_f, out_src_dir, f);
    f.close()

def process_commit(commit_id, resDirName, out_f, out_src_dir, f):
    print("Processing commit: " + commit_id)
    # Check for the right files
    p = subprocess.Popen(["git", "diff", "--name-only",
                          commit_id, commit_id+"^"]
                        ,stdout=subprocess.PIPE
                        ,cwd=orig_src_dir)
    (out, err) = p.communicate()
    files = out.split("\n")
    def isJava(x): return x.endswith(".java") or x.endswith(".Java")
    def isTest(x): return x.find("test") != -1 or x.find("Test") != -1
    src_files = filter(lambda x: isJava(x) and not isTest(x), files)
    if len(src_files) == 0:
        print("No source files changed!")
        return
    if len(src_files) > 1:
        print("Too many files changed!")
        return
    src_file = src_files[0]
    print("src file: " + src_file)
    # Check that it's buildable in both configurations
    system("rm -rf " + src1_dir)
    system("cp -rf " + orig_src_dir + " " + src1_dir)
    system("rm -rf " + src2_dir)
    system("cp -rf " + orig_src_dir + " " + src2_dir)
    repo1 = create_repo_handler(src1_dir, "git")
    repo2 = create_repo_handler(src2_dir, "git")
    repo1.switch_to_rev(commit_id+"^")
    repo2.switch_to_rev(commit_id)
    #if not check_buildable(src1_dir) or not check_buildable(src2_dir):
    #    print("Building revision failed.")
    #    return
    # This all came from crawler.py, and is slightly mysterious
    tmp1f = "/tmp/__rewritebefore.java";
    tmp2f = "/tmp/__rewriteafter.java";
    tmp1f_backup = "/tmp/__backupbefore.java"
    tmp2f_backup = "/tmp/__backupafter.java"
    if (rewrite):
        system("rm -rf " + tmp1f + " " + tmp2f + " " + tmp1f_backup + " " + tmp2f_backup)
        rewrite_ret = rewrite_pair(src1_dir, src2_dir, src_file, tmp1f, tmp2f)
        print("Rewrite RET: " + str(rewrite_ret))
        if rewrite_ret == 1:
            print("Rewrite and store backup!")
            system("cp " + src1_dir + "/" + src_file + " " + tmp1f_backup);
            system("cp " + src2_dir + "/" + src_file + " " + tmp2f_backup);
            system("cp " + tmp1f + " " + src1_dir + "/" + src_file);
            system("cp " + tmp2f + " " + src2_dir + "/" + src_file);
    else:
        rewrite_ret = 0;

    if (rewrite_ret == 2 or not build_pair(src1_dir, src2_dir, src_file, out_src_dir + "/b_" + commit_id + ".po", out_src_dir + "/a_" + commit_id + ".po")):
        print("Cannot extract pair " + commit_id + "^");
        if (rewrite_ret == 1):
            print("Restore back!");
            system("cp " + tmp1f_backup + " " + src1_dir + "/" + src_file);
            system("cp " + tmp2f_backup + " " + src2_dir + "/" + src_file);
        #cnt += 1;
        #if cnt > 50:
        #    print("Not being able to extract for more than 50 revs in a row, ABORT this project!");
        #    break
        return

    if rewrite_ret == 1:
        print("Restore back!");
        system("cp " + tmp1f_backup + " " + src1_dir + "/" + src_file);
        system("cp " + tmp2f_backup + " " + src2_dir + "/" + src_file);

    #cnt = 0
    f.write(commit_id+'\n')
    f.flush()
    global collect_cnt
    collect_cnt += 1
    if collect_limit != 0:
        if collect_cnt >= collect_limit:
            print("Already collected enough revisions, going to terminate!")
            f.close()
            exit(0)

def check_buildable(src_dir):
    p = subprocess.Popen(["mvn", "compile"], cwd=src_dir)
    return p.wait() == 0

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
    elif (path.exists(file1)):
        return 1;
    else:
        return 0;

main()
