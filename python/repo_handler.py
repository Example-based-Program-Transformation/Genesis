from os import system, getcwd, chdir
import subprocess

class svn_handler:
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir;

    def get_parent_rev(self, rev):
        return str(int(rev) - 1);

    def get_revs(self, fix_only, year_limit):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        p = subprocess.Popen(["svn", "log"], stdout = subprocess.PIPE);
        chdir(ori_dir);
        (out, err) = p.communicate();
        lines = out.split("\n");
        last_sep = False;
        comment = "";
        rev = "";
        revs = [];
        for line in lines:
            tokens = line.strip().split();
            if last_sep:
                if (len(tokens) < 1) or (tokens[0][0] != "r"):
                    last_sep = False;
                    continue;
                rev = tokens[0][1:];
                date_str = tokens[4];
                date_tokens = date_str.split("-");
                date = date_tokens[0];
                if (int(date) < year_limit):
                    break;
                comment = "";
            else:
                comment += line + "\n";
            if (len(tokens) == 1) and (tokens[0].startswith("-----------")) and (tokens[0].find("+") == -1) and (len(tokens[0]) > 20):
                if (rev != ""):
                    found = False;
                    if (fix_only):
                        words = comment.strip().split();
                        for word in words:
                            if word.lower() == "fix" or word.lower() == "fixed" or word.lower() == "bug" or word.lower() == "issue" or word.lower() == "issues":
                                found = True;
                                break;
                    if not fix_only or found:
                        revs.append((rev, self.get_parent_rev(rev), comment));
                last_sep = True;
            else:
                last_sep = False;
        return revs;

    def get_diff_for_java(self, rev1, rev2):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        p = subprocess.Popen(["svn", "diff", "-r", rev1 + ":" + rev2], stdout=subprocess.PIPE);
        chdir(ori_dir);
        (out, err) = p.communicate();
        lines = out.split("\n");
        src_file = "";
        res = {};
        line_cnt = 0;
        for line in lines:
            tokens = line.strip().split();
            if (len(tokens) == 2) and (tokens[0] == "Index:"):
                line_cnt = 0;
                if (tokens[1].endswith(".java") or tokens[1].endswith(".Java")):
                    src_file = tokens[1];
                    res[src_file] = [0, []];
                else:
                    src_file = "";
            else:
                line_cnt += 1;
            if (line_cnt > 3) and (src_file != ""):
                res[src_file][1].append(line);
                if (len(tokens) > 1):
                    if (tokens[0] == "+") or (tokens[0] == "-"):
                        res[src_file][0] += 1;
        return res;

    def switch_to_rev(self, rev):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        system("svn update -r " + rev + " --force --accept theirs-full --non-interactive");
        chdir(ori_dir);

class hg_handler:
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir;

    def get_parent_rev(self, rev):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        p = subprocess.Popen(["hg", "log", "-r", rev], stdout = subprocess.PIPE);
        chdir(ori_dir);
        (out, err) = p.communicate();
        lines = out.split("\n");
        for line in lines:
            tokens = line.strip().split();
            if (len(tokens) == 0):
                continue;
            if (tokens[0] == "parent:"):
                tmp = tokens[1].split(":");
                return tmp[0];
        return str(int(rev) - 1);

    def get_revs(self, fix_only, year_limit):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        p = subprocess.Popen(["hg", "log", "--date", str(year_limit) + "-01-01 to 2016-01-01"], stdout = subprocess.PIPE);
        chdir(ori_dir);
        (out, err) = p.communicate();
        lines = out.split("\n");
        rev = "";
        parent = "";
        comment = "";
        revs = [];
        for line in lines:
            tokens = line.strip().split();
            if (len(tokens) == 0):
                continue;
            if (tokens[0] == "changeset:"):
                if (parent != "merged!") and (rev != ""):
                    if (parent == ""):
                        parent = str(int(rev) - 1);
                    found = False;
                    if (fix_only):
                        words = comment.strip().split();
                        for word in words:
                            if word.lower() == "fix" or word.lower() == "fixed" or word.lower() == "bug" or word.lower() == "issue" or word.lower() == "issues":
                                found = True;
                                break;
                    if not fix_only or found:
                        revs.append((rev, parent, comment));
                words = tokens[1].split(":");
                rev = words[0];
                parent = "";
                comment = "";
            elif (tokens[0] == "parent:"):
                if (parent == ""):
                    words = tokens[1].split(":");
                    parent = words[0];
                else:
                    parent = "merged!";
            elif tokens[0] == "summary:":
                comment = " ".join(tokens[1:]);
        return revs;

    def get_diff_for_java(self, rev1, rev2):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        p = subprocess.Popen(["hg", "diff", "-r", rev1, "-r", rev2], stdout=subprocess.PIPE);
        chdir(ori_dir);
        (out, err) = p.communicate();
        lines = out.split("\n");
        src_file = "";
        res = {};
        for line in lines:
            tokens = line.strip().split();
            if (len(tokens) > 5) and (tokens[0] == "diff") and (tokens[1] == "-r") and (tokens[3] == "-r"):
                if (tokens[5].endswith(".java")) or \
                        (tokens[5].endswith(".Java")):
                    src_file = tokens[5];
                else:
                    src_file = "";
            elif src_file != "":
                if not (src_file in res):
                    res[src_file] = [0, []];
                res[src_file][1].append(line);
                if (len(tokens) > 1):
                    if (tokens[0] == "+") or (tokens[0] == "-"):
                        res[src_file][0] += 1;
        return res;

    def switch_to_rev(self, rev):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        system("hg update -r " + rev + " -C");
        chdir(ori_dir);

class git_handler:
    def __init__(self, repo_dir):
        self.repo_dir = repo_dir;

    def get_parent_rev(self, rev):
        return rev + "^1";

    def get_commit_log(self, rev):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        p = subprocess.Popen(["git", "show", rev], stdout=subprocess.PIPE);
        chdir(ori_dir);
        (out, err) = p.communicate();
        lines = out.split("\n");
        ret = [];
        for line in lines:
            if line[0:5] == "diff ":
                break;
            ret.append(line);
        return ret;

    def get_revs(self, fix_only, year_limit):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        subprocess.call(["git", "checkout", "master", "-f"]);
        p = subprocess.Popen(["git", "log"], stdout=subprocess.PIPE);
        chdir(ori_dir);
        (out, err) = p.communicate();
        lines = out.split("\n");
        # parse git log to get bug-fix revision and previous revision
        cur_revision = "";
        last_fix_revision = "";
        comment = "";
        last_is_author = False;
        ret = [];
        cnt = 0;
        for line in lines:
            tokens = line.strip("\n").strip(" ").split();
            if len(tokens) == 0:
                continue;
            if (len(tokens) == 2) and (tokens[0] == "commit") and (len(tokens[1]) > 10):
                cur_revision = tokens[1];
                if last_fix_revision != "":
                    chdir(self.repo_dir);
                    p = subprocess.Popen(["git", "rev-list", "--parents", "-n", "1", last_fix_revision], stdout=subprocess.PIPE);
                    chdir(ori_dir);
                    (out, err) = p.communicate();
                    tokens2 = out.split();
                    if len(tokens2) == 2:
                        chdir(self.repo_dir);
                        p = subprocess.Popen(["git", "diff", "--name-only", last_fix_revision, last_fix_revision+"^1"], stdout=subprocess.PIPE);
                        chdir(ori_dir);
                        (out,err) = p.communicate();
                        out_lines = out.split("\n");
                        for out_line in out_lines:
                            name_str = out_line.strip();
                            idx = name_str.rfind(".");
                            extension = name_str[idx+1:];
                            if (extension == "java") or (extension == "Java"):
                                ret.append((last_fix_revision, tokens2[1], comment));
                                cnt += 1;
                                print "found fix revision ", cnt, ": ", last_fix_revision;
                                break;
                last_fix_revision = "";
                comment = "";
            elif (tokens[0] == "Date:") and last_is_author:
                year = int(tokens[5]);
                if (year < year_limit):
                    break;
            elif (tokens[0] != "Author:" and tokens[0] != "Merge:"):
                comment = comment + "\n" + line;
                if fix_only:
                    is_fix = False;
                    for token in tokens:
                        if (token.lower() == "fixed") or (token.lower() == "bug") or (token.lower() == "fix"):
                            is_fix = True;
                            break;
                if (not fix_only) or is_fix:
                    last_fix_revision = cur_revision;
            if tokens[0] == "Author:":
                last_is_author = True;
            else:
                last_is_author = False;
        return ret;

    def get_diff_for_java(self, rev1, rev2, non_java = False):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        p = subprocess.Popen(["git", "diff", rev1, rev2], stdout=subprocess.PIPE);
        chdir(ori_dir);
        (out, err) = p.communicate();
        lines = out.split("\n");
        src_file = "";
        res = {};
        for line in lines:
            tokens = line.strip().split();
            if (len(tokens) >= 4) and (tokens[0] == "diff") and (tokens[1] == "--git"):
                if (tokens[2].endswith(".java") and tokens[3].endswith(".java")) or \
                        (tokens[2].endswith(".Java") and tokens[3].endswith(".Java")) or non_java:
                    src_file = tokens[3][2:];
                else:
                    src_file = "";
            elif src_file != "":
                if not (src_file in res):
                    res[src_file] = [0, []];
                res[src_file][1].append(line);
                if (len(tokens) > 1):
                    if (tokens[0] == "+") or (tokens[0] == "-"):
                        res[src_file][0] += 1;
        return res;

    def switch_to_rev(self, rev):
        ori_dir = getcwd();
        chdir(self.repo_dir);
        system("git checkout -f " + rev);
        system("git clean -f -d");
        chdir(ori_dir);

def create_repo_handler(repo_dir, repo_type):
    if (repo_type == "git"):
        return git_handler(repo_dir);
    elif (repo_type == "hg"):
        return hg_handler(repo_dir);
    elif (repo_type == "svn"):
        return svn_handler(repo_dir);
    else:
        print "Cannot handle the repository type: ", repo_type;
        assert(0);

def prepare_repodir(existing_repo, repo_type, pre_rev, post_rev, pre_repodir, post_repodir):
    repo = create_repo_handler(existing_repo, repo_type);
    diff_res = repo.get_diff_for_java(pre_rev, post_rev, True);
    # we are going to copy test file from post repo
    testf = set();
    for srcf in diff_res.keys():
        if (srcf.find("test") != -1) or (srcf.find("Test") != -1):
            testf.add(srcf);
    repo.switch_to_rev(pre_rev);
    if (pre_repodir != ""):
        system("cp -rf " + existing_repo + " " + pre_repodir);
    repo.switch_to_rev(post_rev);
    if (post_repodir != ""):
        system("cp -rf " + existing_repo + " " + post_repodir);
    if (pre_repodir != ""):
        for fname in testf:
            srcpath = existing_repo + "/" + fname;
            destpath = pre_repodir + "/" + fname;
            ret = system("cp -rf " + srcpath + " " + destpath);
            if ret != 0:
                return False;
    return True;

def prepare_casedir(patchid, prerev, postrev, url, testcases, outdir, github_user, github_passwd):
    system("rm -rf __tmp_0");
    if github_user == "":
        system("git clone " + url + " __tmp_0");
    else:
        new_url = url[0:8] + github_user + ":" + github_passwd + "@" + url[8:];
        system("git clone " + new_url + " __tmp_0");
    src_dir = outdir + "/src_orig";
    system("rm -rf " + outdir);
    system("mkdir " + outdir);
    prepare_repodir("__tmp_0", "git", prerev, postrev, src_dir, "");
    testcase_file = outdir + "/testcase.txt";
    f = open(testcase_file, "w");
    print len(testcases);
    for row2 in testcases:
        print >> f, row2[0], row2[1], row2[2];
    f.close();
    conf_file = outdir + "/case.conf";
    f = open(conf_file, "w");
    print >> f, "src=src_orig";
    print >> f, "testcase=testcase.txt";
    f.close();
    system("rm -rf __tmp_0");
