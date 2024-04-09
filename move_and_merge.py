############################################
######  BIDS TO SHARED FOLDER SCRIPT  ######
######        BBSLab Apr 2024         ######
############################################

import os
import shutil
import warnings
import pandas as pd

local_bids_path = os.path.normpath(input(r"Please, enter your BIDS source (local) directory path: ").replace("'","").replace(" ","")) 
destination_bids_path = os.path.normpath(input(r"Please, enter your BIDS destination (shared) directory path: ").replace("'","").replace(" ","")) 

list_of_subs_local = [sub for sub in os.listdir(local_bids_path) if sub[:4] == "sub-"]

# move ses-XX to shared folder
def move_subs_to_destination(source, destination):
    if os.path.isdir(destination) == False:
        os.mkdir(destination)
    if os.listdir(source) == []:
        warnings.warn('WARNING: Source subject folder {} is empty. Check if it has not been already moved'.format(source))
    for subdir in os.listdir(source):
        if (subdir in os.listdir(destination)) == False:
            shutil.move(os.path.join(source, subdir), os.path.join(destination, subdir))
            print('{} subfolder was SUCCESSFULLY MOVED to {}'.format(subdir, destination))
        else:
            warnings.warn('WARNING: Subfolder {} already exists in subject folder {}. Moving was SKIPPED.'.format(subdir, destination))

if '.heudiconv' not in os.listdir(destination_bids_path):
    os.mkdir(os.path.join(destination_bids_path, '.heudiconv'))
    
# move BIDS
for sub in list_of_subs_local:
    move_subs_to_destination(os.path.join(local_bids_path, sub), os.path.join(destination_bids_path, sub))
    # move .heudiconv
    move_subs_to_destination(os.path.join(local_bids_path, '.heudiconv', sub[4:]), os.path.join(destination_bids_path, '.heudiconv', sub[4:]))
    
# move unique files        
others_local = [other for other in os.listdir(local_bids_path) if other[:4] != "sub-"]
uniques_local = [unique for unique in others_local if (unique not in [".heudiconv", ".bidsignore", "participants.tsv", "error_heudiconv.txt"])]

for unique_file in uniques_local:
    if (unique_file in os.listdir(destination_bids_path)) == False:
        shutil.move(os.path.join(local_bids_path, unique_file), os.path.join(destination_bids_path, unique_file))
        print('{} file was SUCCESSFULLY MOVED to destination folder'.format(unique_file))
    else:
        warnings.warn('WARNING: {} file already exists in destination folder. Moving was SKIPPED.'.format(unique_file))
        
# merge editable files
def merge_files(source_file_path, destination_file_path):
    if os.path.exists(source_file_path) == True:
        with open(destination_file_path, "a") as dest:
            pass
        with open(destination_file_path, "r+") as dest:
            dest_lines = [line.rstrip() for line in dest]
            with open(source_file_path, 'r') as src:
                for line in src:
                    if line[:-1] not in dest_lines:
                        dest.write(line)
        with open(destination_file_path, "r") as dest2:                
            dest_lines2 = [line.rstrip() for line in dest2]
            if dest_lines != dest_lines2:
                print('{} was updated'.format(destination_file_path))                        

merge_files(os.path.join(local_bids_path,'.bidsignore'), os.path.join(destination_bids_path,'.bidsignore'))
merge_files(os.path.join(local_bids_path,'error_heudiconv.txt'), os.path.join(destination_bids_path,'error_heudiconv.txt'))

# merge participants.tsv

df_participants_src = pd.read_csv(os.path.join(local_bids_path,"participants.tsv"), sep='\t')

if os.path.exists(os.path.join(destination_bids_path,"participants.tsv")) == True:   
    df_participants_des = pd.read_csv(os.path.join(destination_bids_path,"participants.tsv"), sep='\t')
    new_participants_des = pd.concat((df_participants_des, df_participants_src)).groupby('participant_id').first().reset_index() 
    new_participants_des.to_csv(os.path.join(destination_bids_path,"participants.tsv"), sep="\t",
                      header=True, index=False, na_rep="n/a")
    if df_participants_des.equals(new_participants_des) == False:
        print("participants.tsv was successfully updated")
else:
    new_participants_des = df_participants_src
    new_participants_des.to_csv(os.path.join(destination_bids_path,"participants.tsv"), sep="\t",
                      header=True, index=False, na_rep="n/a")
