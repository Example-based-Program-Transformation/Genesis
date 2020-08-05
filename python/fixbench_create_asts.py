"""
Read the pair.info files of the specified bug category.
Extract repo info, required commits, and other data
Then Git clones the repo, checkouts the before and after versions.
Constructs the AST.

Let's do everything through bash lol.

This creates a .sql file, which should be inserted to the db
e.g. mysql -u root -pgenesis < insert_from_bowen_create_ast.sql
"""

import os
import sys
import subprocess
import logging

path_to_ptbench = "/home/root/Workspace/PTBench-Data/SampleData"
# path_to_ptbench = "/home/root/Workspace"

bench_data = {}
uniq_repos = set()


# rm -rf ../github/data/*
# python3 python/fixbench_create_asts.py NULL_DER &> log.log
# mysql -u root -p < insert_from_bowen_create_ast.sql

# Then either
# 1.
# rm cost.txt
# rm cover.txt
# rm /tmp/*round*
#
# then run the following, but changing "54" to the length of the training examples.
# MAVEN_OPTS="-Xms256m -Xmx40g" mvn exec:java -Dexec.mainClass="genesis.learning.Main" -Dexec.args="1 /home/root/Workspace/github/data 54 54 54 1" &> training.log

# 2.
# look at the run_training.sh script, if present
# e.g. sh run_training.sh Genesis-OOB 167 130 167 &> training-oob.log

for root, dirs, files in os.walk(path_to_ptbench):
    for file in files:
        if not file.endswith(".info"):
            continue
        if sys.argv[1] not in root:
            continue

        lines = []
        with open(os.path.join(root, file)) as opened:
            for line in opened:
                lines.append(line.rstrip())

        id = None
        filepath = None
        fixed_commit = None
        buggy_commit = None
        repo_url = "https://www.github.com/"
        repo = None

        # first type of schema
        for line in lines:
            if line.startswith("Id"):
                id = line.split("Id:")[1]
            elif line.startswith("modifiedFPath"):
                filepath = line.split("modifiedFPath:")[1]
            elif line.startswith("FixedFilePath"):
                filepath = line.split("FixedFilePath:")[1]
            elif line.startswith("BuggyFilePath"):
                filepath = line.split("BuggyFilePath:")[1]
            elif line.startswith("comSha"):
                fixed_commit = line.split("comSha:")[1]
            elif line.startswith("parentComSha"):
                buggy_commit = line.split("parentComSha:")[1]
            elif line.startswith("repoName"):
                repo_url += line.split("repoName:")[1].replace("#", "/")
                name_splitted = line.split("repoName:")[1].split('#')
                repo = (name_splitted[0], name_splitted[1])

        if repo is None or buggy_commit is None or fixed_commit is None:
            for line in lines:
                # second type. Why on earth did the information randomly change???
                if line.startswith("Id"):
                    id = line.split("Id:")[1]
                elif line.startswith("Commit"):
                    fixed_commit = line.split("Commit:")[1]
                elif line.startswith("ParentCommit"):
                    buggy_commit = line.split("ParentCommit:")[1]
                elif line.startswith("FixedFilePath"):
                    filepath = line.split("FixedFilePath:")[1]
                elif line.startswith("GitUserName"):
                    name = line.split("GitUserName:")[1]
                    repo_url += name + "/"
                    if repo is None:
                        repo = (name, None)
                    else:
                        repo = (name, repo[1])

                elif line.startswith("GitRepoName"):
                    name = line.split("GitRepoName:")[1]
                    repo_url += name
                    if repo is None:
                        repo = (None, name)
                    else:
                        repo = (repo[0], name)
                elif line.startswith("repoName"):
                    repo_url = "https://www.github.com/"
                    repo_url += line.split("repoName:")[1].replace("#", "/")
                    name_splitted = line.split("repoName:")[1].split('#')
                    repo = (name_splitted[0], name_splitted[1])

        bench_data[id] = (buggy_commit, fixed_commit, filepath, repo_url, repo)
        uniq_repos.add((repo, repo_url))


def download(repo_url, repo, buggy_commit):
    path = "/home/root/Workspace/bowen_bench_checkouts/"

    # change to bowen_bench_checkouts to store the checked out projects
    original_path = os.getcwd()
    os.chdir(path)

    if not os.path.exists(path + repo[1]):

        process = subprocess.Popen(['timeout', '900', 'git', 'clone', repo_url],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        sys.stderr.write('starting git clone ... ')
        out, err = process.communicate()
        sys.stderr.write(err.decode('utf-8'))
    try:
        os.chdir(path + repo[1])
    except:
        return False

    process = subprocess.Popen(['timeout', '900', 'git', 'checkout', '-f', buggy_commit],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)

    sys.stderr.write('starting git checkout ...  for buggy commit  of ... ' + repo[1] + ' : ' + buggy_commit + '\n')
    out, err = process.communicate()
    sys.stderr.write(err.decode('utf-8'))

    # switch back
    os.chdir(original_path)

    return True


def checkout_fixed_version(repo, fixed_commit):
    path = "/home/root/Workspace/bowen_bench_checkouts/"
    original_path = os.getcwd()

    os.chdir(path + repo[1])

    process = subprocess.Popen(['timeout', '900', 'git', 'checkout', '-f', fixed_commit],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    sys.stderr.write('starting git checkout ...  for fixed commit of ...' + repo[1] + ' : ' + fixed_commit + '\n')
    out, err = process.communicate()
    sys.stderr.write(err.decode('utf-8'))

    os.chdir(original_path)


def already_exists(repo, file_path, name):
    serialized_ast_path_root = '/home/root/Workspace/github/data/'
    ast_path_root = "__" + repo[0] + "_" + repo[1] + "_po/"

    return os.path.exists(serialized_ast_path_root + ast_path_root + name)


def ast_of(repo, file_path, name):
    path = "/home/root/Workspace/bowen_bench_checkouts/"

    repo_path = path + repo[1] + "/"

    ast_path_root = "__" + repo[0] + "_" + repo[1] + "_po/"

    filename = file_path.split("/")[-1]
    path_buggy_ast = ast_path_root + "buggy_" + fixed_commit + "_" + filename + ".po"
    path_fixed_ast = ast_path_root + "fixed_" + fixed_commit + "_" + filename + ".po"
    if ast_path_root + name not in [path_buggy_ast, path_fixed_ast]:
        raise Exception("arghh... wrong name. Should be one of " + path_buggy_ast + " or " + path_fixed_ast + ", but got " + name)

    serialized_ast_path_root = '/home/root/Workspace/github/data/'
    if not os.path.exists(serialized_ast_path_root):
        os.mkdir(serialized_ast_path_root + ast_path_root)

    # mvn exec:java -Dexec.mainClass="genesis.infrastructure.TestAppManager"  -Dexec.args="/home/root/Workspace/bowen_bench_checkouts/IridiumSkyblock/ /home/root/Workspace/bowen_bench_checkouts/IridiumSkyblock/src/main/java/com/peaches/epicskyblock/listeners/onSpawnerSpawn.java  /home/root/Workspace/github/data/__IridiumLLC_IridiumSkyblock_po/fixed_3.po"

    exec_args = '-Dexec.args="{} {} {}"'.format(repo_path, repo_path + file_path, serialized_ast_path_root + ast_path_root + name)
    command = ['MAVEN_OPTS="-Xms256m -Xmx40g"', "mvn", "exec:java", '-Dexec.mainClass="genesis.infrastructure.TestAppManager"', exec_args]
    with open('commands/command_' + name + '.sh', 'w+') as outfile:
        outfile.write(' '.join(command))

    sys.stderr.write('executing sh commands/command_' + name + '.sh, which should build the ast \n')
    sys.stderr.write(' '.join(command) + ' \n')

    os.system('sh ' + 'commands/command_' + name + '.sh')

    sys.stderr.write('checking if path exists at : ' + serialized_ast_path_root + ast_path_root + name + '\n')
    result = os.path.exists(serialized_ast_path_root + ast_path_root + name)
    sys.stderr.write('\texists=' + str(result) + '\n')

    return result


def construct_sql_for_applications(uniq_repos):
    sql_inserts = []
    row_id = 1
    application_ids = {}
    for repo, repo_url in uniq_repos:

        format_str = "INSERT INTO `application` VALUES ({},'{}','{}','{}','2020-01-01 00:00:01');"
        sql_insert = format_str.format(row_id, repo[0], repo[1], repo_url)
        sql_inserts.append(sql_insert)

        application_ids[repo_url] = row_id

        row_id += 1

    return sql_inserts, application_ids


def construct_sql_for_patch(bench_data, application_ids):
    sql_inserts = []
    for row_id, (buggy_commit, fixed_commit, filepath, repo_url, repo) in bench_data.items():
        application_id = application_ids[repo_url]
        format_str = "INSERT INTO `patch` VALUES ({},{},'{}','{}','{}','{}','2019-01-01 00:00:01',1,'commit {}\nNot including msg',NULL,NULL,NULL,NULL,NULL,NULL);"
        ast_path_root = "__" + repo[0] + "_" + repo[1] + "_po/"
        path_buggy_ast = ast_path_root + "buggy_" + fixed_commit + "_" + filepath.split("/")[-1] + ".po"
        path_fixed_ast = ast_path_root + "fixed_" + fixed_commit + "_" + filepath.split("/")[-1] + ".po"

        sql_insert = format_str.format(row_id, application_id, buggy_commit, fixed_commit, path_buggy_ast, path_fixed_ast, fixed_commit)
        sql_inserts.append(sql_insert)

    return sql_inserts


if __name__ == '__main__':
    print('sys.argv:' , sys.argv)

    bench_data_to_insert = {}
    insert_id = 0
    for row_id, (buggy_commit, fixed_commit, filepath, repo_url, repo) in bench_data.items():
        print('next piece of data', row_id, repo_url, buggy_commit)
        success = True

        try:
            commit_as_id = fixed_commit
            filename = filepath.split("/")[-1]
            buggy_po_file = "buggy_" + commit_as_id + "_" + filename + ".po"
            fixed_po_file = "fixed_" + commit_as_id + "_" + filename + ".po"
            if not already_exists(repo, filepath, buggy_po_file) \
                    or not already_exists(repo, filepath, fixed_po_file):

                success &= download(repo_url, repo, buggy_commit)

                if success:

                    success &= ast_of(repo, filepath, buggy_po_file)

                if success:
                    print('getting fixed version data', row_id, repo_url, fixed_commit)
                    checkout_fixed_version(repo, fixed_commit)
                    success &= ast_of(repo, filepath, fixed_po_file)

            else:
                print('already present. Can skip')
            if success:
                bench_data_to_insert[insert_id] = (buggy_commit, fixed_commit, filepath, repo_url, repo)
                insert_id += 1

        except Exception as e:
            # if by some insane exceptional case, something fails but hasn't been handled
            # just ignore and continue
            print('Completely mismanaged case')
            print(e)
            import traceback

            traceback.print_exc()
            continue
        # print('done one', row_id)
        # break

    application_inserts, application_ids = construct_sql_for_applications(uniq_repos)

    with open('insert_from_bowen_create_ast_' + sys.argv[1] + '.sql', 'w+') as outfile:
        outfile.write("USE genesis;\n")
        for application_insert in application_inserts:
            outfile.write(application_insert + '\n')

        patch_inserts = construct_sql_for_patch(bench_data_to_insert, application_ids)
        for patch_insert in patch_inserts:
            outfile.write(patch_insert + '\n')

    print('done all')
