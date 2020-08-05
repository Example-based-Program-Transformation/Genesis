#!/usr/bin/env python
from os import system, chdir, getcwd
from sys import argv, exit
import maven_testinfo
import getopt
import subprocess

def parseArgout(out, argout):
    lines = out.split('\n');
    newsig = "[DEBUG] Command line options:";
    newversion = False;
    for line in lines:
        if (line.find(newsig) != -1):
            newversion = True;
            break;
    if not newversion:
        sflag = 0;
        fout = open(argout, "w");
        sourcestr = "";
        classstr = "";
        for line in lines:
            tokens = line.strip().split();
            if len(tokens) > 2 and tokens[0] == "[DEBUG]" and tokens[1] == "Source" and tokens[2] == "roots:":
                sflag = 1;
            elif len(tokens) > 1 and tokens[0] == "[DEBUG]" and tokens[1] == "Classpath:":
                sflag = 2;
            elif sflag != 0 and len(tokens) > 1 and tokens[0] == "[DEBUG]":
                if sflag == 1:
                    if sourcestr == "":
                        sourcestr = tokens[1];
                    else:
                        sourcestr = sourcestr + ":" + tokens[1];
                elif sflag == 2:
                    if classstr == "":
                        classstr = tokens[1];
                    else:
                        classstr = classstr + ":" + tokens[1];
            else:
                sflag = 0;
                if sourcestr != "":
                    print >> fout, " -sourcepath " + sourcestr + " -classpath " + classstr;
                    sourcestr = "";
                    classstr = "";
        if sourcestr != "":
            print >> fout, " -sourcepath " + sourcestr + " -classpath " + classstr;
        fout.close();
    else:
        look_next = False;
        fout = open(argout, "w");
        for line in lines:
            tokens = line.strip().split();
            if look_next:
                print >> fout, " ".join(tokens[1:]);
                look_next = False;
            if len(tokens) > 2:
                if tokens[0] == "[DEBUG]" and tokens[1] == "Command" and tokens[2] == "line" and tokens[3] == "options:":
                    look_next = True;
        fout.close();

if __name__ == "__main__":
    opts, args = getopt.getopt(argv[1:], "", ["compile", "clean", "testinfo=", "getargs="]);
    if len(args) < 1:
        print "need to specify the target directory!";
        exit(-1);
    toCompile = False;
    toClean = False;
    testinfo = "";
    argout = "";
    oridir = getcwd();
    for o, a in opts:
        if o == "--compile":
            toCompile = True;
        if o == "--clean":
            toClean = True;
        if o == "--getargs":
            if (a[0] != "/"):
                argout = oridir + "/" + a;
            else:
                argout = a;
            toClean = True;
            toCompile = True;
        if o == "--testinfo":
            if (a[0] != "/"):
                testinfo = oridir + "/" + a;
            else:
                testinfo = a;

    srcdir = args[0];
    chdir(srcdir);
    ret = 0;
    if toClean:
        ret = system("mvn clean");
        if ret != 0:
            chdir(oridir);
            exit(ret);

    if toCompile:
        execargs = ["mvn", "compile"];
        if argout != "":
            execargs = ["mvn", "-X", "compile"];
        p = subprocess.Popen(execargs, stdout = subprocess.PIPE, stderr = subprocess.PIPE);
        out, err = p.communicate();
        ret = p.returncode;
        print out;
        if argout != "":
            parseArgout(out, argout);
    chdir(oridir);

    if testinfo != "":
        info = maven_testinfo.maven_testinfo(args[0]);
        f = open(testinfo, "w");
        info.writeto(f);
        f.close();

    exit(ret);
