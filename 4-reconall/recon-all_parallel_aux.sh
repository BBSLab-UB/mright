#!/bin/bash

# Load subject IDs from the list file
mapfile -t todo_ids < "$LIST_FILE"

# Iterate over the array of subject IDs
for id in "${!todo_ids[@]}"; do
    # Strip directory path to have only the subject ID
    todo_ids[$id]=$(basename "${todo_ids[$id]}")
done

# Retrieve the current subject ID using the SLURM array task ID
subject_id=${todo_ids[$SLURM_ARRAY_TASK_ID]}

# Construct directory and filename paths based session
if [ -z "$SESSION" ]; then
    # No session specified; use subject ID directly
    subdir=${subject_id}
    subsesbids=${subject_id}
else
    # Session specified; include it in directory and file paths
    subdir=${subject_id}_ses-${SESSION}
    subsesbids=${subject_id}/ses-${SESSION}
fi

# Check if the subject is already processed
if [ -e "$SUBJECTS_DIR/$subdir" ]; then
    echo "$subject_id is already processed. Skipping..."
elif [ -e "$BIDS_FOLDER/$subsesbids/anat/${subdir}_run-01_T2w.nii.gz" ]; then
    # Run FreeSurfer recon-all command
    recon-all -all -s "$subject_id" -T2 "$BIDS_FOLDER/$subsesbids/anat/${subdir}_run-01_T2w.nii.gz" -T2pial -i "$BIDS_FOLDER/$subsesbids/anat/${subdir}_run-01_T1w.nii.gz" -3T -openmp "$PCORES"
    
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
