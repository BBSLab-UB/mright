#!/bin/bash

#LIST_FILE=/home/arnau/Desktop/list.txt
#SLURM_ARRAY_TASK_ID=1
#SESSION=02

mapfile -t todo_ids < "$LIST_FILE"

for i in "${!todo_ids[@]}"; do
  todo_ids[$i]=$(basename "${todo_ids[$i]}")
done

# Access the element using the SLURM_ARRAY_TASK_ID
subject_id=${todo_ids[$SLURM_ARRAY_TASK_ID]}
if [ -z "$SESSION" ]; then
    subdir=${subject_id}
    subsesbids=${subject_id}
else
    subdir=${subject_id}_ses-${SESSION}
    subsesbids=${subject_id}/ses-${SESSION}
fi

if [ -e $SUBJECTS_DIR/${subdir} ] ;then
    echo "${subject_id} is already processed. Skipping..."
elif [ -e $BIDS_FOLDER/${subsesbids} ] ;then
    recon-all -all -s ${subject_id} -T2 $BIDS_FOLDER/${subsesbids}/anat/${subdir}_run-01_T2w.nii.gz -T2pial  -i $BIDS_FOLDER/${subsesbids}/anat/${subdir}_run-01_T1w.nii.gz -3T -openmp $PCORES
    if [ ${subject_id} != ${subdir} ]; then
        mv ${SUBJECTS_DIR}/${subject_id} ${SUBJECTS_DIR}/${subdir}
    fi
fi
