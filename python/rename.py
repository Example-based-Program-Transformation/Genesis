#!/usr/bin/env python
import os
from os import system
from sys import argv

cidx = 1;
if (len(argv) > 2):
    if (argv[2] == "2"):
        cidx = 2;

for root, dirs, files in os.walk(argv[1]):
    for d in dirs:
        if (d.find("__") != 0):
            continue;
        system("mv " + root + "/" + d + " " + root + "/" + d[cidx:]);
