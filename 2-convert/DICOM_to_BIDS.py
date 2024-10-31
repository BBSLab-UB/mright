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
    """Return a list of folder names in the given directory."""
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
    folder1 = meta_func("dicom", "Enter the path to the DICOMs folder")  # Path to DICOM directories
    folder2 = meta_func("bids_in", "Enter the path to the BIDS folder")  # Path to BIDS directory

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
    
    # List of DICOMS in input directory within TP2
    dicoms_folders = set(list_folders(os.path.join(folder1, "TP2")))

    # Determine subjects to process in BIDS
    if use_sessions:
        ses_path = "ses-{}".format(ses)
        bids = [s[4:] for s in os.listdir(folder2) if ((s[:4] == "sub-") and os.path.isdir(os.path.join(folder2, s, ses_path)))]
    else:
        bids = [s[4:] for s in os.listdir(folder2) if ((s[:4] == "sub-"))]

    # Identify subjects needing processing
    dicoms_in_list_clean = [re.sub(r'[^a-zA-Z0-9]', '', sub) for sub in dicoms_folders]
    todo_dicoms = [sub for sub in dicoms_folders if re.sub(r'[^a-zA-Z0-9]', '', sub) not in bids]
    intersection_bids_list = set(dicoms_in_list_clean).intersection(bids)

    if not intersection_bids_list:
        todo_dicoms = dicoms_folders

    while intersection_bids_list:
        overwrite_bids = input(f"{intersection_bids_list} already in BIDS directory, do you want to overwrite? (Y/N) ").upper()
        if overwrite_bids == "N":
            todo_dicoms = [sub for sub in dicoms_folders if re.sub(r'[^a-zA-Z0-9]', '', sub) not in bids]
            print("Overwriting of " + str(intersection_bids_list) + " was skipped.")
            intersection_bids_list = set()
        elif overwrite_bids == "Y":
            for dicom_id in dicoms_in_list_clean:
                subject_path = os.path.join(folder2, f"sub-{dicom_id}", ses_path) if use_sessions else os.path.join(folder2, f"sub-{dicom_id}")
                if os.path.exists(subject_path):
                    shutil.rmtree(subject_path)
                    print(f"INFO: {subject_path} will be overwritten.")
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
            subj_path = os.path.join(folder2, f"sub-{subj_clean}")
            if not os.path.exists(subj_path):
                os.mkdir(subj_path)
            subdir_list = [subdir for subdir in os.listdir(subj_path) if os.path.isdir(os.path.join(subj_path, subdir))]
            
            # For longitudinal studies
            if use_sessions:
                if subdir_list:
                    subdir_check = [ses_subdir for ses_subdir in subdir_list if "ses-" in ses_subdir[:4]]
                    if subdir_check != subdir_list:
                        with open(os.path.join(folder2, "error_heudiconv.txt"), "a") as f:
                            print(f"WARNING: Subject {subj} has been skipped due to session hierarchy issues. Logged in error_heudiconv.txt")
                            f.write(str(datetime.datetime.now()) + "\t" + subj + " session hierarchy issue\n")
                        continue
                if ses_path not in os.listdir(subj_path):
                    print(f"Starting subject {subj} conversion")
                    command = "heudiconv -d "+ os.path.join(folder1, "TP2", "{subject}", "*", "*.IMA") + " -o "+ folder2 +" -f "+ heuristic_file_path +" -s "+ subj + " -ss "+ ses +" -c dcm2niix -b --minmeta --overwrite --grouping custom"
                    os.system(command)
                else:
                    with open(os.path.join(folder2, "error_heudiconv.txt"), "a") as f:
                        print(f"WARNING: Subject {subj} was previously processed and will be skipped. Logged in error_heudiconv.txt")
                        f.write(str(datetime.datetime.now()) + "\t" + subj + " already processed\n")
           
            else:
                if subdir_list:
                    subdir_check = [ses_subdir for ses_subdir in subdir_list if "ses-" not in ses_subdir[:4]]
                    if subdir_check != subdir_list:
                        with open(os.path.join(folder2, "error_heudiconv.txt"), "a") as f:
                            print(f"WARNING: Subject {subj} has been skipped due to incorrect session structure. Logged in error_heudiconv.txt")
                            f.write(str(datetime.datetime.now()) + "\t" + subj + " incorrect session structure\n")
                        continue
                if f"sub-{subj_clean}" not in os.listdir(folder2) or not subdir_list:
                    print(f"Starting subject {subj} conversion")
                    command = "heudiconv -d "+ os.path.join(folder1, "TP2", "{subject}", "*", "*.IMA") + " -o "+ folder2 +" -f "+ heuristic_file_path +" -s "+ subj +" -c dcm2niix -b --minmeta --overwrite --grouping custom"
                    os.system(command)
                else:
                    with open(os.path.join(folder2, "error_heudiconv.txt"), "a") as f:
                        print(f"WARNING: Subject {subj} was previously processed and will be skipped. Logged in error_heudiconv.txt")
                        f.write(str(datetime.datetime.now()) + "\t" + subj + " already processed\n")
        
        except Exception as e:
            with open(os.path.join(folder2, "error_heudiconv.txt"), "a") as f:
                print(f"WARNING: Unable to process subject {subj} due to an error. Logged in error_heudiconv.txt")
                f.write(str(datetime.datetime.now()) + "\t" + subj + " error: " + str(e) + "\n")
            continue

    # .bidsignore file in case error_heudiconv.txt is created
    if os.path.exists(os.path.join(folder2, "error_heudiconv.txt")):
        if not os.path.exists(os.path.join(folder2, ".bidsignore")):
            with open(os.path.join(folder2, ".bidsignore"), "a") as f:
                f.write("error_heudiconv.txt\n")
        else:
            with open(os.path.join(folder2, ".bidsignore"), "r+") as f:
                lines = {line.rstrip() for line in f}
                if "error_heudiconv.txt" not in lines:
                    f.write("\nerror_heudiconv.txt\n")   

    # Delete scans.tsv and events.tsv optional files                  
    ses_path = "ses-*" if use_sessions else ""
    subses_path = os.path.join(folder2, "sub-*", ses_path)

    if len(list(Path(folder2).glob(os.path.join("sub-*", ses_path, "*scans*")))) > 0:
        if delete_scans:
            cmd_scans = "rm " + os.path.join(subses_path, "*_scans.tsv")
            os.system(cmd_scans)
            print("INFO: Deleting all *_scans.tsv files from each subject[/session] folder")
        else:
            print("INFO: *_scans.tsv files were left in each subject[/session] folder")

    if len(list(Path(folder2).glob(os.path.join("sub-*", ses_path, "func", "*_events.tsv")))) > 0:
        if delete_events:
            cmd_events = "rm " + os.path.join(subses_path, "func", "*_events.tsv")
            os.system(cmd_events)
            print("INFO: Deleting all *_events.tsv files from each subject[/session]/func folder")
        else:
            print("INFO: *_events.tsv files were left in each subject[/session]/func folder")

if __name__ == '__main__':
    main()