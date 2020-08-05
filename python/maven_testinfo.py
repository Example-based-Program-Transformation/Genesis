from os import getcwd, chdir
import os
import xml.etree.ElementTree as ET
import subprocess

class maven_testinfo:
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir;
        ori_dir = getcwd();
        chdir(repo_dir);
        p = subprocess.Popen(["timeout", "-k", "30m", "25m", "mvn", "-fn", "-X", "test"], stdout = subprocess.PIPE);
        chdir(ori_dir);
        (out, err) = p.communicate();
        if p.returncode == 124 or p.returncode == 137:
            # This test simply timeout, we are not going to parse the partial results, and we just skip
            self.malform = True;
            return;
        lines = out.split("\n");
        self.num_module = 0;
        self.base_dir = [];
        self.report_dir = [];
        self.class_dir = [];
        self.testclass_dir = [];
        self.testclass = [];
        self.classpath = [];
        self.source_dir = [];
        self.malform = False;
        intest = False;
        incp = False;
        bdir = "";
        cdir = "";
        tcdir = "";
        rdir = "";
        sdir = ""
        cpath = [];
        tclass = None;
        for line in lines:
            tokens = line.strip().split();
            if (len(tokens) == 0):
                continue;
            if (len(tokens) > 3) and (tokens[0] == "[INFO]") and (tokens[1] == "---") and (tokens[2].find("maven-surefire-plugin") == 0):
                if tclass != None:
                    self.testclass.append(tclass);
                tclass = None;
                intest = True;
                bdir = "";
                cdir = "";
                rdir = "";
                tcdir = "";
                sdir = ""
                cpath = [];
            elif intest and (len(tokens) >= 5) and (tokens[0] == 'T') and (tokens[1] == 'E') and (tokens[2] == 'S') and (tokens[3] == 'T') and (tokens[4] == 'S'):
                intest = False;
                if (not (bdir != "" and cdir != "" and tcdir != "" and len(cpath) != 0)):
                    print bdir;
                    print cdir;
                    print tcdir;
                    print cpath;
                    print "Strange mvn test result for parsing!"
                    self.malform = True;
                    return;
                self.base_dir.append(bdir);
                self.class_dir.append(cdir);
                self.testclass_dir.append(tcdir);
                self.classpath.append(cpath);
                self.report_dir.append(rdir);
                self.source_dir.append(sdir)
                self.num_module += 1;
                tclass = [];
            elif intest and (len(tokens) > 4) and ((tokens[0] == "[INFO]") or (tokens[0] == "[DEBUG]")) and (tokens[1] == "Surefire") and (tokens[2] == "report") and (tokens[3] == "directory:"):
                rdir = tokens[4];
            elif intest and (len(tokens) > 4) and (tokens[0] == "[DEBUG]") and (tokens[2] == "basedir"):
                bdir = tokens[4];
            elif intest and (len(tokens) > 4) and (tokens[0] == "[DEBUG]") and (tokens[2] == "classesDirectory"):
                cdir = tokens[4];
            elif intest and (len(tokens) > 4) and (tokens[0] == "[DEBUG]") and (tokens[2] == "testClassesDirectory"):
                tcdir = tokens[4];
            elif intest and (tokens[0] == "[DEBUG]") and \
                ((len(tokens) > 3) and (tokens[1] == "test") and (tokens[2] == "classpath") and (tokens[3] == "classpath:") or\
                 (len(tokens) > 3) and (tokens[1] == "Test") and (tokens[2] == "Classpath") and (tokens[3] == ":") or \
                 (len(tokens) > 2) and (tokens[1] == "test") and (tokens[2] == "classpath:")):
                incp = True;
                for token in tokens[3:]:
                    if token[0] == '/':
                        cpath.append(token);
            elif intest and incp:
                if (len(tokens) == 2) and (tokens[0] == "[DEBUG]") and (tokens[1] != "provider"):
                    for token in tokens[1:]:
                        if token[0] == '/':
                            cpath.append(token);
                else:
                    incp = False;
            elif (len(tokens) == 2) and (tokens[0] == "Running"):
                tclass.append(tokens[1]);
            elif intest and (len(tokens) > 4) and (tokens[0] == "[DEBUG]") and (tokens[2] == "testSourceDirectory"):
                sdir = tokens[4]
        if tclass != None:
            self.testclass.append(tclass);
        self.testcase = [];
        for i in range(0, self.num_module):
            modulecases = [];
            if (i >= len(self.testclass)):
                self.malform = True;
                return;
            for j in range(0, len(self.testclass[i])):
                fname = self.report_dir[i] + "/TEST-" + self.testclass[i][j] + ".xml";
                if (not os.path.exists(fname)):
                    self.malform = True;
                    return;
                # print "Processing: " + fname;
                xmlroot = ET.parse(fname);
                testcases = [];
                for testcase in xmlroot.findall("testcase"):
                    if (testcase.find("skip") != None):
                        continue;
                    class_name = testcase.get("classname");
                    method_name = testcase.get("name");
                    case_time = float(testcase.get("time").replace(",", ""));
                    failure = testcase.find("failure");
                    error = testcase.find("error");
                    if (failure == None and error == None):
                        testcases.append((class_name, method_name, case_time, 0));
                    else:
                        testcases.append((class_name, method_name, case_time, 1));
                modulecases.append(testcases);
            self.testcase.append(modulecases);

    def _get_cases(self, status):
        ret = set();
        for i in range(0, self.num_module):
            for j in range(0, len(self.testcase[i])):
                for testcase in self.testcase[i][j]:
                    if testcase[3] == status:
                        ret.add((testcase[0], testcase[1]));
        return ret;

    def passed_cases(self):
        return self._get_cases(0);

    def fail_cases(self):
        return self._get_cases(1);

    def writeto(self, fout):
        print >>fout, self.num_module;
        for i in range(0, self.num_module):
            print >>fout, self.base_dir[i];
            print >>fout, self.report_dir[i];
            print >>fout, self.class_dir[i];
            print >>fout, self.testclass_dir[i];
            print >>fout, ":".join(self.classpath[i]);
            print >>fout, self.source_dir[i]
            print >>fout, len(self.testclass[i]),
            for tclass in self.testclass[i]:
                print >>fout, tclass,
            print >>fout;
            assert(len(self.testclass[i]) == len(self.testcase[i]));
            for testcases in self.testcase[i]:
                print >>fout, len(testcases);
                for case in testcases:
                    print >>fout, case[0], case[1], case[3];
