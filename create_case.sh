directory_of_data="/home/root/Workspace/PTBench-Data/2ndLabel/Substaintial"


# look at create_case_one.sh instead.
# this is a similar script, in that it is run for evaluation
# but this randomly picks 30 cases to run on

echo $1
echo ${directory_of_data}
ids=$(ls -t -U $directory_of_data/$1 | grep "#" | shuf -n 30 )

for id in $ids
do
	echo $id
	{ 
		timeout 60m python3 python/fixbench_create_case_from_training.py $1_$id $directory_of_data/$1/$id  custom_case_$1_$id $1_space || { echo 'failed to create case' > failed_case_$id.log ;  }	
   	} > test_script_$1_$id.log 2> test_script_$1_$id.err 	
	wait
done
echo 'done'
