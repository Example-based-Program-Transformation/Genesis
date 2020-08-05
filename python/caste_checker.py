#!/usr/bin/env python
from sys import argv, exit
from os import getcwd, system, path
import getopt
import subprocess

from repo_handler import create_repo_handler

dir = getcwd()

out_dir = "caste_data"
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

# usage: caste_checker.py <repo user> <repo name> <commits file>

def main():
    repo_user = args[0]
    repo_name = args[1]
    process_repo(repo_user, repo_name, args[2])

def commit_failure(commit_id):
  print("=====================================================================")
  print(" FINAL REPORT: COMMIT STATUS FOR COMMIT: " + commit_id)
  print(" COMMIT PROCESSING FAILED: UNSUITABLE FOR GENESIS")
  print("=====================================================================")

def commit_success(commit_id):
  print("=====================================================================")
  print(" FINAL REPORT: COMMIT STATUS FOR COMMIT: " + commit_id)
  print(" COMMIT PROCESSING SUCCEEDED: SUITABLE FOR GENESIS")
  print("=====================================================================")

def process_repo(repo_user, repo_name, commits_file):
  resDirName = repo_user + "_" + repo_name
  print("* Processing project: " + repo_user + "/" + repo_name)
  system("rm -rf " + orig_src_dir)
  ret = 0
  ret = system("git clone https://github.com/" + repo_user + "/" + repo_name + " " + orig_src_dir)
  if ret != 0:
    print("* Cannot clone from github, give up!");
    return;

  out_f = out_dir + "/" + resDirName + "_revs"
  out_src_dir = out_dir + "/" + resDirName + "_po"
  system("rm -rf " + out_src_dir)
  system("mkdir " + out_src_dir)
  f = open(out_f, "w")

  commits_f = open(commits_file)
  for line in commits_f.readlines():
    process_commit(line.strip(), resDirName, out_f, out_src_dir, f);
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
        commit_failure(commit_id)
        return
    if len(src_files) > 1:
        print("Too many files changed!")
        commit_failure(commit_id)
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
        commit_failure(commit_id)
        return

    if rewrite_ret == 1:
        print("Restore back!");
        system("cp " + tmp1f_backup + " " + src1_dir + "/" + src_file);
        system("cp " + tmp2f_backup + " " + src2_dir + "/" + src_file);

    commit_success(commit_id)

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

def build_pair(repo_dir1, repo_dir2, src_file, file1, file2):
    cmd = 'timeout 5m mvn exec:java -q -e -f ' + pompath + ' -Dexec.mainClass="genesis.learning.TreeDiffer" -Dexec.args="';
    cmd += repo_dir1 + " ";
    cmd += repo_dir2 + " ";
    cmd += repo_dir1 + "/" + src_file + " ";
    cmd += repo_dir2 + "/" + src_file + " "+ file1 + " " + file2 + '"';
    print("Executing cmd: " + cmd)
    ret = system(cmd);
    return (ret == 0);

def rewrite_pair(repo_dir1, repo_dir2, src_file, file1, file2):
    cmd = 'timeout 5m mvn exec:java -q -e -f ' + pompath + ' -Dexec.mainClass="genesis.rewrite.RewritePassManager" -Dexec.args="';
    cmd += repo_dir1 + " ";
    cmd += repo_dir2 + " ";
    cmd += repo_dir1 + "/" + src_file + " ";
    cmd += repo_dir2 + "/" + src_file + " "+ file1 + " " + file2 + '"';
    print("Executing cmd: " + cmd)
    ret = system(cmd);
    if (ret != 0):
        return 2;
    elif (path.exists(file1)):
        return 1;
    else:
        return 0;

main()
