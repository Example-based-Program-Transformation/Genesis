#!/usr/bin/env python
from sys import argv
import math

f = open(argv[1], "r");
lines = f.readlines();
res = dict();
node = set();
f.close();
for line in lines:
    tokens = line.strip().split();
    if (len(tokens) >= 5):
        a = int(tokens[0]);
        b = int(tokens[1]);
        cost = int(tokens[4]);
        # cost2 = int(tokens[5]);
        if (math.log(cost) < 2):
            res[(a, b)] = math.log(cost);
            node.add(a);
            node.add(b);

print "graph rel {";
for a, b in res.keys():
    print "v" + str(a) + " -- v" + str(b) + "[label=\"" + "{0:.{1}f}".format(res[(a,b)], 2) + "\"]";
print "}";
print "// node total " + str(len(node));
