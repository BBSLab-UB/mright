############################################
#  SCRIPT FOR DICOM SORTING - XA60 UPDATED #
#             BBSLab Oct 2025              #
############################################

# Import libraries
import shutil
import os
import sys
from pathlib import Path
import pydicom

# Define functions
def flatten_sub(root: Path):
    root = Path(root).resolve()
    changed = False

    def get_dir_indices(path: Path):
        """
        For a given file path, return a list of numeric indices representing
        the alphabetical position of each folder *only* if its parent
        contains multiple subdirectories.
        """
        rel_parts = path.relative_to(root).parts[:-1]  # exclude filename
        indices = []
        current = root

        for part in rel_parts:
            subdirs = sorted([p.name for p in current.iterdir() if p.is_dir()])
            if len(subdirs) > 1:  # only assign index if multiple siblings
                idx = subdirs.index(part)
                indices.append(idx)
            current = current / part

        return indices

    # Move all files to root with renaming
    for path in sorted(root.rglob('*')):
        if not path.is_file():
            continue
        if path.parent == root:
            continue  # already in root

        indices = get_dir_indices(path)
        prefix = '_'.join(map(str, indices)) + '_' if indices else ''
        new_name = prefix + path.name
        dest = root / new_name

        # Avoid name collisions
        count = 1
        while dest.exists():
            dest = root / f"{prefix}{count}_{path.name}"
            count += 1

        shutil.move(str(path), dest)
        changed = True

    # Remove empty dirs (bottom-up)
    for dir_path in sorted(root.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            dir_path.rmdir()
            changed = True
    
    if changed:
        print(f"INFO: {root.resolve()} directory was flattened before sorting")

def get_sequence_name(dcminfo):
    if dcminfo.get([0x18, 0x24]):
        # Siemens E11
        sequence_name = dcminfo[0x18, 0x24].value
    elif dcminfo.get([0x18, 0x9005]):
        # Siemens XA
        sequence_name = dcminfo[0x18, 0x9005].value
    else:
        sequence_name = ""

    return sequence_name

# Set root directory
root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)
from meta import meta_func, meta_create

# Create metadata and get DICOM directory path
meta_create()
dicoms_path = meta_func("dicom", "the path to the DICOMs folder")  # Path to DICOM directories
timepoint = meta_func("timepoint", "the name of the timepoint folder (e.g., 'TP2')") # Name of timepoint folder

# Map for DICOM tags and directories
tag2directory = {
    '*fl2d1': 'Localizer',
    '*tfl3d1_16ns': 'T1w_MPR',
    '*tfl3d1_256ns': 'T1w_MPR',
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

# Combine the DICOM path and the timepoint
dicoms_to_order_folder = os.path.join(dicoms_path, timepoint)
list_subjects = os.listdir(dicoms_to_order_folder)

# Filter subjects to process based on the file structure
list_subjects_to_do = [
    subfolder.name for subfolder in Path(dicoms_to_order_folder).iterdir()
    if subfolder.is_dir()
    and (
        any(f.is_file() for f in subfolder.iterdir())  # are there unsorted files directly in the sub folders?
        or any(
            f.is_file() and len(f.relative_to(subfolder).parts) >= 3  # aren't files in second-level folders?
            for f in subfolder.rglob('*')
        )
    )
    and not any(seq_folder.name == "T1w_MPR" for seq_folder in subfolder.rglob('*') if seq_folder.is_dir())  # isn't there a T1 folder?
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
        
    flatten_sub(subject_folder)

    others_folder = os.path.join(subject_folder, r'OTHER')

    if not os.path.exists(others_folder):
        os.makedirs(others_folder)
    if os.path.exists(os.path.join(subject_folder, 'DICOMDIR')):
        os.rename(os.path.join(subject_folder, 'DICOMDIR'), os.path.join(others_folder, 'DICOMDIR'))
    if os.path.exists(os.path.join(subject_folder, 'DICOM')):
        shutil.rmtree(os.path.join(subject_folder, 'DICOM'))

    # List of all DICOM files
    all_files_list = [f for f in Path(subject_folder).glob('*') if f.is_file()]
    
    # Initial count of files
    initial_files = sum([
        1 for file in os.listdir(subject_folder)
        if os.path.isfile(os.path.join(subject_folder, file))
    ])

    # Sort files by acquisition time
    all_files_list.sort(key=os.path.getmtime)

    while all_files_list:
        # Read the first DICOM file
        this_dicom = pydicom.dcmread(all_files_list[0])

        if this_dicom.Modality != 'MR':
            if not os.path.exists(others_folder):
                os.makedirs(others_folder)
            os.rename(all_files_list[0], os.path.join(others_folder, all_files_list[0].name))
            # Redefine unsorted DICOM list and sort
            all_files_list = [f for f in Path(subject_folder).glob('*') if f.is_file()]
            all_files_list.sort(key=os.path.getmtime)
            continue

        sequence_name = get_sequence_name(this_dicom)
        # Determine sequence ID for diffusion
        if sequence_name[0:4] == 'ep_b':
            sequence_id = 'ep_b_dMRI'
        else:
            sequence_id = sequence_name # SequenceID for the rest

        # Move files to respective directories
        if sequence_id in tag2directory.keys():
            if not os.path.exists(os.path.join(subject_folder, tag2directory[sequence_id])):  
                os.makedirs(os.path.join(subject_folder, tag2directory[sequence_id]))
            this_dicom_path = str(all_files_list[0])
            new_dicom_path = this_dicom_path.replace(subject_folder, os.path.join(subject_folder, tag2directory[sequence_id]), 1)
            os.rename(this_dicom_path, new_dicom_path)

        # Same for Sequence_ID not in dictionary
        else:
            if not os.path.exists(others_folder):
                os.makedirs(others_folder)
            this_dicom_path = str(all_files_list[0])
            new_dicom_path = this_dicom_path.replace(subject_folder, others_folder, 1)
            os.rename(this_dicom_path, new_dicom_path)

        # Redefine unsorted DICOM list and sort
        all_files_list = [f for f in Path(subject_folder).glob('*') if f.is_file()]
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