import sys
import os
from pathlib import Path
import pandas as pd
import json

# Add the root directory to the Python path to enable importing from parent directory
root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)
from meta import meta_func, meta_create

# Alternative import path 
# sys.path.append("/home/arnau/Desktop/mright-main")
# from meta import meta_func, meta_create

# Initialize metadata
meta_create()

# Get paths from metadata
bids_path = meta_func("bids_in", "your BIDS destination directory path")
qc_path = meta_func("qc", "your QC directory path")
heuristic_file_path = meta_func("heuristic", "your heuristic file path")
ses = meta_func("ses", "your session label", ispath=False)

# Dynamically load and execute a heuristic module to access configuration settings for processing
heuristic_module_name = os.path.basename(heuristic_file_path).split('.')[0]
spec = importlib.util.spec_from_file_location(heuristic_module_name, heuristic_file_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

delete_scans = module.delete_scans

# Get sequence type (T1 or T2) from user input with validation
value_ok = False
while value_ok == False:
    seq = input(r"Please, enter the sequence type you want to rename (T1/T2): ").upper()
    if seq == "T1" or seq == "T2":
        value_ok = True
    else:
        print("Please, enter a valid response.")

# Define path to the QC file for the specified sequence and session
qc_file = os.path.join(qc_path, "ses-" + ses, seq, "ses-{}_{}_QC.txt".format(ses, seq))

# Find subjects with incorrectly converted files (containing 'heudiconv' in the filename)
wrong_subs = set(str(p).split('/')[-4][4:] for p in list(
    Path(bids_path).glob("sub-*/ses-{}/anat/*{}*heudiconv*nii.gz".format(ses, seq))))

# Get list of subjects that have the specified session, excluding those with incorrect files
subs_with_ses = set([s[4:] for s in os.listdir(bids_path) if os.path.isdir(os.path.join(bids_path, s, "ses-" + ses))]).difference(wrong_subs)

# Rename subjects with incorrect files by adding "REVIEW" suffix
for sub in wrong_subs:
    wrong_files = list(
        Path(bids_path).glob("sub-{}/ses-{}/anat/*{}*heudiconv*nii.gz".format(sub, ses, seq)))
    if sub[-6:] != "REVIEW":
        print("WARNING: {} were incorrectly converted to NIfTI format. Please redo the conversion, sub will be skipped and renamed as sub-{}REVIEW.".format(wrong_files, sub)) 
        os.rename(os.path.join(bids_path, "sub-" + sub), os.path.join(bids_path, "sub-" + sub + "REVIEW"))
    else:
        print("WARNING: {} were incorrectly converted to NIfTI format. Please redo the conversion, sub will be skipped.".format(wrong_files)) 

# Read the QC file into a DataFrame
df_qc = pd.read_csv(qc_file, sep=",", dtype=str)

# Add a new column for the new run numbers
df_qc['new_run'] = None

# Define rating values mapping for sorting/prioritization
ratings = {
    "1": 1,          
    "2A": 2,
    "2": 3,
    "2B": 4,
    "3": 5,
    "4": 6,
    "EXCLUDED": 7,    
    None: 10000,      # Missing values
    "": 10001,
    pd.NA: 10002
}

# Convert text ratings to numeric 
df_qc = df_qc.replace({"rating_value": ratings})

# Functions that regenerate scans.tsv

def normalize_time_string(time_str):
    try:
        h, m, s = time_str.strip().split(":")
        if '.' in s:
            s, us = s.split(".")
        else:
            us = '0'
        s = s.zfill(2)
        us = us.ljust(6, '0')
        return f"{h.zfill(2)}:{m.zfill(2)}:{s}.{us}"
    except Exception as e:
        raise ValueError(f"Invalid time format: '{time_str}'") from e


def generate_new_scans_tsv(bids_folder, sub, ses):
    scans_file = os.path.join(bids_folder, sub, ses, f"{sub}_{ses}_scans.tsv")
    scans_df = pd.read_csv(scans_file, sep="\t")
    date = scans_df.loc[0, 'acq_time'].split('T')[0]

    path_sub_ses = Path(bids_folder) / sub / ses

    nii_files = list(path_sub_ses.glob("*/*.nii.gz"))

    list_of_niis = [file.parent.name + '/' + file.name for file in nii_files]
    list_of_acq_times = []
    list_of_series_times = []
    list_of_jsons = []

    for nii in nii_files:
        json_path = str(nii).replace(".nii.gz", ".json")
        try:
            with open(json_path, 'r') as json_file:
                data = json.load(json_file)
                acq_time_raw = normalize_time_string(data["AcquisitionTime"])
                acq_time = date + "T" + acq_time_raw
            
                try:
                    series_time = data["global"]["const"]["SeriesTime"]
                except (KeyError, TypeError):
                    series_time = pd.NA
        except (FileNotFoundError):
            series_time = pd.NA
            acq_time = pd.NA
            print(json_path, "not found")
        
        json_fn = os.path.basename(json_path)

        list_of_acq_times.append(acq_time)
        list_of_series_times.append(series_time)
        list_of_jsons.append(json_fn)

    real_df = pd.DataFrame({'filename': list_of_niis,
                            'acq_time': list_of_acq_times,
                            'series_time': list_of_series_times
                            })
    
    if pd.notna(real_df['series_time']).any():
        real_df.sort_values(by=['acq_time', 'series_time'], inplace=True, ignore_index=True)
    else:
        real_df.sort_values(by='acq_time', inplace=True, ignore_index=True)

    if 'series_time' in real_df.columns:
        real_df.drop(columns='series_time', inplace=True)
    
    real_df.to_csv(os.path.join(bids_folder, sub, ses, f"{sub}_{ses}_scans.tsv"), sep="\t", index=False)
    
# Process each subject that has the specified session and is in the QC file
for sub in set(df_qc.subject).intersection(subs_with_ses):

    # Check if this subject has already been processed (has run-00 files)
    dirname_anat = os.path.join(bids_path, 'sub-'+str(sub), 'ses-'+ses, 'anat')
    has_run_00 = any(f'run-00_{seq}w.nii.gz' in f for f in os.listdir(dirname_anat))
        
    if has_run_00:
        print(f"INFO: Sub {sub} has already been processed (run-00 files exist). Skipping.")
        continue
    
    # Count how many runs for this sequence and subject exist in the BIDS directory
    runs_sub_seq_bidspath = sum(seq+'w.nii.gz' in f for f in os.listdir(
        os.path.join(bids_path,'sub-'+str(sub), 'ses-'+ses, 'anat')))
    
    # Remove entries with missing ratings
    df_qc = df_qc[df_qc.rating_value < 10000]
    
    if sub in set(df_qc.subject):
        # Count how many runs for this subject and sequence are in the QC file
        runs_sub_seq_qc = df_qc.subject.value_counts()[sub]
        
        # Check if BIDS directory has more runs than QC file
        if runs_sub_seq_bidspath > runs_sub_seq_qc:
            print(f"WARNING: Sub {sub} has some unchecked {seq} files and will be skipped. Please review the QC file and the BIDS folder of the sub.")
            continue
        # Check if QC file has more runs than BIDS directory
        elif runs_sub_seq_bidspath < runs_sub_seq_qc:
            sub_df = df_qc[df_qc.subject == sub]
            # Check if there are duplicate run entries in QC file
            if sub_df.duplicated(subset=['run']).any():
                # Check that there are no conflicting ratings (excluded or rating 4)
                if all(i != 6 and i != 7 for i in sub_df[sub_df.duplicated(keep=False, subset=['run'])].rating_value):
                    print(f"INFO: Some {seq} files of sub {sub} were checked more than once. Best rating will be kept.")
                    # Keep only the best rating for each run
                    df_qc = pd.concat([
                        df_qc[df_qc.subject != sub],
                        sub_df.sort_values('rating_value').drop_duplicates(subset=['run'], keep='first').sort_values('run')
                    ], ignore_index=True)
                else:
                    print(f"WARNING: Some {seq} files of sub {sub} were checked more than once, and some of these ratings conflict each other. Sub will be skipped. Please review the QC file.")
                    continue
    else:
        print(f"WARNING: Sub {sub} not found in the QC file.")
        continue
    
    # Prepare for renaming based on ratings
    df_this_sub = df_qc[df_qc.subject == sub].copy()
    # Sort by run number
    df_this_sub = df_this_sub.sort_values(by='run')
    
    # Get rating of the first run ('01')
    rating_01 = df_this_sub[df_this_sub.run == '01'].rating_value.iloc[0]
    
    # If first run has poor quality, rename it to '00'
    if rating_01 > 5:
        df_this_sub.loc[df_this_sub.index[df_this_sub.run == '01'], 'new_run'] = "00"
    
    # Find the run with the best rating (lowest numeric value)
    idx_min = df_this_sub['rating_value'].idxmin()
    min_val = df_this_sub.loc[idx_min, 'rating_value']

    # If any runs have acceptable quality 
    if min_val <= 5:
        # If the best run is not already run '01', rename files
        if min_val != rating_01:
            df_this_sub.loc[df_this_sub.index[df_this_sub.run == '01'], 'new_run'] = "00"
            df_this_sub.loc[idx_min, 'new_run'] = '01'
        else:
            continue 
    else:
        # If all runs have poor quality, mark the subject as discarded in comments
        for i, idx in enumerate(df_this_sub.index):
            existing_comment = df_this_sub.at[idx, 'comment']
            cleaned_comment = str(existing_comment) if pd.notna(existing_comment) else ""
            df_this_sub.at[idx, 'comment'] = cleaned_comment + " [SUB DISCARDED]"

    # Update the main QC DataFrame with new run numbers and comments
    df_qc.loc[df_this_sub.index, ['new_run', 'comment']] = df_this_sub[['new_run', 'comment']]
    
    # Path to the anatomical directory for this subject
    dirname_anat = os.path.join(bids_path,'sub-'+str(sub), 'ses-'+ses, 'anat')
    
    print("")
    
    # Rename files based on the new run numbers
    for i in range(len(df_this_sub)):
        if df_this_sub.run.iloc[i] != df_this_sub.new_run.iloc[i]:
            # Define old and new file paths
            old_path = os.path.join(dirname_anat, 'sub-{}_ses-{}_run-{}_{}w'.format(sub, ses, df_this_sub.run.iloc[i], seq))
            new_path = os.path.join(dirname_anat, 'sub-{}_ses-{}_run-{}_{}w'.format(sub, ses, df_this_sub.new_run.iloc[i], seq))
            
            print('Old path:', old_path)
            print('New path:', new_path)
            
            # Execute the file renaming commands
            os.system("mv {} {}".format(old_path+".nii.gz", new_path+".nii.gz"))
            os.system("mv {} {}".format(old_path+".json", new_path+".json"))
            
    
    # Regenerate scans.tsv file
    if delete_scans = False:
        generate_new_scans_tsv(bids_path, 'sub-' + sub, 'ses-' + ses)
