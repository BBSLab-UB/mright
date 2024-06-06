#!/usr/bin/env python3
# -*- coding: utf-8 -*-

############################################
####  DICOM AND BIDS INVENTORY SCRIPT   ####
####          BBSLab Jun 2024           ####
############################################

# import libraries
import os
import datetime
import csv
import sys

root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)
from meta import meta_func, meta_create

# input paths
meta_create()
dicoms_path = meta_func("dicom", "your DICOM directory path", msg2=" (add TP folder to path if needed)")                            # /institut directory
bids_path = meta_func("bids_out", "your BIDS directory path (from the shared folder)")                                              # /institut directory
recons_path = meta_func("recons", "your recon_all directory path", msg2=" (press Enter if it does not exist)")                      # /institut directory, won't be BIDS-compliant, MRI/derivatives/<recons>/sub-XXXX[_ses-XX]
processed_path = meta_func("bold", "your BOLD preprocessed images directory path", msg2=" (press Enter if it does not exist)")      # /institut directory
qc_folder = meta_func("qc", "your QC output directory path")                                                                        # /laboratori directory
ses = meta_func("ses", "your session label", ispath=False)

if ses == "NOSESSION":
    seslabel = ""
    seslabel_dash = ""
else:
    seslabel = "ses-{}".format(ses)
    seslabel_dash = "ses-{}_".format(ses)
    
# other paths
today = str(datetime.date.today())
output_path = os.path.join(qc_folder, seslabel, seslabel_dash+'dicoms_bids_inventory_'+today+'.csv')

# list of subs for each path
bids_ls = os.listdir(bids_path)
bids = [sub for sub in bids_ls if "sub-" in sub and os.path.isdir(os.path.join(bids_path, sub, seslabel))]   # subs that have bids for this session

dicoms_ls = os.listdir(dicoms_path)
dicoms = ["sub-" + sub for sub in dicoms_ls if (not sub in ["._.DS_Store", ".DS_Store"])]    # subs that have dicoms of this session

recons_ls = os.listdir(recons_path)
recons = [sub for sub in recons_ls if (not sub in ["._.DS_Store", ".DS_Store"] and (not "_" in sub) and "sub-" in sub and seslabel in sub)] # if session exists

processed_ls = os.listdir(processed_path)
mni    = [sub for sub in processed_ls if os.path.isfile(os.path.join(processed_path, sub, seslabel, 'func', 'MNI_2mm', sub+'_'+seslabel_dash+"task-rest_dir-ap_run-{item:02d}_bold_MNI-space.nii.gz"))] 
native = [sub for sub in processed_ls if os.path.isfile(os.path.join(processed_path, sub, seslabel, 'func', 'native_T1', sub+'_'+seslabel_dash+"task-rest_dir-ap_run-{item:02d}_bold_T1-space.nii.gz"))] 

# check if MNI == Native
mni_notnative = list(set(mni).difference(set(native)))
native_notmni = list(set(native).difference(set(mni)))
if len(mni_notnative) != 0:
    print('WARNING: Subjects {} have preprocessed images in MNI space but not in the native one. These images will be omitted.'.format(mni_notnative))
elif len(native_notmni) != 0:
    print('WARNING: Subjects {} have preprocessed images in the native space but not in the MNI one. These images will be omitted.'.format(native_notmni))

# check if all subjects have DICOMS and BIDS
all_subjects = list(set(dicoms).union(set(bids), set(recons), set(mni), set(native)))
notbids = list(set(all_subjects).difference(set(bids)))
notdicoms = list(set(all_subjects).difference(set(dicoms)))
if len(notbids) > 0:
    print("WARNING: Subjects {} do not have BIDS images. Check if the conversion was done and the given path is correct".format(notbids))
elif len(notdicoms) > 0:
    print("WARNING: Subjects {} do not have DICOM images. Check if the DICOMS were not removed and the given path is correct".format(notdicoms))

# dictionary splits subs by bids type 
subs_by_bidstype = {}
bidstypes = ['anat', 'func', 'dwi', 'perf', 'fmap', 'swi']
for bidstype in bidstypes:
    subs_this_bidstype = [sub for sub in bids if os.path.isdir(os.path.join(bids_path, sub, seslabel, bidstype))]
    subs_by_bidstype[bidstype] = subs_this_bidstype
#subs_by_bidstype will be = {'anat': ['sub-1', 'sub-2',...],
#                           'func':  ['sub-2', 'sub-4', 'sub-5',...],
#                           ...}
    
# headers of the csv output
header_list = ['id_user', 'Dicom', 'Dicom_resting', 'Dicom_T1', 'Dicom_T2', 'Dicom_pCASL',
               'Bids', 'Bids_func', 'Bids_func_bold', 'Bids_func_sbref',
               'Bids_anat', 'Bids_anat_T1', 'Bids_anat_T2', 'Bids_anat_FLAIR',
               'Bids_SWI','Bids_SWI_comb', 'Bids_SWI_mag', 'Bids_SWI_mIP', 'Bids_SWI_phase',
               'Bids_dwi', 'Bids_dwi_dir_ap_bval', 'Bids_dwi_dir_ap_bvec', 'Bids_dwi_dir_ap', 'Bids_dwi_dir_pa_bval', 'Bids_dwi_dir_pa_bvec', 'Bids_dwi_dir_pa',
               'Bids_perf', 'Bids_perf_pCASL_ap', 'Bids_perf_pCASL_pa',
               'Bids_fmap','Bids_func_sefm_ap', 'Bids_func_sefm_pa', 'Bids_dwi_sefm_ap', 'Bids_dwi_sefm_pa', 'Bids_perf_pCASL_sefm_ap', 'Bids_perf_pCASL_sefm_pa',
               'recon_all',
               'preprocessed_bold']

bids_header_list = [bids_header for bids_header in header_list if 'Bids' in bids_header] # only bids-related headers

# functions
def simple_write(file, path):
    '''This function writes 1 for non-empty existing directories,
    and 0 for the rest'''
    if os.path.isdir(path):
        file.write("1,")
        if len(os.listdir(path)) == 0:
            print("WARNING: Folder {} is empty!!".format(path))
    else:
        file.write("0,")

# file substrings for each file type in each subdirectory        
subdirs_dict = {'anat': ["T1", "T2", "FLAIR"],
                'swi':  ["mag_GRE", "phase_GRE", "swi", "minIP"],
                'func': ["bold", "sbref"],
                'dwi':  [["ap", "dwi.bval"], ["ap", "dwi.bvec"], ["ap", "dwi.nii"], ["pa", "dwi.bval"], ["pa", "dwi.bvec"], ["pa", "dwi.nii"]],
                'perf': ["pcasl_dir-ap", "pcasl_dir-pa"],
                'fmap': ["restsefm_dir-ap", "restsefm_dir-pa", "dwisefm_dir-ap", "dwisefm_dir-pa", "pcaslsefm_dir-ap", "pcaslsefm_dir-pa"]
                }
  
def bids_write(file, bidstype):
    '''Write 0 or 1 function for BIDS folder and subfolders'''
    substring_list = subdirs_dict[bidstype]
    if sub in subs_by_bidstype[bidstype]: #the sub has this BIDS type
        file.write("1,")
        bidstype_path = os.path.join(bids_path, sub, seslabel, bidstype)
        if len(os.listdir(bidstype_path)) == 0:
            print("WARNING: Folder {} is empty!!".format(bidstype_path))
        files_this_bidstype = os.listdir(bidstype_path) # files in sub for this bids type
        if bidstype == "dwi": #DWI files need 2 substrings for the detection
            for two_substrings in substring_list:
                file.write(str(int(sum([1 for file2 in files_this_bidstype if all(substring in file2 for substring in two_substrings)])))+",") # dwi files need 2 substring conditions
        else:
            for substring in substring_list:
                file.write(str(int(sum([1 for file2 in files_this_bidstype if substring in file2])/2))+",")
    else:
        file.write("0," * (len(substring_list)+1))

if os.path.isdir(os.path.dirname(output_path)) == False: os.mkdir(os.path.dirname(output_path)) 

#writing the CSV    
with open(output_path, 'w') as f:
    writer = csv.writer(f)
    writer.writerow(header_list)    #write header row
    print("There are {} subjects.".format(len(all_subjects)))
    i = 1
    for sub in all_subjects:
        print("Now writing subject {} in {}. {} subject(s) left".format(sub, output_path, len(all_subjects)-i))
        f.write(sub+",")
        
        # DICOMS
        simple_write(f, os.path.join(dicoms_path, sub[4:]))     #there is a DICOM folder for this subject and session
        simple_write(f, os.path.join(dicoms_path, sub[4:], "RESTING"))
        simple_write(f, os.path.join(dicoms_path, sub[4:], "T1w_MPR"))
        simple_write(f, os.path.join(dicoms_path, sub[4:], "T2w_SPC"))
        simple_write(f, os.path.join(dicoms_path, sub[4:], "pCASL"))
        
        # BIDS    
        if sub in bids:     # there is a BIDS folder for this subject and session
            f.write("1,")
            bids_write(f, 'func')
            bids_write(f, 'anat')
            bids_write(f, 'swi')
            bids_write(f, 'dwi')
            bids_write(f, 'perf')
            bids_write(f, 'fmap')
        else:
            f.write("0," * len(bids_header_list))
        
        # recon-all
        simple_write(f,os.path.join(recons_path,sub + "_"+seslabel))
        
        # bold preprocessed
        if (sub in mni) and (sub in native):
            f.write("1,")
        else:
            f.write("0,")
        
        f.write("\n")
        i = i+1
