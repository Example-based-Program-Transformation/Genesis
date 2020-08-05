directory_of_data="/home/root/Workspace/PTBench-Data/FinalData-Single/"

# this script is used to run the evaluation on each case in the dataset
# can be run from python/get_evaluation_output_using_k_training_cases.py

# from python: run_command(['sh', 'create_case_one.sh', bug_type, name, trained_space_path], id="run_create_case_" + str(case_id) + "_" + str(k))
# in other words, $1 is the bug_type, $2 is the name of the case (e.g. FBViolation#100), 
#                 $3 is the directory of the trained space

echo $1
echo ${directory_of_data}
echo $2
echo $3
echo $4
{ 
	timeout 60m python3 python/fixbench_create_case_from_training.py $1_$2 $directory_of_data/$1/$2  custom_case_$1_$2 $3  || { echo 'failed to create case' > failed_case_$1_$2_$3.log ;  }	
} > test_script_$1_$2_$3.log 2> test_script_$1_$2_$3.err 	
echo 'done one'
