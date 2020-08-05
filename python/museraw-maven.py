#!/usr/bin/env python
import os
from os import system, chdir, getcwd
from sys import argv, exit
import json
import getopt

def check_pom(corpus_path, path):
    system("rm -rf __tmp");
    system("mkdir __tmp");
    system("cp -rf " + corpus_path + "/" + path + " __tmp/tmp.tgz");
    system("cd __tmp && tar xzf tmp.tgz && chmod -R 0755 *");
    found = False;
    for root, dirs, files in os.walk("__tmp"):
        for fname in files:
            if fname == "pom.xml":
                found = True;
                break;
        if found:
            break;
    return found;

def check_compile(url, user, passwd):
    system("rm -rf __tmp");
    system("mkdir __tmp");
    ori_dir = getcwd();
    if user == "":
        system("git clone " + url + " __tmp/src");
    else:
        new_url = url[0:8] + github_user + ":" + github_passwd + "@" + url[8:];
        system("git clone " + new_url + " __tmp/src");
    if (not os.path.isdir("__tmp/src")):
        # something wrong happened, we just quit
        return False;
    chdir("__tmp/src");
    ret = system("timeout -k 15m 10m mvn compile");
    chdir(ori_dir);
    return ret == 0;

if (len(argv) < 3):
    exit(1);
(opts, args) = getopt.getopt(argv[1:], "", ["github-user=", "github-passwd=", "corpus-path=", "paracount=", "paraid="]);
github_user = "";
github_passwd = "";
paracount = 1;
paraid = 0;
corpus_path = "/home/fanl/Workspace/muse/corpus";
for (o, a) in opts:
    if (o == "--github-user"):
        github_user = a;
    if (o == "--github-passwd"):
        github_passwd = a;
    if (o == "--corpus-path"):
        corpus_path = a;
    if (o == "--paracount"):
        paracount = int(a);
    if (o == "--paraid"):
        paraid = int(a);

with open(args[0]) as data_file:
    data = json.load(data_file);

fout = open(args[1], "w");
cnt = 0;
for proj in data["results"]:
    name = proj["full_name"];
    url = proj["html_url"];
    path = proj["path"];
    cnt = cnt + 1;
    if (paracount > 1):
        if (cnt % paracount != paraid):
            continue;
    print "Processing: ", name, url, path;
    if (not check_pom(corpus_path, path)):
        print "Cannot find pom.xml!";
        continue;
    print "Found pom.xml!";
    if (not check_compile(url, github_user, github_passwd)):
        print "Cannot compile!";
        continue;
    print "Compile succ!";
    print >> fout, name, url, path;
    fout.flush();
fout.close();
system("rm -rf __tmp");
