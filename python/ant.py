#!/usr/bin/env python
from os import system, chdir, getcwd
from sys import argv, exit
import getopt
import subprocess

def parseArgout(out, argout):
    lines = out.split('\n');
    look_next = False;
    fout = open(argout, "w");
    cur_args = [];
    for line in lines:
        tokens = line.strip().split();
        if look_next:
            if len(tokens) > 1 and tokens[1][0] == "'":
                cur_args.append(tokens[1][1:len(tokens[1]) - 1]);
            else:
                print >> fout, " ".join(cur_args);
                look_next = False;
        if len(tokens) > 2:
            if tokens[0] == "[javac]" and tokens[1] == "Compilation" and tokens[2] == "arguments:":
                look_next = True;
                cur_args = [];
    fout.close();

if __name__ == "__main__":
    opts, args = getopt.getopt(argv[1:], "", ["compile", "clean", "getargs="]);
    if len(args) < 1:
        print "need to specify the target directory!";
        exit(-1);
    toCompile = False;
    toClean = False;
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

    srcdir = args[0];
    chdir(srcdir);
    ret = 0;
    if toClean:
        ret = system("ant clean");
        if ret != 0:
            chdir(oridir);
            exit(ret);

    if toCompile:
        execargs = ["ant", "compile"];
        if argout != "":
            execargs = ["ant", "-v", "compile"];
        p = subprocess.Popen(execargs, stdout = subprocess.PIPE);
        out, err = p.communicate();
        ret = p.returncode;
        print out;
        if argout != "":
            parseArgout(out, argout);

    chdir(oridir);
    exit(ret);
