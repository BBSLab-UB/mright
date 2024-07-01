############################################
##########  DICOM TO BIDS SCRIPT  ##########
##########    BBSLab Mar 2024     ##########
############################################

# import libraries
import os
import sys
import datetime
import shutil
import re

root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)
from meta import meta_func, meta_create

# input paths
meta_create()
dicoms_path = meta_func("dicom", "your DICOM directory path", msg2=" (add TP folder to path if needed)") # /institut directory
dicoms_list_txt = meta_func("dicom_list", "your list of DICOMS file path")                               # copy subjects folders to a .txt --> a subject folder path or ID per line
bids_path = meta_func("bids_in", "your BIDS destination directory path")                                 # recommended: local folder at /home, folder must be created before running the script
heuristic_file_path = meta_func("heuristic", "your heuristic file path")
ses = meta_func("ses", "your session label", ispath=False)

#delete optional files?
delete_optional = True

if ses == "NOSESSION":
    use_sessions = False
else:
    use_sessions = True

#selecting DICOMS from list
def get_dicoms_in_list(dicoms_list):
    with open(dicoms_list) as file:
        list_of_dicoms = []
        for dicom_id_path in file:
            dicom_id_path = dicom_id_path.rstrip()
            if dicom_id_path[-1] == "/":
                dicom_id_path = dicom_id_path[:-1]
            dicom_id = os.path.basename(dicom_id_path)
            list_of_dicoms.append(dicom_id)
    return list_of_dicoms
dicoms_in_list = get_dicoms_in_list(dicoms_list_txt)

# list of DICOMS in input directory
dicoms_in_dir = [s for s in os.listdir(dicoms_path)]

# is there any difference?
list_minus_dir = set(dicoms_in_list).difference(dicoms_in_dir)
if (list_minus_dir != set()) is True:                                           # Some subject not in dicoms_path
    print(f"WARNING: {str(list_minus_dir)} subject(s) not in source directory")
    with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:        # error log
        f.write(str(datetime.datetime.now()) + "\t" + str(list_minus_dir) +
                " subject(s) not in source directory\n")
    dicoms_in_list = list(set(dicoms_in_list).difference(list_minus_dir))       # missing subjects are skipped

# is there any BIDS already in the bids_path? Is there any conflict? Do you want to overwrite?
if use_sessions == True:
    ses_path ="ses-{}".format(ses)    
    bids = [s[4:] for s in os.listdir(bids_path) if ((s[:4] == "sub-") and os.path.isdir(os.path.join(bids_path, s, ses_path)) and (os.listdir(os.path.join(bids_path, s)) != []))]

else:
    bids = [s[4:] for s in os.listdir(bids_path) if ((s[:4] == "sub-") and (os.listdir(os.path.join(bids_path, s)) != []))]

dicoms_in_list_clean = [] #subs with only alphanumeric characters (BIDS standard matching)

for sub in dicoms_in_list:
    sub_clean = re.sub(r'[^a-zA-Z0-9]', '', sub)
    dicoms_in_list_clean.append(sub_clean)
intersection_bids_list = set(dicoms_in_list_clean).intersection(bids)

if intersection_bids_list == set():                                             # If there isn't any subject in both list and bids_path
    todo_dicoms = dicoms_in_list

while (intersection_bids_list != set()) is True:                                # Some subject is both in list and bids_path
    overwrite_bids = input(str(intersection_bids_list) +
                           " already in BIDS directory, do you want to overwrite? (Y/N) ").upper()
    if overwrite_bids == "N":                                                  # No overwriting: todo_dicoms = dicoms in list not in bids_path
        todo_dicoms = []
        for sub in dicoms_in_list:
            sub_clean = re.sub(r'[^a-zA-Z0-9]', '', sub)
            if sub_clean not in bids:
                todo_dicoms.append(sub)
        print("Overwriting of " + str(intersection_bids_list) + " was skipped.")
        intersection_bids_list = set()
        
    elif overwrite_bids == "Y":                                                # Overwriting: delete BIDS in conflict, convert the entire list
        if use_sessions == True:
            for dicom_id in dicoms_in_list_clean:
                if os.path.exists(os.path.join(bids_path, "sub-{}".format(dicom_id), ses_path)):
                    shutil.rmtree(os.path.join(bids_path, "sub-{}".format(dicom_id), ses_path))
                    print("INFO: " + os.path.join(bids_path, "sub-{}".format(dicom_id), ses_path) + " will be overwritten.")
                if os.path.exists(os.path.join(bids_path, ".heudiconv", dicom_id, ses_path)):
                    shutil.rmtree(os.path.join(bids_path, ".heudiconv", dicom_id, ses_path))
                    print("INFO: " + os.path.join(bids_path, ".heudiconv", dicom_id, ses_path) + " will be overwritten.")
        
        else:            
            for dicom_id in dicoms_in_list_clean:
                if os.path.exists(os.path.join(bids_path, "sub-{}".format(dicom_id))):
                    shutil.rmtree(os.path.join(bids_path, "sub-{}".format(dicom_id)))
                    print("INFO: " + os.path.join(bids_path, "sub-{}".format(dicom_id)) + " will be overwritten.")
                if os.path.exists(os.path.join(bids_path, ".heudiconv", dicom_id)):
                    shutil.rmtree(os.path.join(bids_path, ".heudiconv", dicom_id))
                    print("INFO: " + os.path.join(bids_path, ".heudiconv", dicom_id) + " will be overwritten.")                    
        todo_dicoms = dicoms_in_list
        intersection_bids_list = set()
    
    else:
        print("Please, enter a valid response.\n")                              # can't exit loop if Y/N is not entered


# heudiconv run

for subj in todo_dicoms:
    
    try:
        subj_clean = re.sub(r'[^a-zA-Z0-9]', '', subj)
        subj_path = os.path.join(bids_path, "sub-{}".format(subj_clean))
        if os.path.exists(subj_path) == False: os.mkdir(subj_path) # create  sub- path 
        subdir_list = [subdir for subdir in os.listdir(subj_path) if os.path.isdir(os.path.join(subj_path , subdir))]
        
        # for longitudinal studies
        # heuristic must have keys like t1w=create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:02d}_T1w')
        if use_sessions == True:
                    
        # ses- check: Subj folder must be empty or contain ONLY ses- subfolders
            if subdir_list:
                subdir_check = [ses_subdir for ses_subdir in subdir_list if "ses-" in ses_subdir[:4]]
                if subdir_check != subdir_list:
                    with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:
                        print("WARNING: Subject {} has been skipped because it lacks session hierarchy, despite a session was inputed. Issue logged in error_heudiconv.txt".format(subj))
                        f.write(str(datetime.datetime.now()) + "\t" + subj + " session inputed, but there is no previous session hierarchy\n")
                    continue
            if not ses_path in os.listdir(subj_path):
                print("Starting subject {} conversion".format(subj))
                command = "heudiconv -d "+ os.path.join(dicoms_path,"{subject}","*","*.IMA") + " -o "+ bids_path +" -f "+ heuristic_file_path +" -s "+ subj + " -ss "+ ses +" -c dcm2niix -b --minmeta --overwrite --grouping custom"
                os.system(command)
            else:                                                                   # this should not happen, todo_dicoms subjects are never in bids_path previously
                with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:
                    print("WARNING: Subject {} has been processed before and you chose to not overwrite. Subject will be skipped. Issue logged in error_heudiconv.txt".format(subj))
                    f.write(str(datetime.datetime.now()) + "\t" + subj + " already processed\n")
       
        # for NON-longitudinal studies
        # heuristic must have keys like t1w=create_key('sub-{subject}/anat/sub-{subject}_run-{item:02d}_T1w')        
        else:
            
            # ses- check: Subj folder must be empty or contain ONLY ses- subfolders
            if subdir_list:
                subdir_check = [ses_subdir for ses_subdir in subdir_list if "ses-" not in ses_subdir[:4]]
                if subdir_check != subdir_list:
                    with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:
                        print("WARNING: Subject {} has been skipped because it has session hierarchy, despite no session was inputed. Issue logged in error_heudiconv.txt".format(subj))
                        f.write(str(datetime.datetime.now()) + "\t" +subj + " session not inputed, but there is previous session hierarchy\n")
                    continue
            if ("sub-{}".format(subj_clean) not in os.listdir(bids_path)) or (subdir_list == []):
                print("Starting subject {} conversion".format(subj))
                command = "heudiconv -d "+ os.path.join(dicoms_path,"{subject}","*","*.IMA") + " -o "+ bids_path +" -f "+ heuristic_file_path +" -s "+ subj +" -c dcm2niix -b --minmeta --overwrite --grouping custom"
                os.system(command)
            else:                                                                   # this should not happen, todo_dicoms subjects are never in bids_path previously
                with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:
                    print("WARNING: Subject {} has been processed before and you chose to not overwrite. Subject will be skipped. Issue logged in error_heudiconv.txt".format(subj))
                    f.write(str(datetime.datetime.now()) + "\t" + subj + " already processed\n")
    
    except:                                                                     # this could happen, especially if the script is run on Windows
        with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:
            print("WARNING: Unable to process subject {}. Subject will be skipped. Issue logged in error_heudiconv.txt".format(subj))
            f.write(str(datetime.datetime.now()) + "\t" + subj + " error\n")
        continue

# .bidsignore file in case error_heudiconv.txt is created
if os.path.exists(os.path.join(bids_path, "error_heudiconv.txt")) == True:
    if os.path.exists(os.path.join(bids_path, ".bidsignore")) == False:
        with open(os.path.join(bids_path, ".bidsignore"), "a") as f:
                    f.write("error_heudiconv.txt\n")
    else:
        with open(os.path.join(bids_path, ".bidsignore"), "r+") as f:
            lines = {line.rstrip() for line in f}
            if "error_heudiconv.txt" not in lines:
                f.write("\nerror_heudiconv.txt\n")   

# delete scans.tsv and events.tsv optional files                  
if delete_optional == True:
    if use_sessions == True:
        subses_path = "ses-*"
    else:
        subses_path = ""
    subses_path = os.path.join(bids_path, "sub-*", ses_path)
    cmd_remove = "rm " + os.path.join(subses_path, "*_scans.tsv") + " && rm " + os.path.join(subses_path, "func", "*_events.tsv")
    os.system(cmd_remove)
