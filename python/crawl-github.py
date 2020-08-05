#!/usr/bin/env python
from urllib2 import urlopen
from bs4 import BeautifulSoup
from sys import argv
from os import system
import random
import time

def fetchProjectList(lang, size, page):
    ret = []
    url_str = "https://github.com/search?o=desc&p=" + str(page) + "&q=language%3A"+ lang + \
        "++size%3A>" + str(size) + "+NOT+android+in%3Aname%2Cdescription" + \
        "&ref=searchresults&s=stars&type=Repositories";
    print url_str;
    soup = BeautifulSoup(urlopen(url_str), 'lxml');

    # The hacky pattern is that the user_name/project_name will appear three
    # times in a row, and the last time starts with "/". It might be invalid
    # if github updates its webpage layout
    lastlink1 = ""
    lastlink2 = ""
    for link in soup.find_all('a'):
        linkstr = link.get('href');
        if len(linkstr) < 2:
            continue;
        if (len(lastlink1) >= len(linkstr)) and \
           (len(lastlink2) >= len(linkstr)):
            if linkstr[0] == "/":
                if lastlink1[0:len(linkstr)-1] == linkstr[1:len(linkstr)]:
                    if lastlink2[0:len(linkstr)-1] == linkstr[1:len(linkstr)]:
                        if linkstr != "/":
                            ret.append(linkstr)
        lastlink2 = lastlink1
        lastlink1 = linkstr
    return ret

assert( len(argv) > 1);
outdir = argv[1];
system("rm -rf " + outdir);
system("mkdir " + outdir);
random.seed(53);
for i in range(1, 101):
    print "Fetching page " + str(i);
    l = fetchProjectList("Java", "1000", i);
    print l;
    f = open(outdir + "/p" + str(i) + ".txt", "w");
    for addr in l:
        print >> f, addr;
    f.close();
    time.sleep(random.uniform(30, 50));
