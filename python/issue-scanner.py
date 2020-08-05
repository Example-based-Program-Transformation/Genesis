#!/usr/bin/env python
import json
import requests
from sys import argv, stdout
import getopt

def to_gitrev(token):
    if len(token) < 10:
        return "";
    for c in token[0:10]:
        if not ((c >= '0' and c <= '9') or (c>='a') and (c<='f')):
            return "";
    j = len(token) - 1;
    while not ((token[j] >= '0' and token[j] <= '9') or (token[j] >= 'a') and (token[j] <= 'f')):
        j -= 1;
    return token[0:j + 1];

(opts, args) = getopt.getopt(argv[1:], "u:o:", []);
target_token = "classcast";
user = "";
passwd = "";
outf = "";
for o, a in opts:
    if (o == "-u"):
        idx = a.find(":");
        user = a[0:idx];
        passwd = a[idx+1:];
    if (o == "-o"):
        outf = a;

repos = [];
for fname in args:
    f = open(fname, "r");
    lines = f.readlines();
    for line in lines:
        tokens = line.strip().split();
        repos.append(tokens[0]);


issue_list = [];
for repo in repos:
    if (repo[0] == "/"):
        repo = repo[1:];
    base_url = "https://api.github.com/repos/" + repo;
    if base_url[len(base_url) - 1] != "/":
        base_url += "/";
    url = base_url + "issues?state=closed&per_page=100&page=4";
    if user == "":
        r = requests.get(url);
    else:
        r = requests.get(url, auth = (user, passwd) );

    if (r.status_code == 403):
        print r.text;
        print "We got cut down by Github!"
        break;
    cnt = 0;
    print r.text;
    for issue in r.json():
        cnt += 1;
        a = issue["title"];
        b = issue["body"];
        print issue["number"];
        if b == None:
            b = "";
        if (a.lower().find(target_token) != -1 or b.lower().find(target_token) != -1):
            # print "Title:" + issue["title"];
            # print "Body:" + issue["body"];
            # print "Number:" + str(issue["number"]);
            issue_list.append((repo, issue["number"], issue["url"]));
    print "Total issue checked: ", cnt;

    #for repo, number, _, _ in issue_list:
        #url = base_url + "issues/" + str(number) + "/comments";
        # print url;
        #if (user == ""):
        #    r = requests.get(url);
        #else:
        #    r = requests.get(url, auth=(user, passwd));
        #for comment in r.json():
        #    print comment;
        #    tokens = comment["body"].strip().split();
        #    for token in tokens:
        #        rev = str(to_gitrev(token));
        #        if (rev != ""):
        #            commit_list.append((repo, rev, number));

print issue_list;
if outf == "":
    fout = stdout;
else:
    fout = open(outf, "w");
for repo, number, url in issue_list:
    print >>fout, repo, number, url;
if outf != "":
    fout.close();
