############################################
##########  DICOM TO BIDS SCRIPT  ##########
##########    BBSLab Mar 2024     ##########
############################################

import os
import sys
import importlib.util
import datetime
import shutil
import re
from pathlib import Path

# Function to list folders in a given directory
def list_folders(path):
    """Return a list of folder (subjects) names in the given directory."""
    if not os.path.exists(path):
        print(f"Error: The path '{path}' does not exist.")
        return []
    
    return [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]

def main():
    # Importing meta functions
    root_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.append(root_dir)
    from meta import meta_func, meta_create

    # Input paths
    meta_create()
    dicoms_path = meta_func("dicom", "Enter the path to the DICOMs folder")  # Path to DICOM directories
    bids_path = meta_func("bids_in", "Enter the path to the BIDS folder")  # Path to BIDS directory

    heuristic_file_path = meta_func("heuristic", "your heuristic file path") # Path to heuristic file
    ses = meta_func("ses", "your session label", ispath=False) # Timepoint (session) label

    # Dynamically load and execute a heuristic module to access configuration settings for processing
    heuristic_module_name = os.path.basename(heuristic_file_path).split('.')[0]
    spec = importlib.util.spec_from_file_location(heuristic_module_name, heuristic_file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    delete_scans = module.delete_scans
    delete_events = module.delete_events

    use_sessions = (ses != "NOSESSION")
    
    # List of DICOMS in input directory 
    dicoms_folders = set(list_folders(os.path.join(dicoms_path, "TP2")))
    # Determine subjects to process in BIDS
    if use_sessions:
        ses_path = "ses-{}".format(ses)
        bids = [s[4:] for s in os.listdir(bids_path) if ((s[:4] == "sub-") and os.path.isdir(os.path.join(bids_path, s, ses_path)))]
    else:
        bids = [s[4:] for s in os.listdir(bids_path) if ((s[:4] == "sub-"))]

    # Clean DICOM folders and ensure format consistency
    dicoms_in_list_clean = {f"sub-{re.sub(r'[^a-zA-Z0-9]', '', sub)}" for sub in dicoms_folders}

    # Identify subjects needing processing
    todo_dicoms = {sub for sub in dicoms_in_list_clean if sub not in bids}

    # Identify subjects that do not need processing
    intersection_bids_list = dicoms_in_list_clean.intersection(bids)
    
    # If there are no subjects in both dicoms_folders and bids_path
    if intersection_bids_list == set():                                             # If there isn't any subject in both list and bids_path
        todo_dicoms = dicoms_folders

    # If there are subjects in both dicoms_folders and bids_path
    while (intersection_bids_list != set()) is True:                                # Some subject is both in list and bids_path
        overwrite_bids = input(str(intersection_bids_list) +
                            " already in BIDS directory, do you want to overwrite? (Y/N) ").upper()
        # No overwriting: todo_dicoms = dicoms in list not in bids_path
        if overwrite_bids == "N":                                                  # No overwriting: todo_dicoms = dicoms in list not in bids_path
            todo_dicoms = []
            for sub in dicoms_folders:
                sub_clean = re.sub(r'[^a-zA-Z0-9]', '', sub)
                if sub_clean not in bids:
                    todo_dicoms.append(sub)
            print("Overwriting of " + str(intersection_bids_list) + " was skipped.")
            intersection_bids_list = set()

        # Overwriting: delete BIDS in conflict, convert the entire list    
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
            todo_dicoms = dicoms_folders
            intersection_bids_list = set()
        
        else:
            print("Please, enter a valid response.\n") 

    # Print the list of subjects to be processed
    print("Subjects to be processed:", todo_dicoms)

    # Heudiconv run
    for subj in todo_dicoms:
        try:
            subj_clean = re.sub(r'[^a-zA-Z0-9]', '', subj)
            subj_path = os.path.join(bids_path, f"sub-{subj_clean}")
            if not os.path.exists(subj_path):
                os.mkdir(subj_path)
            subdir_list = [subdir for subdir in os.listdir(subj_path) if os.path.isdir(os.path.join(subj_path, subdir))]
            
            # For longitudinal studies
            # Heuristic must have keys like t1w=create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:02d}_T1w')
            if use_sessions:
                # ses- check: Subj folder must be empty or contain ONLY ses- subfolders
                if subdir_list:
                    subdir_check = [ses_subdir for ses_subdir in subdir_list if "ses-" in ses_subdir[:4]]
                    if subdir_check != subdir_list:
                        with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:
                            print(f"WARNING: Subject {subj} has been skipped due to session hierarchy issues. Logged in error_heudiconv.txt")
                            f.write(str(datetime.datetime.now()) + "\t" + subj + " session hierarchy issue\n")
                        continue
                if ses_path not in os.listdir(subj_path):
                    print(f"Starting subject {subj} conversion")
                    command = "heudiconv -d "+ os.path.join(dicoms_path, "TP2", "{subject}", "*", "*") + " -o "+ bids_path +" -f "+ heuristic_file_path +" -s "+ subj + " -ss "+ ses +" -c dcm2niix -b --minmeta --overwrite --grouping custom"
                    os.system(command)
                else:
                    with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:
                        print(f"WARNING: Subject {subj} was previously processed and will be skipped. Logged in error_heudiconv.txt")
                        f.write(str(datetime.datetime.now()) + "\t" + subj + " already processed\n")
            
            # For non-longitudinal studies
            # Heuristic must have keys like t1w=create_key('sub-{subject}/anat/sub-{subject}_run-{item:02d}_T1w')        
            else:
                # ses- check: Subj folder must be empty or contain ONLY ses- subfolders
                if subdir_list:
                    subdir_check = [ses_subdir for ses_subdir in subdir_list if "ses-" not in ses_subdir[:4]]
                    if subdir_check != subdir_list:
                        with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:
                            print(f"WARNING: Subject {subj} has been skipped due to incorrect session structure. Logged in error_heudiconv.txt")
                            f.write(str(datetime.datetime.now()) + "\t" + subj + " incorrect session structure\n")
                        continue
                if f"sub-{subj_clean}" not in os.listdir(bids_path) or not subdir_list:
                    print(f"Starting subject {subj} conversion")
                    command = "heudiconv -d "+ os.path.join(dicoms_path, "TP2", "{subject}", "*", "*") + " -o "+ bids_path +" -f "+ heuristic_file_path +" -s "+ subj +" -c dcm2niix -b --minmeta --overwrite --grouping custom"
                    os.system(command)
                else:
                    with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:
                        print(f"WARNING: Subject {subj} was previously processed and will be skipped. Logged in error_heudiconv.txt")
                        f.write(str(datetime.datetime.now()) + "\t" + subj + " already processed\n")
        
        except Exception as e:
            with open(os.path.join(bids_path, "error_heudiconv.txt"), "a") as f:
                print(f"WARNING: Unable to process subject {subj} due to an error. Logged in error_heudiconv.txt")
                f.write(str(datetime.datetime.now()) + "\t" + subj + " error: " + str(e) + "\n")
            continue

    # .bidsignore file in case error_heudiconv.txt is created
    if os.path.exists(os.path.join(bids_path, "error_heudiconv.txt")):
        if not os.path.exists(os.path.join(bids_path, ".bidsignore")):
            with open(os.path.join(bids_path, ".bidsignore"), "a") as f:
                f.write("error_heudiconv.txt\n")
        else:
            with open(os.path.join(bids_path, ".bidsignore"), "r+") as f:
                lines = {line.rstrip() for line in f}
                if "error_heudiconv.txt" not in lines:
                    f.write("\nerror_heudiconv.txt\n")   

    # Delete scans.tsv and events.tsv optional files                  
    ses_path = "ses-*" if use_sessions else ""
    subses_path = os.path.join(bids_path, "sub-*", ses_path)

    if len(list(Path(bids_path).glob(os.path.join("sub-*", ses_path, "*scans*")))) > 0:
        if delete_scans == True:
            cmd_scans = "rm " + os.path.join(subses_path, "*_scans.tsv")
            os.system(cmd_scans)
            print("INFO: Deleting all *_scans.tsv files from each subject[/session] folder")
        elif delete_scans == False:
            print("INFO: *_scans.tsv files were left in each subject[/session] folder")
        else:
            print("WARNING: Invalid value for 'delete_scans' variable in heuristics file. No deletion of *_scans.tsv files was done.")

    if len(list(Path(bids_path).glob(os.path.join("sub-*", ses_path, "func", "*_events.tsv")))) > 0:
        if delete_events == True:
            cmd_events = "rm " + os.path.join(subses_path, "func", "*_events.tsv")
            os.system(cmd_events)
            print("INFO: Deleting all *_events.tsv files from each subject[/session]/func folder")
        elif delete_events == False:
            print("INFO: *_events.tsv files were left in each subject[/session]/func folder")
        else:
            print("WARNING: Invalid value for 'delete_events' variable in heuristics file. No deletion of *_events.tsv files was done.")

if __name__ == '__main__':
    main()
