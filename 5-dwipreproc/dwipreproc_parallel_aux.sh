#!/bin/bash

#Constants MB-dMRI & SB-dMRI
#EPI_FACTOR=140
#ECHO_SPACING=0.69
#DWELL_TIME=(140*0.69/1000)=0.0966

mapfile -t todo_ids < "$LIST_FILE"

for i in "${!todo_ids[@]}"; do
  todo_ids[$i]=$(basename "${todo_ids[$i]}")
done
SLURM_ARRAY_TASK_ID=0
# Access the element using the SLURM_ARRAY_TASK_ID
subject_id=${todo_ids[$SLURM_ARRAY_TASK_ID]}
if [ -z "$SESSION" ]; then
    subsesdir=${subject_id}
    subsesname=${subject_id}
else
    subsesdir=${subject_id}/ses-${SESSION}
    subsesname=${subject_id}_ses-${SESSION}
fi

# input variables
anat_folder=${BIDS_FOLDER}/${subsesdir}/anat
dwi_folder=${BIDS_FOLDER}/${subsesdir}/dwi
fmap_folder=${BIDS_FOLDER}/${subsesdir}/fmap

dwi_b0_ap_file=${fmap_folder}/${subsesname}_acq-dwisefm_dir-ap_run-01_epi.nii.gz
dwi_b0_pa_file=${fmap_folder}/${subsesname}_acq-dwisefm_dir-pa_run-01_epi.nii.gz

dwi_ap_file=${dwi_folder}/${subsesname}_dir-ap_run-01_dwi.nii.gz
dwi_pa_file=${dwi_folder}/${subsesname}_dir-pa_run-01_dwi.nii.gz

bval_ap=${dwi_folder}/${subsesname}_dir-ap_run-01_dwi.bval
bval_pa=${dwi_folder}/${subsesname}_dir-pa_run-01_dwi.bval
bvec_ap=${dwi_folder}/${subsesname}_dir-ap_run-01_dwi.bvec
bvec_pa=${dwi_folder}/${subsesname}_dir-pa_run-01_dwi.bvec
t1=${anat_folder}/${subsesname}_run-01_T1w.nii.gz

# output variables
acqparams_file=${FOLDER_OUT}/acqparams.txt
subses_folder_out=${FOLDER_OUT}/${subsesdir}
dwi_folder_out=${subses_folder_out}/dwi
dwi_appa_file=${dwi_folder_out}/${subsesname}_desc-concat-appa_dwi

fmap_folder_out=${subses_folder_out}/fmap
dwi_b0_appa_file=${fmap_folder_out}/${subsesname}_desc-concat-appa-b0_epi
topup_out_files=${fmap_folder_out}/${subsesname}_desc-topup
topup_iout_file=${dwi_folder_out}/${subsesname}_desc-topup-b0ref_dwi
topup_log_original=${fmap_folder_out}/${subsesname}_desc-concat-appa-b0_epi.topup_log
topup_log_bids=${fmap_folder_out}/${subsesname}_desc-concat-appa-b0-topup-log_epi.txt

mean_b0=${dwi_folder_out}/${subsesname}_desc-topup-meanb0_dwi
mean_b0_brain=${dwi_folder_out}/${subsesname}_desc-topup-meanb0-brain_dwi
mean_b0_brain_mask_original=${dwi_folder_out}/${subsesname}_desc-topup-meanb0-brain_dwi_mask
mean_b0_brain_mask_bids=${dwi_folder_out}/${subsesname}_desc-topup-meanb0-brain_mask

index_file=${FOLDER_OUT}/index.txt

bval_appa_file=${dwi_appa_file}.bval
bvec_appa_file=${dwi_appa_file}.bvec

eddy_out_files=${dwi_folder_out}/${subsesname}_desc-eddy
eddy_out_dwi=${eddy_out_files}_dwi

# eddy output renaming array
declare -A renames_eddy=(
    ["${eddy_out_files}-command_dwi.txt"]="${eddy_out_files}_dwi.eddy_command_txt"
    ["${eddy_out_files}-movementrms_dwi.txt"]="${eddy_out_files}_dwi.eddy_movement_rms"
    ["${eddy_out_files}-outlier-free_dwi.nii.gz"]="${eddy_out_files}_dwi.eddy_outlier_free_data.nii.gz"
    ["${eddy_out_files}-outlier-map_dwi.nii.gz"]="${eddy_out_files}_dwi.eddy_outlier_map"
    ["${eddy_out_files}-outlier-map-nsqrstd_dwi.nii.gz"]="${eddy_out_files}_dwi.eddy_outlier_n_sqr_stdev_map"
    ["${eddy_out_files}-outlier-map-nstd_dwi.nii.gz"]="${eddy_out_files}_dwi.eddy_outlier_n_stdev_map"
    ["${eddy_out_files}-outlier-report_dwi.txt"]="${eddy_out_files}_dwi.eddy_outlier_report"
    ["${eddy_out_files}-parameters_dwi.txt"]="${eddy_out_files}_dwi.eddy_parameters"
    ["${eddy_out_files}-shell-alignment_dwi.txt"]="${eddy_out_files}_dwi.eddy_post_eddy_shell_alignment_parameters"
    ["${eddy_out_files}-posteddy-shell-petranslation_dwi.txt"]="${eddy_out_files}_dwi.eddy_post_eddy_shell_PE_translation_parameters"
    ["${eddy_out_files}-movementrms-restricted_dwi.txt"]="${eddy_out_files}_dwi.eddy_restricted_movement_rms"
    ["${eddy_out_files}-rotated_dwi.bvec"]="${eddy_out_files}_dwi.eddy_rotated_bvecs"
    ["${eddy_out_files}-inputparameters_dwi.txt"]="${eddy_out_files}_dwi.eddy_values_of_all_input_parameters"
)

anat_folder_out=${subses_folder_out}/anat
t1w_to_dwi=${anat_folder_out}/${subsesname}_from-T1w_to-dwi_mode-image_xfm.txt
t1w_brain=${anat_folder_out}/${subsesname}_desc-brain_T1w
t1w_brain_mask_original=${anat_folder_out}/${subsesname}_desc-brain_T1w_mask
t1w_brain_mask_bids=${anat_folder_out}/${subsesname}_desc-T1w-brain_mask

t1w_brain_mask_dwi=${anat_folder_out}/${subsesname}_res-dwi_desc-T1w-brain_mask
t1w_brain_mask_dwi_dil=${anat_folder_out}/${subsesname}_res-dwi_desc-T1w-brain-dilated_mask

dtifit_out_files=${dwi_folder_out}/${subsesname}_model-tensor_param

#create folders
mkdir $subses_folder_out -p
mkdir $dwi_folder_out -p
mkdir $fmap_folder_out -p
mkdir $anat_folder_out -p

#####for topup and eddycurrent fsl algorithms: https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy

echo 'Preparing files for topup'
#merge SBREF AP-PA
fslmerge -t ${dwi_b0_appa_file} $dwi_b0_ap_file $dwi_b0_pa_file

# create .txt file with acquisition parameters (AP and PA)
# 0.001*(echo space (ms)*(EPI factor-1) --> 0.001 * 0.69 * (140-1)
if [ ! -f ${acqparams_file} ]; then
  printf "0 -1 0 0.09591\n0 1 0 0.09591" > ${acqparams_file}
fi

echo 'Running topup'
#Run top-up
topup --imain=${dwi_b0_appa_file} --datain=${acqparams_file} --config=b02b0.cnf --out=${topup_out_files} --iout=${topup_iout_file}
mv ${topup_log_original} ${topup_log_bids}

echo 'Preparing files for eddy'
#creating masks on the unwarped (distortion corrected space)-> t_mean of AP and PA corrected singleband b0 volumes
fslmaths ${topup_iout_file} -Tmean ${mean_b0}
bet ${mean_b0} ${mean_b0_brain} -f 0.7 -m
mv ${mean_b0_brain_mask_original}.nii.gz ${mean_b0_brain_mask_bids}.nii.gz

#concatenates DTI (multiband) AP-PA
fslmerge -t ${dwi_appa_file} ${dwi_ap_file} ${dwi_pa_file}

#concatenation order 1->AP and 2->PA
if [ ! -f ${index_file} ]; then
  indx=""	
  for ((i=1; i<=100; i+=1)); do indx="$indx 1"; done
  for ((i=1; i<=100; i+=1)); do indx="$indx 2"; done
  echo $indx > ${index_file}
fi

#concatenates bvals and bvecs AP-PA
paste ${bvec_ap} ${bvec_pa} -d " " >> ${bvec_appa_file}
paste ${bval_ap} ${bval_pa} -d " " >> ${bval_appa_file}

echo 'Eddy correction starts'
#Run eddy
eddy_openmp --imain=${dwi_appa_file} --mask=${mean_b0_brain_mask_bids} --acqp=${acqparams_file} --index=${index_file} --bvecs=${bvec_appa_file} --bvals=${bval_appa_file} --topup=${topup_out_files} --repol --out=${eddy_out_files}
#--repol -> instructs eddy to remove any slices deemed as outliers and replace them with predictions made by the Gaussian Process

#eddy output renaming
for new in "${!renames_eddy[@]}"; do
    old="${renames_eddy[$new]}"
    if [[ -f "$old" ]]; then
        mv "$old" "$new"
    else
        echo "$old file was not found"
    fi
done

#makes brain mask from T1w
flirt -ref ${mean_b0} -in $t1 -omat ${t1w_to_dwi}
bet $t1 ${t1w_brain} -f 0.15 -m -R -B
mv ${t1w_brain_mask_original}.nii.gz ${t1w_brain_mask_bids}.nii.gz
flirt -in ${t1w_brain_mask_bids} -ref ${mean_b0} -applyxfm -init ${t1w_to_dwi} -out ${t1w_brain_mask_dwi}

#T1_brain_mask expansion
fslmaths ${t1w_brain_mask_dwi} -dilD -kernel 3D ${t1w_brain_mask_dwi_dil}

echo 'DTI fit'
#Run dtifit
dtifit -k ${eddy_out_dwi} -o ${dtifit_out_files} -m ${t1w_brain_mask_dwi_dil} -r ${eddy_out_files}-rotated_dwi.bvec -b ${bval_appa_file}

# dtifit output renaming
for old in "${dtifit_out_files}"_??.nii.gz; do
    [[ -f "$old" ]] || continue
    suffix="${old: -7:2}"
    lower_suffix=$(echo "$suffix" | tr 'A-Z' 'a-z')
    new="${dtifit_out_files}-${lower_suffix}_dwimap.nii.gz"
    mv "$old" "$new"
done