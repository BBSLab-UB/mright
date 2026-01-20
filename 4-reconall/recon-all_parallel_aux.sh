#!/bin/bash

# Convert the exported todo_ids_str into an array
IFS=' ' read -r -a todo_ids <<< "$todo_ids_str"

# Iterate over the array of subject IDs
for id in "${!todo_ids[@]}"; do
    # Strip directory path to have only the subject ID
    todo_ids[$id]=$(basename "${todo_ids[$id]}")
done

# Retrieve the current subject ID using the SLURM array task ID
subject_id=${todo_ids[$SLURM_ARRAY_TASK_ID]}

# Construct directory and filename paths based on session
if [ -z "$SESSION" ]; then
    # No session specified; use subject ID directly
    subdir=${subject_id}
    subsesbids=${subject_id}
else
    # Session specified; include it in directory and file paths
    subdir=${subject_id}_ses-${SESSION}
    subsesbids=${subject_id}/ses-${SESSION}
fi

# Define file paths
T1_FILE="$BIDS_FOLDER/$subsesbids/anat/${subdir}_run-01_T1w.nii.gz"
T2_FILE="$BIDS_FOLDER/$subsesbids/anat/${subdir}_run-01_T2w.nii.gz"

# Check if the subject is already processed
if [ -e "$SUBJECTS_DIR/$subdir" ]; then
    echo "$subject_id is already processed. Skipping..."
# Check if the T1 file exists
elif [ -e "$T1_FILE" ]; then
    # If T1 exists, check if T2 exists
    if [ -e "$T2_FILE" ]; then
        # If T2 exists, run recon-all with T2 refinement
        echo "Found T1 and T2 for $subject_id. Running recon-all with T2 refinement..."
        recon-all -all -sd "$SUBJECTS_DIR" -s "$subject_id" -T2 "$T2_FILE" -T2pial -i "$T1_FILE" -3T -openmp "$PCORES"
    else
        # If T2 does not exist, run standard recon-all without T2
        echo "Found T1 only for $subject_id. Running recon-all without T2..."
        recon-all -all -sd "$SUBJECTS_DIR" -s "$subject_id" -i "$T1_FILE" -3T -openmp "$PCORES"
    fi

    # Check for errors
    if [ $? -ne 0 ]; then
        echo "Error processing $subject_id. Check FreeSurfer logs for details."
    fi

    # Move processed data if subject and directory names differ
    if [ "$subject_id" != "$subdir" ]; then
        mv "$SUBJECTS_DIR/$subject_id" "$SUBJECTS_DIR/$subdir"
    fi
else
    echo "Required files for $subject_id not found in $BIDS_FOLDER/$subsesbids. Skipping..."
fi