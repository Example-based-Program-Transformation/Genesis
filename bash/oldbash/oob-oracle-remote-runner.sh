#!/bin/bash
MACHINES=(ec2-54-197-2-240
          ec2-54-172-37-170
          ec2-52-90-55-142
          ec2-54-152-172-4)

CASES=({1..13})

RESULTS_DIR="/raid/petera/genesis/results/oob-oracle/$(date -Iminutes)"
mkdir -p $RESULTS_DIR

#mkdir -p results
#MACHINE_CASES=("1 2" "3 4" "5 6" "7 8" "9 10" "11 12" "13 14" "15 16" "17 18" "19 20")
#for i in $(seq 0 $((${#MACHINE_CASES[@]}-1))); do
#	for c in ${MACHINE_CASES[$i]}; do scp -r ${MACHINES[$i]}:/home/ubuntu/Workspace/genesis/rdir$c results/; done
#done
#exit 0

# Statuses and updating is handled per *machine*.

# MACHINE_CASES: The remaining cases that need to be run on that
# machine. Does not include the case that is currently being run.

# MACHINE_CUR_CASE: The case currently being run on a machine

# If MACHINE_CUR_CASE is empty and MACHINE_CASES is not, we should
# take the first case from MACHINE_CASES and run it:

# CASE_STATES[i] =
#   0: Waiting in the queue.  Everything is initialized here
#   1: Running on a machine
#   2: Downloading
#   3: All done

# DL_CASES: Array of cases

declare -a CASE_STATES
for c in "${CASES[@]}"; do
	CASE_STATES[$c]=0
done

DL_CASES=()
CASES_TO_RUN=("${CASES[@]}")

function update_cur_cases() {
	for i in $(seq 0 $((${#MACHINES[@]}-1))); do
		if ! ssh ${MACHINES[$i]} ps ax | grep genesis >/dev/null; then
			if [ -n "${MACHINE_CUR_CASE[$i]}" ]; then
				case="${MACHINE_CUR_CASE[$i]}"
				CASE_STATES[$case]=2
				MACHINE_CUR_CASE[$i]=""
				DL_CASES+=($case)
				start_dl $i $case &
			fi
		fi
	done
}

function start_dl() {
	echo "scp -r ${MACHINES[$1]}:/home/ubuntu/Workspace/genesis/oobrdir$2 $RESULTS_DIR/ >/tmp/scp_oobrdir$2_out.log 2>/tmp/scp_oobrdir$2_err.log &" >/tmp/scp_oobrdir$2_cmd
	scp -r ${MACHINES[$1]}:/home/ubuntu/Workspace/genesis/oobrdir$2 $RESULTS_DIR/ >/tmp/scp_oobrdir$2_out.log 2>/tmp/scp_oobrdir$2_err.log
	echo "scp -r ${MACHINES[$1]}:/home/ubuntu/Workspace/genesis/oobwdir$2 $RESULTS_DIR/ >/tmp/scp_oobwdir$2.log 2>/tmp/scp_oobwdir$2_err.log &" >/tmp/scp_oobwdir$2_cmd
	scp -r ${MACHINES[$1]}:/home/ubuntu/Workspace/genesis/oobwdir$2 $RESULTS_DIR/ >/tmp/scp_oobwdir$2.log 2>/tmp/scp_oobwdir$2_err.log
}

function update_dl_cases() {
	to_remove=()
	for c in "${DL_CASES[@]}"; do
		if ! ps ax | grep -v grep | grep "scp.*[rw]dir$c" >/dev/null; then
			to_remove+=($c)
		fi
	done
	for c in "${to_remove[@]}"; do
		DL_CASES=( "${DL_CASES[@]/$c}" )
		CASE_STATES[$c]=3
	done
}

function queue_case() {
	case=${CASES_TO_RUN[0]}
	ssh ${MACHINES[$1]} tmux new-session -d -s genesis_oob_repair_$case "'cd /home/ubuntu/Workspace/genesis; bash/run-oob-case.sh $case oracle'"
	MACHINE_CUR_CASE[$1]=$case
	CASES_TO_RUN=("${CASES_TO_RUN[@]:1}")
	CASE_STATES[$case]=1
}

function case_status() {
	case ${CASE_STATES[$1]} in
		0) echo "Waiting..."
		   ;;
		1) echo "Running..."
		   ;;
		2) echo "Downloading..."
		   ;;
		3) echo "Done!"
	esac
}

while true; do
	update_cur_cases
	update_dl_cases
	clear
	printf "%-18s %-9s\n" "Machine" "Cur. case"
	for i in $(seq 0 $((${#MACHINES[@]}-1))); do
		printf "%-18s %-9s\n" "${MACHINES[$i]}" "${MACHINE_CUR_CASE[$i]}"
		if [ -z "${MACHINE_CUR_CASE[$i]}" -a -n "${CASES_TO_RUN}" ]; then
			echo "queuing next case for machine: $i" >>/tmp/operations.log
			queue_case $i
		fi
	done
	printf "\n\n"
	printf "Remaining cases: ${CASES_TO_RUN[*]}\n"
	printf "\n\n"
	should_continue=false
	for i in "${CASES[@]}"; do
		printf "Case %3s status: %s\n" $i $(case_status $i)
		if [ ${CASE_STATES[$i]} -ne 3 ]; then
			should_continue=true
		fi
	done
	if ! $should_continue; then
		break
	fi
done

printf "\n\nAll done!\n"































# For each machine, start running the cases. Somewhat integrated with
# machinies tatuses?

# for i in $(seq 0 $((${#MACHINE_CASES[@]}-1))); do
# 	echo -e "Machine ${MACHINES[$i]}\tcases: ${MACHINE_CASES[$i]}"
# 	#ssh ${MACHINES[$i]} tmux new-session -d -s genesis_repair "cd /home/ubuntu/Workspace/genesis; for 
# done



# Status display: every 10 seconds, check in once for each machine.
# If a case just finished, download the results

