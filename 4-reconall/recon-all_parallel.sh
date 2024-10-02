#!/bin/bash
# bash recon-all_parallel.sh -o subjects_dir_freesurfer -i BIDS_DIRECTORY -l LIST -p CORES -s SESSION

echo SCRIPT FOR RECON-ALLS IN PARALLEL

positional=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -o|--output_dir)
    export SUBJECTS_DIR="$2"
    shift # past argument
    shift # past value
    ;;
    -i|--input_dir)
    export BIDS_FOLDER="$2"
    shift # past argument
    shift # past value
    ;;
    -l|--list_file)
    export LIST_FILE="$2"
    shift # past argument
    shift # past value
    ;;
    -s|--session)
    export SESSION="$2"
    shift # past argument
    shift # past value
    ;;
    -p|--pcores)
    export PCORES="$2"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    positional+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
#gets params from terminal call
set -- "${positional[@]}" # restore positional parameters

#Setting variables for Slurm
num_tasks=$(echo $(wc -l $LIST_FILE) | awk '{print $1;}')
num_tasks_idx=$(($num_tasks - 1))
num_cores=`nproc`
max_tasks=$(($num_cores / $PCORES - 1))

echo 
echo SUBJECTS_DIR $'\t'= "${SUBJECTS_DIR}"
echo BIDS_FOLDER $'\t'= "${BIDS_FOLDER}"
echo LIST_TXT $'\t'= "${LIST_FILE}"
echo SESSION $'\t'= "${SESSION}"
echo PARALLEL CORES $'\t'= "${PCORES}"

mapfile -t todo_ids < "$LIST_FILE"

for i in "${!todo_ids[@]}"; do
  todo_ids[$i]=$(basename "${todo_ids[$i]}")
done

echo TO DO SUBJECTS $'\t'= "${todo_ids[*]}"
#Loading modules and variables
module load fsl/6.0.4 freesurfer/freesurfer-7.1

today_date=$(date '+%Y%m%d')
echo 'Log file will be stored in the current directory.'


sbatch <<EOF
#!/bin/bash
#SBATCH --job-name=recon-alls                    ## name that will show up in the queue
#SBATCH --ntasks=1                               ## number of tasks (analyses) to run
#SBATCH --array=0-${num_tasks_idx}%${max_tasks}  ## array of running tasks
#SBATCH -o recon-all_${today_date}_%A_log.out    ## log file filname
#SBATCH --cpus-per-task=${PCORES}                ## the number of threads allocated to each task
#SBATCH --nodes=1                                ## the number of threads allocated to each task
#SBATCH --partition=batch                        ## the partitions to run in (comma seperated)
#SBATCH --time=5-00:00:00                        ## time for analysis (day-hour:min:sec)

srun bash recon-all_parallel_aux.sh
EOF
