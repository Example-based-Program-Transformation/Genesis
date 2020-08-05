#!/usr/bin/env python
import gurobipy
from sys import argv
import getopt

def parseCoverFile(coverf):
    f = open(coverf);
    lines = f.readlines();
    f.close();
    i = 0;
    ret = [];
    while (i < len(lines)):
        assert( i + 2 < len(lines) );
        tokens = lines[i+2].strip().split();
        tmp = set();
        for token in tokens:
            tmp.add(int(token));
        ret.append(tmp);
        i += 3;
    return ret;

def parseCostFile(costf):
    f = open(costf);
    lines = f.readlines();
    f.close();
    tokens = lines[0].strip().split();
    n = int(tokens[0]);
    n1 = int(tokens[1]);
    n2 = int(tokens[2]);
    m = int(tokens[3]);
    ret = [];
    for line in lines[1:]:
        tmp = [];
        tokens = line.strip().split();
        for token in tokens:
            tmp.append(int(token));
        ret.append(tmp);
    return (n, n1, n2, m, ret);

assert( len(argv) > 3 );
(opts, args) = getopt.getopt(argv[1:], "", ["a=", "b=", "c=", "formula=", "enforce=", "validation-only"]);
a = 100000000;
b = 50000;
c = 10;
formula = 0;
enforce = -1;
valid_only = False;

for o, arg in opts:
    if (o == "--a"):
        a = int(arg);
    if (o == "--b"):
        b = int(arg);
    if (o == "--c"):
        c = int(arg);
    if (o == "--formula"):
        formula = int(arg);
    if (o == "--validation-only"):
        valid_only = True;
    if (o == "--enforce"):
        enforce = int(arg);

coverf = args[0];
costf = args[1];
outf = args[2];
print "Initialization!"
(n, n1, n2, m, cost) = parseCostFile(costf);
print "Parsed cost file!"
cover = parseCoverFile(coverf);
print "Parsed cover file: tot ", len(cover);
M = gurobipy.Model("genesis");
print "n = ", n, "n1 = ", n1, "n2 = ", n2, "m = ", m;

x = {};
y = {};
s = 0;
if (valid_only):
    s = n1;
for i in range(s, n2):
    x[i] = M.addVar(vtype=gurobipy.GRB.BINARY, name="x" + str(i));
for i in range(0, m):
    y[i] = M.addVar(vtype=gurobipy.GRB.BINARY, name="y" + str(i));

print "Variable setup!"

M.update();

obj = 0;
for i in range(s, n2):
    if (i < n1):
        obj = obj + x[i];
    else:
        obj = obj + c * x[i];
if (formula == 1):
    obj = obj * a;
    for i in range(0, m):
        obj = obj - y[i];
elif (formula == 2):
    obj = obj * a;
    for i in range(n1, n2):
        for j in range(0, m):
            obj = obj - cost[i][j] * y[j];
M.setObjective(obj, gurobipy.GRB.MAXIMIZE);

for i in range(s, n2):
    coverCons = 0;
    for j in range(0, m):
        if i in cover[j]:
            coverCons = coverCons + y[j];
    M.addConstr(coverCons >= x[i]);
    sizeCons = 0;
    for j in range(0, m):
        sizeCons = sizeCons + cost[i][j] * y[j];
    M.addConstr(sizeCons <= a - (a-b) * x[i]);

if enforce != -1:
    M.addConstr(y[enforce] >= 1);

print "Constraint setup!";

M.optimize();

covered = set();
selected = set();

for v in M.getVars():
    print v.varName, v.x;
    if abs(v.x) > 0.1:
        idx = int(v.varName[1:]);
        if (v.varName[0] == 'x'):
            covered.add(idx);
        else:
            selected.add(idx);
print "MIP Result: ", M.objVal;

f = open(outf, "w");
print >> f, len(selected),

# I want to order the set with coverage/cost
sel = [];
for idx in selected:
    pat_cov = len(cover[idx]);
    pat_cost = 0;
    for i in range(s, n2):
        pat_cost += cost[i][idx];
    print pat_cost, pat_cov, idx;
    sel.append((float(pat_cost)/pat_cov, idx));

for fcost, idx in sorted(sel):
    print fcost, idx;
    print >> f, idx,

print >> f;
print >> f, covered;
test_cnt = 0;
for i in range(s, n):
    print >> f, i,
    tmp1 = set();
    tmp2 = {};
    tot = 0;
    for j in range(0, m):
        if j in selected:
            if i in cover[j]:
                tmp1.add(j);
            tmp2[j] = cost[i][j];
            tot += tmp2[j];
    if i < n2:
        if i in covered:
            print >> f, "Y",
        else:
            print >> f, "N",
    else:
        if (tot <= b) and (len(tmp1) > 0):
            print >> f, "Y",
        else:
            print >> f, "N",
    print >> f, tot, tmp1, tmp2;
    if (i >= n2) and (tot <= b) and (len(tmp1) > 0):
        test_cnt += 1;
f.close();
print "Test cover: ", test_cnt;

# This is collect useful statistics
training_sample = 0;
validation_sample = 0;
testing_sample = 0;
training_space = 0;
validation_space = 0;
testing_space = 0;
cover_sample = set();
cover_space = set();
for i in range(0, m):
    cover_sample |= set(cover[i]);
    if i in selected:
        cover_space |= set(cover[i]);
for i in range(0, n1):
    if i in cover_sample:
        training_sample += 1;
    if i in cover_space:
        training_space += 1;
for i in range(n1, n2):
    if i in cover_sample:
        validation_sample += 1;
    if i in cover_space:
        validation_space += 1;
for i in range(n2, n):
    if i in cover_sample:
        testing_sample += 1;
    if i in cover_space:
        testing_space += 1;
print "Training sample cover: ", training_sample;
print "Validation smaple cover: ", validation_sample;
print "Testing sample cover: ", testing_sample;
print "Training space cover: ", training_space;
print "Validation space cover: ", validation_space;
print "Testing space cover: ", testing_space;
