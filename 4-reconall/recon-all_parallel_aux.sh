#!/bin/bash

# Load subject IDs from the list file
mapfile -t todo_ids < "$LIST_FILE"

# Iterate over the array of subject IDs
for subject_id in "${todo_ids[@]}"; do
    # Strip directory path to have only the subject ID
    subject_id=$(basename "$subject_id")

    # Define directory and filename based on SESSION
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
        
        # Check for errors
        if [ $? -ne 0 ]; then
            echo "Error processing $subject_id. Check FreeSurfer logs for details."
            continue
        fi

        # Move processed data if subject and directory names differ
        if [ "$subject_id" != "$subdir" ]; then
            mv "$SUBJECTS_DIR/$subject_id" "$SUBJECTS_DIR/$subdir"
        fi
    else
        echo "Required files for $subject_id not found in $BIDS_FOLDER/$subsesbids. Skipping..."
    fi
done