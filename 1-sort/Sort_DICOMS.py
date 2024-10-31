############################################
########  SCRIPT FOR DICOM SORTING  ########
########      BBSLab Mar 2024       ########
############################################

# Import libraries
import os
import sys
from pathlib import Path
import pydicom
from meta import meta_func, meta_create

# Set root directory
root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)

# Create metadata and get DICOM directory path
meta_create()
dicoms_to_order_folder = meta_func("dicom", "your DICOM directory path", msg2=" (add TP folder to path if needed)")
list_subjects = os.listdir(dicoms_to_order_folder)

# Filter subjects to process based on directory constraints (fewer than 7 folders and more than 0 unsorted files)
list_subjects_to_do = [
    s for s in list_subjects
    if sum([
        1 for file in os.listdir(os.path.join(dicoms_to_order_folder, s))
        if os.path.isdir(os.path.join(dicoms_to_order_folder, s, file))
    ]) < 7 and sum([
        1 for file in os.listdir(os.path.join(dicoms_to_order_folder, s))
        if os.path.isfile(os.path.join(dicoms_to_order_folder, s, file))
    ]) > 0
]

# Print summary of subjects to process
print(
    f"{len(list_subjects_to_do)} out of {len(list_subjects)} subjects will be sorted in chosen folder: {dicoms_to_order_folder}"
)
if list_subjects_to_do:
    print("These subjects are: " + ", ".join(list_subjects_to_do))

# Sort DICOM files
for nSUB in list_subjects_to_do:
    print(f"Processing subject {nSUB}...")
    subject_folder = os.path.join(dicoms_to_order_folder, nSUB)
    
    # List of all DICOM files
    all_files_list = list(Path(subject_folder).glob(r'*.IMA'))
    
    # Initial count of files
    initial_files = sum([
        1 for file in os.listdir(subject_folder)
        if os.path.isfile(os.path.join(subject_folder, file))
    ])

    # Map for DICOM tags and directories
    tag2directory = {
        '*fl2d1': 'Localizer',
        '*tfl3d1_16ns': 'T1w_MPR',
        '*spc_314ns': 'T2w_SPC',
        'ep_b1495#12': 'dMRI',
        'epse2d1_140': 'dMRI',
        'ep_b_dMRI': 'dMRI',
        '*tir2d1rs15': 'FLAIR',
        'epse2d1_104': 'RESTING',
        'epfid2d1_104': 'RESTING',
        'tgse_mv3d1_2480': 'ASL_siemens',
        'mbPCASL2d1_86': 'pCASL',
        'epse2d1_86': 'pCASL',
        '*fl3d1r_t70': 'TOF',
        '*swi3d1r': 'SWI'
    }

    # Sort files by acquisition time
    all_files_list.sort(key=os.path.getmtime)

    while all_files_list:
        # Read the first DICOM file
        this_dicom = pydicom.dcmread(all_files_list[0])
        series_n = '%0.4d' % int(this_dicom.SeriesNumber)

        # List of DICOMs with a given series number
        dicoms_this_series = list(Path(subject_folder).glob(rf'*MR.{series_n}.*'))

        # Determine sequence ID for diffusion
        if this_dicom.SequenceName[0:4] == 'ep_b':
            sequence_id = 'ep_b_dMRI'
        else:
            sequence_id = this_dicom.SequenceName # SequenceID for the rest

        # Move files to respective directories
        if sequence_id in tag2directory.keys():
            if not os.path.exists(os.path.join(subject_folder, tag2directory[sequence_id])):  
                os.makedirs(os.path.join(subject_folder, tag2directory[sequence_id]))
            for this_dicom_path in dicoms_this_series: # Move dicom to subdirectory
                this_dicom_path = str(this_dicom_path)
                new_dicom_path = this_dicom_path.replace(subject_folder, os.path.join(subject_folder, tag2directory[sequence_id]), 1)
                os.rename(this_dicom_path, new_dicom_path)

        # Same for Sequence_ID not in dictionary
        else:
            if not os.path.exists(os.path.join(subject_folder, r'OTHER')):
                os.makedirs(os.path.join(subject_folder, r'OTHER'))
            for this_dicom_path in dicoms_this_series:
                this_dicom_path = str(this_dicom_path)
                new_dicom_path = this_dicom_path.replace(subject_folder, os.path.join(subject_folder, r'OTHER'), 1)
                os.rename(this_dicom_path, new_dicom_path)

        # Redefine unsorted DICOM list and sort
        all_files_list = list(Path(subject_folder).glob(r'*.IMA'))
        all_files_list.sort(key=os.path.getmtime)

    # Info: Check if all files were sorted
    sorted_files = initial_files - sum([
        1 for file in os.listdir(subject_folder)
        if os.path.isfile(os.path.join(subject_folder, file))
    ])
    n_directories = sum([
        1 for file in os.listdir(subject_folder)
        if os.path.isdir(os.path.join(subject_folder, file))
    ])
    list_dir = "    ".join([
        str(item) for item in os.listdir(subject_folder)
        if os.path.isdir(os.path.join(subject_folder, item))
    ])

    # Output result of processing
    if sorted_files == initial_files:
        print(
            f"Processing of subject {nSUB} successfully done.\n"
            f"{sorted_files} out of {initial_files} files sorted in {n_directories} directories:\n{list_dir}"
        )
    else:
        print(
            f"WARNING: Unable to complete processing of subject {nSUB}.\n"
            f"{sorted_files} out of {initial_files} files sorted in {n_directories} directories:\n{list_dir}"
        )