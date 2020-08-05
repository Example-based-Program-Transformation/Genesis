"""
Create a test-case from one data point and run the learned space of transformations on it
1. Create case files
2. Run initialization step of Genesis:
mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-c npe-space-tv/candidate -s npe-space-tv/space.txt -init-only -w npe-wdir1 npe-case1/case.conf"
3. Run BowenDefectLocationProducer to create localization.log file
4. Run final step of Genesis:
mvn exec:java -Dexec.mainClass="genesis.repair.Main" -Dexec.args="-c npe-space-tv/candidate -s npe-space-tv/space.txt -skip-init -w npe-wdir1"

1. Given path_to_example, e.g. "~/Workspace/bowen_bench/NULL_DEFERENCE/46/"
path_to_example ->
(path_to_example -> info) ->
(info -> before_commit) ->
(() -> test case file) ->
(() -> case conf file) ->
(info -> before_commit -> git_repo) ->
(git_repo -> download(git_repo)) ->
download(git_repo)

Constructs the equivalent of npe-case1 directory. This directory contains case.conf file, testcase.txt file (empty), and src_orig

2.

3. Use BowenDefectLocationProducer.java
mvn exec:java -Dexec.mainClass="genesis.infrastructure.BowenDefectLocationProducer" -Dexec.args="/home/root/Workspace/bowen_bench/PTBench-Data-master/NULL_DEREFERENCE/150/pair.info /home/root/Workspace/bowen_bench/PTBench-Data-master/NULL_DEREFERENCE/150/diff.txt"


run:
python python/fixbench_create_case_from_training.py null_deference_174 /home/root/Workspace/PTBench-Data/NULL_DEREFERENCE/174  custom_case_null_deference_174 custom-space


"""

import os
import sys
import subprocess
import shutil
import shutil

path_to_ptbench = "/home/root/Workspace/PTBench-Data/"


def run_command(command, id, witness=None):
    with open('commands/command_' + id + '.sh', 'w+') as outfile:
        outfile.write(' '.join(command))

    sys.stderr.write('executing commands/command_' + id + '.sh \n')
    sys.stderr.write(' '.join(command) + ' \n')

    os.system('sh ' + 'commands/command_' + id + '.sh')

    if witness is None:
        return True

    result = witness()

    if not result:
        sys.stderr.write('\tresult is false' + ' \n')
    else:
        os.remove('commands/command_' + id + '.sh')
    return result


def run_init(candidate_dir, space_file, workdir_to_create, case_file, id):
    """
    Step 2
    """
    def witness():
        dir_exists = os.path.exists(workdir_to_create) and os.path.isdir(workdir_to_create)
        return dir_exists

    command = ["mvn", "exec:java", '-Dexec.mainClass="genesis.repair.Main"', '-Dexec.args="-c ' + candidate_dir + ' -s ' + space_file + ' -init-only -w ' + workdir_to_create + ' ' + case_file + '"']
    success = run_command(command, '_init_' + id, witness)
    return success


def write_localization_file(path_to_info, path_to_diff, workdir, case_dir_name, id):
    """
    Step 3
    """
    def witness():
        exists = os.path.exists('localization.log')
        shutil.move('localization.log', workdir + '/localization.log')
        exists &= os.path.exists(workdir + '/localization.log')
        return exists

    if not os.path.exists(workdir) or not os.path.isdir(workdir):
        raise Exception("argh")

    if os.path.exists(workdir + '/localization.log'):
        os.remove(workdir + '/localization.log')

    path_to_repo = case_dir_name + '/src_orig'
    command = ['mvn', 'exec:java', '-Dexec.mainClass="genesis.infrastructure.FixBenchDefectLocationProducer"',
               '-Dexec.args="' + path_to_info + ' ' + path_to_diff + ' ' + path_to_repo + '"']
    success = run_command(command, '_localization_' + id, witness)
    return success


def run_repair(candidate_dir, space_file, workdir, id):
    """
    Step 4
    """

    def witness():
        exists = os.path.exists(workdir)
        return exists

    command = ['timeout', '60m', 'mvn', 'exec:java', '-Dexec.mainClass="genesis.repair.Main"', '-Dexec.args="-c ' + candidate_dir + ' -s ' + space_file + ' -skip-init -w ' + workdir + '"']
    success = run_command(command, '_init_' + id, witness)
    return success


def move_generated_patches(id):
    os.mkdir('patches_' + id)
    for i in range(11, 99):
        command = ['mv', '__patch' + str(i) + '*', 'patches_' + id]

        run_command(command, 'move_patches_' + id + '_' + str(i))

    command = ['mv', '__patch*', 'patches_' + id ]

    run_command(command, 'move_patches_' + id)


def download_repo_as_case_directory(path_to_example, case_dir_name, id):
    """
    Step 1
    """
    def read_info(path_to_example):
        file = path_to_example + '/' + 'pair.info'
        with open(file) as f:
            info = {}
            for line in f:
                split = line.strip().split(':')
                key = split[0]
                value = split[1]
                info[key] = value
            return info

    def get_old_commit(info):
        if 'parentComSha' in info:
            return info['parentComSha']
        else:
            return info['ParentCommit']

    def write_test_case_file():
        with open(case_dir_name + '/testcase.txt', 'w+') as outfile:
            outfile.write('\n')

    def write_case_conf_file():
        with open(case_dir_name + '/case.conf', 'w+') as outfile:
            outfile.write('src=src_orig\n')
            outfile.write('testcase=testcase.txt\n')

    def git_repo(info, before_commit):
        if 'repoName' in info:
            repo_name = info['repoName'].replace('#', '/')
            repo_dir = info['repoName'].split('#')[1]
            repo_url = "https://www.github.com/" + repo_name
        else:
            repo_name = info['GitUserName'] + '/' + info['GitRepoName']
            repo_dir = info['GitUserName']
            repo_url = "https://www.github.com/" + repo_name

        return (repo_url, repo_dir, before_commit)

    def download(github_repo, id):
        repo_url, repo_dir, before_commit = github_repo

        original_path = os.getcwd()

        os.chdir(case_dir_name)

        process = subprocess.Popen(['timeout', '2400', 'git', 'clone', repo_url, 'src_orig'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        sys.stderr.write('starting git clone ... ')
        print(process.communicate())

        os.chdir('src_orig')

        process = subprocess.Popen(['timeout', '2400', 'git', 'checkout', '-f', before_commit],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

        sys.stderr.write('starting git checkout ...  for buggy commit  of ... ' + 'custom_case_' + id + ' : ' + before_commit + '\n')
        out, err = process.communicate()
        sys.stderr.write(err.decode('utf-8'))

        # switch back
        os.chdir(original_path)

    if os.path.exists(case_dir_name):
        raise Exception("hmm, case_dir already exists " + case_dir_name)

    os.mkdir(case_dir_name)


    info = read_info(path_to_example)
    old_commit = get_old_commit(info)

    write_test_case_file()

    write_case_conf_file()

    repo_info = git_repo(info, old_commit)

    download(repo_info, id)


if __name__ == '__main__':
    # assuming that training already done and put in ...
    print('Executing fixbench_create_case_from_training.py:')
    print(sys.argv)
    id = sys.argv[1]
    path_to_example = sys.argv[2]
    case_dir_name = sys.argv[3]
    trained_space = sys.argv[4]

    if not os.path.exists(case_dir_name):
        download_repo_as_case_directory(path_to_example, case_dir_name, id)

    workdir = id + 'wdir'

    if not os.path.exists(workdir):
        run_init(trained_space + '/candidate', trained_space + '/space.txt', workdir, case_dir_name + '/case.conf', id)

    # running the localization file creation script is important. Always run it, even if the file looks like it's already there
    # because Genesis creates an empty loacalization file.
    # if not os.path.exists(workdir + '/localization.log'):
    write_localization_file(path_to_example + "/pair.info", path_to_example + "/diff.txt", workdir, case_dir_name, id)

    run_repair(trained_space + '/candidate', trained_space + '/space.txt', workdir, id)

    move_generated_patches(id + "_" + trained_space)
    shutil.rmtree(workdir)  # save space by removing wdir

