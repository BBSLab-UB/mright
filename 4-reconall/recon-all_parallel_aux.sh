#!/bin/bash

# File containing the subject IDs
TODO_IDS_FILE="$HOME/Desktop/mright-main/4-reconall/todo.txt"

# Session number
SESSION="02"

# Input and output directories 
SUBJECTS_DIR="$HOME/Desktop/Output"
BIDS_FOLDER="$HOME/Desktop/BIDS"

# Number of cores to use for parallel processing
PCORES=2

# Load subject IDs from todo file
mapfile -t todo_ids < "$TODO_IDS_FILE"

# Iterate over the array of subject IDs
for subject_id in "${todo_ids[@]}"; do
    # Strip directory path if present
    subject_id=$(basename "$subject_id")

    # Create directory and filename based on SESSION
    if [ -z "$SESSION" ]; then
        subdir=${subject_id}
        subsesbids=${subject_id}
    else
        subdir=${subject_id}_ses-${SESSION}
        subsesbids=${subject_id}/ses-${SESSION}
    fi

    # Check if the subject is already processed
    if [ -e "$SUBJECTS_DIR/$subdir" ]; then
        echo "$subject_id is already processed. Skipping..."
    elif [ -e "$BIDS_FOLDER/$subsesbids/anat/${subdir}_run-01_T2w.nii.gz" ]; then
        # Run FreeSurfer recon-all command
        recon-all -all -s "$subject_id" -T2 "$BIDS_FOLDER/$subsesbids/anat/${subdir}_run-01_T2w.nii.gz" -T2pial -i "$BIDS_FOLDER/$subsesbids/anat/${subdir}_run-01_T1w.nii.gz" -3T -openmp "$PCORES"

        # Move processed data if subject and directory names differ
        if [ "$subject_id" != "$subdir" ]; then
            mv "$SUBJECTS_DIR/$subject_id" "$SUBJECTS_DIR/$subdir"
        fi
    else
        echo "Required files for $subject_id not found in $BIDS_FOLDER/$subsesbids. Skipping..."
    fi
done