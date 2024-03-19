# -*- coding: utf-8 -*-'
import os
import pydicom
import glob


DICOMS_to_order_folder = input('Please, enter your DICOM directory: ')
if DICOMS_to_order_folder[-1] == '/':
    DICOMS_to_order_folder = DICOMS_to_order_folder[:-1]

LIST_SUBJECTS=os.listdir(DICOMS_to_order_folder)

#check folders and maintain only those which are not ordered

LIST_SUBJECTS_TODO = [s for s in LIST_SUBJECTS if sum([1 for file in os.listdir(DICOMS_to_order_folder+"/"+s) if os.path.isdir(DICOMS_to_order_folder+"/"+s+"/"+file)])<7 and sum([1 for file in os.listdir(DICOMS_to_order_folder+"/"+s) if os.path.isfile(DICOMS_to_order_folder+"/"+s+"/"+file)])>0]
 
print(str(len(LIST_SUBJECTS_TODO))+" out of "+str(len(LIST_SUBJECTS))+" subjects found to be ordered in chosen folder: "+DICOMS_to_order_folder)
if len(LIST_SUBJECTS_TODO) != 0:
    print("These subjects are: "+"    ".join(LIST_SUBJECTS_TODO))

#****************************************************************
#************************DO NOT EDIT*****************************
#****************************************************************

for nSUB in LIST_SUBJECTS_TODO:
    print("Processing subject "+ nSUB+"...")
    INPUT_FOLDER=DICOMS_to_order_folder
    DFOLDER=INPUT_FOLDER+'/'+nSUB +'/'
    OUTPUT_FOLDER=DICOMS_to_order_folder+'/'+nSUB+'/'
    filter_files=DFOLDER+'*.IMA' 
    
    initial_files = sum([1 for file in os.listdir(DICOMS_to_order_folder+"/"+nSUB) if os.path.isfile(DICOMS_to_order_folder+"/"+nSUB+"/"+file)])
    #dictionary of DICOM tags and folders
    tag2directory = {'*fl2d1': 'Localizer', 
            '*tfl3d1_16ns': 'T1w_MPR',
            '*spc_314ns':'T2w_SPC' ,
            'ep_b1495#12': 'dMRI',
            'epse2d1_140':'dMRI', 
            'ep_b_dMRI':'dMRI',       
            '*tir2d1rs15':'FLAIR',
            'epse2d1_104':'RESTING', #se field map
            'epfid2d1_104':'RESTING',
            'tgse_mv3d1_2480':'ASL_siemens',
            'mbPCASL2d1_86':'pCASL',
            'epse2d1_86':'pCASL',
            '*fl3d1r_t70':'TOF',
            '*swi3d1r':'SWI'}
    
    #sets counter to 0 for all sequences
    adquisicion_num = tag2directory.copy()
    for seq in adquisicion_num.keys():
        adquisicion_num[seq]=0
    #start with first file
    
    ALL_DICOMS=glob.glob(filter_files) 
    ALL_DICOMS.sort(key=os.path.getmtime) #sort by date
    
    while len(ALL_DICOMS)>0:
        NEXT_DICOM=pydicom.read_file(ALL_DICOMS[0])
        SERIES_NUM = '%0.4d' % (int(NEXT_DICOM.SeriesNumber))
        NEXT_DICOMS= ALL_DICOMS=glob.glob(DFOLDER+'*MR.'+SERIES_NUM+'.*')
        #finds SequenceID for difu
        if NEXT_DICOM.SequenceName[0:4]=='ep_b':
            DicomSequenceName='ep_b_dMRI'
        else:
            DicomSequenceName=NEXT_DICOM.SequenceName
        
        if DicomSequenceName in tag2directory.keys():                
            adquisicion_num[DicomSequenceName]=adquisicion_num[DicomSequenceName]+1 
            if adquisicion_num[DicomSequenceName]>1:
                DIR_APPENDIX=''#'_'+'%0.2d' % (adquisicion_num[DicomSequenceName])
            else:
                DIR_APPENDIX=''     
            if not os.path.exists(OUTPUT_FOLDER+tag2directory[DicomSequenceName]+ DIR_APPENDIX+'/'):
               os.makedirs(OUTPUT_FOLDER+tag2directory[DicomSequenceName]+ DIR_APPENDIX+'/') 
            
            for DICOM2MOVE in NEXT_DICOMS:
                DICOM2MOVE_TO=DICOM2MOVE.replace(DFOLDER, OUTPUT_FOLDER+tag2directory[DicomSequenceName]+ DIR_APPENDIX+'/',1)    
                os.rename(DICOM2MOVE,DICOM2MOVE_TO)
        else:
             if not os.path.exists(OUTPUT_FOLDER+'OTHER/'):
                os.makedirs(OUTPUT_FOLDER+'OTHER/')                
             for DICOM2MOVE in NEXT_DICOMS:
                DICOM2MOVE_TO=DICOM2MOVE.replace(DFOLDER, OUTPUT_FOLDER+'OTHER/',1)
                os.rename(DICOM2MOVE,DICOM2MOVE_TO)
        ALL_DICOMS=glob.glob(filter_files) 
        ALL_DICOMS.sort(key=os.path.getmtime)
    
    sorted_files = initial_files - sum([1 for file in os.listdir(DFOLDER) if os.path.isfile(DFOLDER+file)])
    n_directories = sum([1 for file in os.listdir(DFOLDER) if os.path.isdir(DFOLDER+file)])
    list_dir = "    ".join([str(item) for item in [d for d in os.listdir(DFOLDER) if os.path.isdir(DFOLDER+d)]])
    if sorted_files == initial_files:
        print(f'Processing of subject {nSUB} successfully done.\n{sorted_files} out of {initial_files} files sorted in {n_directories} directories:\n{list_dir}')
    else:
        print(f'WARNING: Unable to complete processing of subject {nSUB}.\n{sorted_files} out of {initial_files} files sorted in {n_directories} directories:\n{list_dir}')
    
