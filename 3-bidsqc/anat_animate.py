#!/usr/bin/env python3
# -*- coding: utf-8 -*-

############################################
#######  T1/T2 GIF GENERATOR FOR QC  #######
#######       BBSLab Jun 2024        #######
############################################

# import libraries
import nibabel as nib
from PIL import Image
import numpy as np
import os
import pandas as pd
from datetime import datetime
import sys

root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)
from meta import meta_func

# input paths
bids_path = bids_path = meta_func("bids_out", "your BIDS directory path (from the shared folder)")      # /institut directory
qc_path = meta_func("qc", "your QC directory path") 
ses = meta_func("ses", "your session label", ispath=False)

if ses == "NOSESSION":
    seslabel = ""
    seslabel_dash = ""
else:
    seslabel = "ses-{}".format(ses)
    seslabel_dash = "ses-{}_".format(ses)
    
# PLOTTING ORDER: X,Y,Z; sagital, coronal, axial

# root_out: QC folder

def anat_gif(root_in, root_out, sub, run, img_type):
    '''This function generates a gif for xyz axes. It accepts T1 and T2 images'''
    notpossible_txtpath = os.path.join(root_out, seslabel, img_type, seslabel_dash+img_type+"_notpossible_QC.txt")
    try:
        # NIfTI read as an array
        anat_array = np.array(nib.load(os.path.join(root_in, sub, seslabel, "anat", sub+"_"+seslabel_dash+"run-"+run+"_"+img_type+"w.nii.gz")).get_fdata())
    except:
        print(sub+"!! Not possible")
        with open(notpossible_txtpath,"a") as f:
            if os.path.exists(notpossible_txtpath) == False: f.write("timestamp,sub,run,message")
            f.write(str(datetime.now())+","+sub+",run-"+run+",cannot open\n")
        return 0
    try:
        # GIF generation
        multiplier = int(img_type[1]) #== T1 = 1, T2= 2
        anat_im =  Image.fromarray(anat_array[1,:,:]*multiplier/20).rotate(90, expand=1)
    
        sagital = [Image.fromarray(anat_array[i,:,:]*multiplier/20).rotate(90, expand=1) for i in range(anat_array.shape[0])]
        coronal = [Image.fromarray(anat_array[:,i,:]*multiplier/20).rotate(90, expand=1) for i in range(anat_array.shape[1])]
        axial   = [Image.fromarray(anat_array[:,:,i]*multiplier/20).rotate(90, expand=1) for i in range(anat_array.shape[2])]
        
        images=sagital+coronal+axial
    except:
        print(sub+"!! Not possible")
        with open(notpossible_txtpath,"a") as f:
            if os.path.exists(notpossible_txtpath) == False: f.write("timestamp,sub,run,message")
            f.write(str(datetime.now())+","+sub+",run-"+run+",cannot create gif\n")
        return 0
    try:
        # Saving GIF
        anat_im.save(os.path.join(root_out, seslabel, img_type, "gifs", sub+"_"+seslabel_dash+"run-"+run+"_"+img_type+".gif"), duration=70, save_all=True, append_images=images, loop=0)
        print(sub + ", run-"+run+ ", " + img_type + " gif was correctly generated") # X out of Y done
    except:
        print(sub+"!! Not possible")
        with open(notpossible_txtpath,"a") as f:
            if os.path.exists(notpossible_txtpath) == False: f.write("timestamp,sub,run,message")
            f.write(str(datetime.now())+","+sub+",run-"+run+",cannot save gif\n")
        return 0    

# list of subjects for this session
subjects_ls = os.listdir(bids_path)
subjects = [sub for sub in subjects_ls if sub[:4]=="sub-" and os.path.isdir(os.path.join(bids_path, sub, seslabel))]

# load newest  version of inventory [ses-XX_]dicoms_bids_inventory_YYYY-MM-DD.txt
newest_inv = sorted([inv for inv in os.listdir(os.path.join(qc_path, seslabel)) if "_dicoms_bids_inventory_" in inv])[-1]
inventory_df=pd.read_csv(os.path.join(qc_path, seslabel, newest_inv), sep=",")
inventory_df.columns=sorted(inventory_df.columns.str.replace('id_user',''),key=lambda x : x=='')
inventory_df = inventory_df.drop(inventory_df.columns[-1], axis=1)

def qc_exec(img_type):
    '''This function selects the subjects and runs to animate'''
    gifs_path = os.path.join(qc_path, seslabel, img_type, 'gifs')
    print('-----------')
    print('Now trying to animate {} images. Output will be saved at: {}'.format(img_type, gifs_path))
    
    # create directories
    if os.path.exists(os.path.dirname(gifs_path)) == False: os.mkdir(os.path.dirname(gifs_path))
    if os.path.exists(gifs_path) == False: os.mkdir(gifs_path)
    
    # selection of the pending runs
    for sub in subjects:
        n_runs = inventory_df.loc[sub,"Bids_anat_"+img_type]   
        print(n_runs, img_type, "runs detected for", sub)
        list_runs = ["%.2d" % int(i) for i in range(n_runs+1)][1:]
        
        # run will be excluded if it is found in 1. QC TXT file or 2. gifs folder
        qc_txt_path = os.path.join(qc_path, seslabel, img_type, seslabel_dash+img_type+"_QC.txt")
        if os.path.exists(qc_txt_path):
            qc_df = pd.read_csv(qc_txt_path)
            qc_sub_df = qc_df[qc_df.subject==int(sub[4:])]
            list_runs_txt = ["%.2d" % int(i) for i in qc_sub_df.run]
        else:
            list_runs_txt = []
        gifs_this_sub = [gif for gif in os.listdir(gifs_path) if sub in gif]
        list_runs_folder = [gif.partition("run-")[2].partition("_")[0] for gif in gifs_this_sub]
        
        for run in list_runs:
            if run in list_runs_folder and list_runs_txt:
                print("run "+run+" already in txt file and gifs folder")
            elif run in list_runs_folder:
                print("run "+run+" already in gifs folder")
            elif run in list_runs_txt:
                print("run "+run+" already in txt file")
            else:
                print('Animating gif for {} and run {}'.format(sub, run))
                anat_gif(bids_path, qc_path, sub, run, img_type)
            print('-----------')

qc_exec("T1")
qc_exec("T2")

