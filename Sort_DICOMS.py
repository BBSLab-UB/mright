############################################
########  SCRIPT FOR DICOM SORTING  ########
########      BBSLab Mar 2024       ########
############################################

# import libraries 
import os
from pathlib import Path
import pydicom

# input folder
dicoms_to_order_folder = input(r'Please, enter your DICOM directory: ')
list_subjects=os.listdir(dicoms_to_order_folder)

# check folders and maintain only those which are not ordered. Less than 7 folders per subject AND more than 0 unsorted files?
list_subjects_to_do = [s for s in list_subjects if sum([1 for file in os.listdir(os.path.join(dicoms_to_order_folder, s)) if os.path.isdir(os.path.join(dicoms_to_order_folder, s, file))])<7 and sum([1 for file in os.listdir(os.path.join(dicoms_to_order_folder, s)) if os.path.isfile(os.path.join(dicoms_to_order_folder, s, file))])>0]

print(str(len(list_subjects_to_do))+" out of "+str(len(list_subjects))+" subjects found to be ordered in chosen folder: "+dicoms_to_order_folder)
if len(list_subjects_to_do) != 0:
    print("These subjects are: "+", ".join(list_subjects_to_do))
    
  
# sort
for nSUB in list_subjects_to_do:
    print("Processing subject "+ nSUB+"...")
    subject_folder = os.path.join(dicoms_to_order_folder, nSUB)
    all_files_list = list(Path(subject_folder).glob(r'*.IMA'))
    initial_files = sum([1 for file in os.listdir(subject_folder) if os.path.isfile(os.path.join(subject_folder, file))])   # how much files are in subject_folder

    # dictionary of DICOM tags and folders
    tag2directory = {'*fl2d1': 'Localizer', 
            '*tfl3d1_16ns': 'T1w_MPR',
            '*spc_314ns':'T2w_SPC' ,
            'ep_b1495#12': 'dMRI',
            'epse2d1_140':'dMRI', 
            'ep_b_dMRI':'dMRI',       
            '*tir2d1rs15':'FLAIR',
            'epse2d1_104':'RESTING',    # se field map
            'epfid2d1_104':'RESTING',
            'tgse_mv3d1_2480':'ASL_siemens',
            'mbPCASL2d1_86':'pCASL',
            'epse2d1_86':'pCASL',
            '*fl3d1r_t70':'TOF',
            '*swi3d1r':'SWI'}

    # start with first file, sorted by acquisition time
    all_files_list.sort(key = os.path.getmtime) # sort by date

    while len(all_files_list)>0:    # this list only includes the unsorted files

        this_dicom = pydicom.read_file(all_files_list[0])   # always it reads the first file
        series_n = '%0.4d' % (int(this_dicom.SeriesNumber))
        dicoms_this_series = list(Path(subject_folder).glob(r'*MR.{}.*'.format(series_n))) # list of dicoms with a given series number

        # finds SequenceID for diffusion
        if this_dicom.SequenceName[0:4] == 'ep_b':
            sequence_id = 'ep_b_dMRI'
        else:
            sequence_id = this_dicom.SequenceName   # SequenceID for the rest

        if sequence_id in tag2directory.keys():                
            if not os.path.exists(os.path.join(subject_folder, tag2directory[sequence_id])):    # create subdirectories
               os.makedirs(os.path.join(subject_folder, tag2directory[sequence_id]))
            for this_dicom_path in dicoms_this_series:      # move dicom to subdirectory
                this_dicom_path = str(this_dicom_path)
                new_dicom_path = this_dicom_path.replace(subject_folder, os.path.join(subject_folder, tag2directory[sequence_id]),1)    
                os.rename(this_dicom_path, new_dicom_path)
        
        # same for Sequence_ID not in dictionary
        else:
             if not os.path.exists(os.path.join(subject_folder, r'OTHER')):
                os.makedirs(os.path.join(subject_folder, r'OTHER'))
             for this_dicom_path in dicoms_this_series:
                this_dicom_path = str(this_dicom_path)
                new_dicom_path = this_dicom_path.replace(subject_folder, os.path.join(subject_folder, r'OTHER'),1)    
                os.rename(this_dicom_path, new_dicom_path)
        
        # redefinition of unsorted DICOM list
        all_files_list = list(Path(subject_folder).glob(r'*.IMA'))
        all_files_list.sort(key = os.path.getmtime)
    
    # info: check if all files were sorted
    sorted_files = initial_files - sum([1 for file in os.listdir(subject_folder) if os.path.isfile(os.path.join(subject_folder, file))])
    n_directories = sum([1 for file in os.listdir(subject_folder) if os.path.isdir(os.path.join(subject_folder, file))])
    list_dir = "    ".join([str(item) for item in [d for d in os.listdir(subject_folder) if os.path.isdir(os.path.join(subject_folder, d))]])
    
    if sorted_files == initial_files:
        print(f'Processing of subject {nSUB} successfully done.\n{sorted_files} out of {initial_files} files sorted in {n_directories} directories:\n{list_dir}')
    else:
        print(f'WARNING: Unable to complete processing of subject {nSUB}.\n{sorted_files} out of {initial_files} files sorted in {n_directories} directories:\n{list_dir}')
