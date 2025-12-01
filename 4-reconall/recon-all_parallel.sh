#!/bin/bash

# ============================================
# Script for Running Recon-All with SLURM
# ============================================
# Usage:
#   bash recon-all_parallel.sh -o <output_dir> -i <input_dir> -p <cores> [-s <session>] [-l <list_file>]
#
# Arguments:
#   -o, --output_dir    Directory to store processed subjects
#   -i, --input_dir     BIDS directory containing input data
#   -s, --session       Session identifier (e.g., "01"), only required in longitudinal studies
#   -p, --pcores        Number of cores to use per task
#   -l, --list_file     Optional - file containing a list of subject IDs. If not provided, the script will auto-generate a list based on the input directory.
# ============================================

echo "Script for running recon-all in parallel"

# Parse command line arguments
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
        -l|--list_file)
        LIST_FILE="$2"
        shift; shift
        ;;
        *) # Unknown option
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
done

# Ensure all required variables are set
if [ -z "$SUBJECTS_DIR" ] || [ -z "$BIDS_FOLDER" ] || [ -z "$PCORES" ]; then
    echo "Missing arguments. Usage:"
    echo "bash script.sh -o <output_dir> -i <input_dir> -p <cores> [-s <session>] [-l <list_file>]"
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

# Generate the list of subjects to be processed
generate_todo_list() {
    local input_dir="$1"
    local output_dir="$2"
    local todo_list=()

    # Iterate over subjects in the input directory
    for subj_dir in "$input_dir"/sub-*; do
        subj_num=${subj_dir##*/sub-}

        # Dynamically determine the session path
        local ses_dir="$subj_dir/ses-${SESSION}"

        # Check for the session directory and if it does not need processing
        if [ -d "$ses_dir" ] && [ ! -d "$output_dir/sub-${subj_num}_ses-${SESSION}" ]; then
            todo_list+=("$subj_num")
        fi
    done

    # Save the list as an object
    LIST_FILE=("${todo_list[@]}")
    echo "Subjects needing processing: ${LIST_FILE[@]}"
}

# Build todo_ids: from list file if provided, else auto-generate
if [ -n "${LIST_FILE:-}" ]; then
  [ -f "$LIST_FILE" ] || { echo "List file does not exist: $LIST_FILE"; exit 1; }
  mapfile -t todo_ids < "$LIST_FILE"
  echo "Using list file: ${todo_ids[*]}"
else
  generate_todo_list "$BIDS_FOLDER" "$SUBJECTS_DIR"
  todo_ids=("${LIST_FILE[@]}")  # LIST_FILE is the array from generate_todo_list
fi

# Check if todo_ids is empty
if [ ${#todo_ids[@]} -eq 0 ]; then
  echo "No subjects to process."; exit 0
fi

# Configure SLURM Job Settings
num_tasks=${#todo_ids[@]}
num_tasks_idx=$(($num_tasks - 1))

# Determine system capabilities for task distribution (slurm will use, at most, 90% of the cores)
num_cores=$(nproc)
max_tasks=$(echo "($num_cores * 0.9) / $PCORES" | bc -l | awk '{print int($1)}')

# Display configured settings for confirmation
echo
echo "Configured Settings:"
echo "---------------------"
echo "Output Directory:       $SUBJECTS_DIR"
echo "BIDS Directory:         $BIDS_FOLDER"
echo "Session Number:         $SESSION"
echo "Cores per Task:         $PCORES"

# Load necessary software modules
module load fsl/5.0.11 freesurfer/freesurfer-6.0.0

# Create symlink for fsaverage to resolve the issue with missing FG labels (makes sure the fsaverage directory is linked correctly)
rm -rf "$SUBJECTS_DIR/fsaverage"
ln -s "$FREESURFER_HOME/subjects/fsaverage" "$SUBJECTS_DIR/fsaverage"

# Capture the current date for log file naming
today_date=$(date '+%Y%m%d')
echo "Log file will be stored in the current directory."

# Generate BIDS dataset_description.json
cat > "$SUBJECTS_DIR/dataset_description.json" <<EOF
{
  "Name": "Recon-all Output",
  "BIDSVersion": "1.10.1",
  "PipelineDescription": {
    "Name": "Recon-all Pipeline",
    "Version": "1.1",
    "Software": [
      {
        "Name": "FreeSurfer",
        "Version": "6.0.0"
      },
      {
        "Name": "FSL",
        "Version": "5.0.11"
      }
    ]
  }
}
EOF

# Establish the maximum memory per CPU permitted
cpu_mem=$(( $(free -m | awk 'NR==2{print $2}') / $(nproc) ))

# Add the sub- prefix to each ID, if needed
prefixed_ids=()
for id in "${todo_ids[@]}"; do
  [[ "$id" == sub-* ]] && prefixed_ids+=("$id") || prefixed_ids+=("sub-$id")
done

# Export the todo_ids_str for the SLURM job
export todo_ids_str=$(IFS=' '; echo "${prefixed_ids[*]}")
echo "About to submit SLURM job with todo_ids: $todo_ids_str"

# Submit the SLURM array job
sbatch --export=ALL,SUBJECTS_DIR="$SUBJECTS_DIR",todo_ids_str="$todo_ids_str",BIDS_FOLDER="$BIDS_FOLDER",SESSION="$SESSION",PCORES="$PCORES" <<EOF
#!/bin/bash
#SBATCH --job-name=recon-alls
#SBATCH --ntasks=1
#SBATCH --array=0-${num_tasks_idx}%${max_tasks}
#SBATCH -e ${SUBJECTS_DIR}/recon-all_${today_date}_%A_errorlog.out
#SBATCH --cpus-per-task=${PCORES}
#SBATCH --nodes=1
#SBATCH --partition=batch
#SBATCH --time=5-00:00:00
#SBATCH --mem-per-cpu=${cpu_mem}M

# Load necessary modules
module load fsl/5.0.11 freesurfer/freesurfer-6.0.0

# Create symlink for fsaverage 
rm -rf "$SUBJECTS_DIR/fsaverage"
ln -s "$FREESURFER_HOME/subjects/fsaverage" "$SUBJECTS_DIR/fsaverage"

# Convert exported todo_ids string back to an array in this sbatch environment
IFS=' ' read -r -a local_todo_ids <<< "\$todo_ids_str"

# Get the subject id for this task
subj_id="\${local_todo_ids[\$SLURM_ARRAY_TASK_ID]}"
echo "Processing subject ID: \$subj_id"

# Determine the input path
if [ -n "\$SESSION" ]; then
    input_path="\$BIDS_FOLDER/\$subj_id/ses-\$SESSION"
else
    input_path="\$BIDS_FOLDER/\$subj_id"
fi

# Check if input path exists
if [ ! -d "\$input_path" ]; then
    echo "Required files for \${subj_id} not found in \$input_path. Skipping..."
    exit 1
fi

# Run the auxiliary script for this subject
srun bash recon-all_parallel_aux.sh "\$input_path"

EOF