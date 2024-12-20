#!/bin/bash

# ============================================
# Script for Running Recon-All with SLURM
# ============================================
# Usage:
#   bash recon-all_parallel.sh -o <output_dir> -i <input_dir> -l <list_file> -p <cores> [-s <session>]
#
# Arguments:
#   -o, --output_dir    Directory to store processed subjects
#   -i, --input_dir     BIDS directory containing input data
#   -l, --list_file     File containing a list of subject IDs
#   -s, --session       Session identifier (e.g., "01"), only required in longitudinal studies
#   -p, --pcores        Number of cores to use per task
# ============================================

echo "Script for running recon-all in parallel"

while [[ $# -gt 0 ]]; do
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
        *) # Unknown option
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
done

# Error handling

# Ensure all required variables are set
if [ -z "$SUBJECTS_DIR" ] || [ -z "$BIDS_FOLDER" ] || [ -z "$LIST_FILE" ] || [ -z "$PCORES" ]; then
    echo "Missing arguments. Usage:"
    echo "bash script.sh -o <output_dir> -i <input_dir> -l <list_file> -p <cores> [-s <session>]"
    exit 1
fi

if [ -z "$SESSION" ]; then
    echo "Optional session argument is missing, proceeding without session. If the study is longitudinal, program will fail."
fi

# Check if files and directories exist
if [ ! -d "$SUBJECTS_DIR" ]; then
    echo "Output directory does not exist: $SUBJECTS_DIR"
    exit 1
fi

if [ ! -d "$BIDS_FOLDER" ]; then
    echo "BIDS directory does not exist: $BIDS_FOLDER"
    exit 1
fi

if [ ! -f "$LIST_FILE" ]; then
    echo "List file does not exist: $LIST_FILE"
    exit 1
fi

# Configure SLURM Job Settings

# Calculate the number of tasks from the list file
num_tasks=$(echo $(wc -l < "$LIST_FILE"))
num_tasks_idx=$(($num_tasks - 1))

# Determine system capabilities for task distribution (slurm will use, at most, the 90% of the cores)
num_cores=$(nproc)
max_tasks=$(echo "($num_cores * 0.9) / $PCORES" | bc -l | awk '{print int($1)}')

# Display configured settings for confirmation
echo
echo "Configured Settings:"
echo "---------------------"
echo "Output Directory:       $SUBJECTS_DIR"
echo "BIDS Directory:         $BIDS_FOLDER"
echo "Subject List File:      $LIST_FILE"
echo "Session Number:         $SESSION"
echo "Cores per Task:         $PCORES"

# Prepare Subject IDs

# Load subject IDs from the list file
mapfile -t todo_ids < "$LIST_FILE"

# Process each subject ID
for i in "${!todo_ids[@]}"; do
  todo_ids[$i]=$(basename "${todo_ids[$i]}")
done

# Display subjects to be processed
echo "To Do Subjects:         ${todo_ids[*]}"

# Load necessary software modules
module load fsl/6.0.4 freesurfer/freesurfer-7.1

# Capture the current date for log file naming
today_date=$(date '+%Y%m%d')
echo 'Log file will be stored in the current directory.'

# Establish the maximum memory per CPU permitted
cpu_mem=$(($(free -m | awk 'NR==2{print $2}') / $(nproc)))

# Submit the SLURM array job
sbatch <<EOF
#!/bin/bash
#SBATCH --job-name=recon-alls                                           # Job name
#SBATCH --ntasks=1                                                      # Number of tasks (analyses) to run
#SBATCH --array=0-${num_tasks_idx}%${max_tasks}                         # Array of running tasks
#SBATCH -e ${SUBJECTS_DIR}/recon-all_${today_date}_%A_errorlog.out      # Output filenames for logs
#SBATCH --cpus-per-task=${PCORES}                                       # CPUs allocated to each task
#SBATCH --nodes=1                                                       # Nodes allocated to each task
#SBATCH --partition=batch                                               # Partitions (queue) to submit job to (comma separated)
#SBATCH --time=5-00:00:00                                               # Time limit for analysis (day-hour:min:sec)
#SBATCH --mem-per-cpu=${cpu_mem}M

srun bash recon-all_parallel_aux.sh
EOF
