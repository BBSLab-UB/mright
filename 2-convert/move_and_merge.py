############################################
######  BIDS TO SHARED FOLDER SCRIPT  ######
######        BBSLab Apr 2024         ######
############################################

import os
import sys
import warnings
from pathlib import Path
import pandas as pd

root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)
from meta import meta_func, meta_create

# we have to move the generated BIDS and metadata to the shared folder
meta_create()
local_bids_path = meta_func("bids_in", "your BIDS source (local) directory path")
destination_bids_path = meta_func("bids_out", "your BIDS destination (shared) directory path")

#subjects to move
list_of_subs_local = [sub for sub in os.listdir(local_bids_path) if sub[:4] == "sub-"]

# function: move subject-related files to shared folder
def move_subs_to_destination(source, destination):
    '''This function moves the subfolders of a given subject to the
    destination folder'''
    if os.path.isdir(destination) == False:
        os.mkdir(destination)
    if os.listdir(source) == []:
        warnings.warn('WARNING: Source subject folder {} is empty. Check if it has not been already moved'.format(source))
    for subdir in os.listdir(source):
        if (subdir in os.listdir(destination)) == False:
            command_dir = "cp -r " + os.path.join(source, subdir) + " " + os.path.join(destination, subdir) + " && rm -rf " + os.path.join(source, subdir)
            os.system(command_dir)
            print('{} subfolder was SUCCESSFULLY MOVED to {}'.format(subdir, destination))
        else:
            warnings.warn('WARNING: Subfolder {} already exists in subject folder {}. Moving was SKIPPED.'.format(subdir, destination))

# ses-noses tree check
listdir2 = lambda bids_root:[os.path.basename(str(subdir_p)) for subdir_p in list(Path(bids_root).glob(os.path.join('sub-*','*')))]
ses_tree = lambda bids_root: any('ses' in subdir_n for subdir_n in listdir2(bids_root))
noses_tree = lambda bids_root: any('ses' not in subdir_n for subdir_n in listdir2(bids_root))

def check(path1, path2):
    if listdir2(path1) != [] and listdir2(path2) != []:
        if ses_tree(path1) == noses_tree(path2):
            if path1 == path2:
                raise ValueError('ERROR: {} directory has both session and no-session hierarchies.'.format(path1))
            else:
                raise ValueError('ERROR: Input {} and output {} directories have conflicting session/no-session hierarchies.'.format(path1, path2))

check(local_bids_path, local_bids_path)
check(destination_bids_path, destination_bids_path)
check(local_bids_path, destination_bids_path)

# create .heudiconv in destination path
if '.heudiconv' not in os.listdir(destination_bids_path):
    os.mkdir(os.path.join(destination_bids_path, '.heudiconv'))
   
for sub in list_of_subs_local:
    # move BIDS
    move_subs_to_destination(os.path.join(local_bids_path, sub), os.path.join(destination_bids_path, sub))
    # move .heudiconv
    move_subs_to_destination(os.path.join(local_bids_path, '.heudiconv', sub[4:]), os.path.join(destination_bids_path, '.heudiconv', sub[4:]))
    
# move unique files: files that only exist once in each BIDS directory        
others_local = [other for other in os.listdir(local_bids_path) if other[:4] != "sub-"]
uniques_local = [unique for unique in others_local if (unique not in [".heudiconv", ".bidsignore", "participants.tsv", "error_heudiconv.txt"])] #.heudiconv folder and editable files are excluded

for unique_file in uniques_local:
    if (unique_file in os.listdir(destination_bids_path)) == False:
        command_file = "cp " + os.path.join(local_bids_path, unique_file) + " " + os.path.join(destination_bids_path, unique_file) + " && rm -f " + os.path.join(local_bids_path, unique_file)
        os.system(command_file)
        print('{} file was SUCCESSFULLY MOVED to destination folder'.format(unique_file))
    else:
        print('INFO: {} file already exists in destination folder. Moving was SKIPPED.'.format(unique_file))
        
# merge editable text files
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
                        
# merge .bidsignore and error_heudiconv.txt
merge_files(os.path.join(local_bids_path,'.bidsignore'), os.path.join(destination_bids_path,'.bidsignore'))
merge_files(os.path.join(local_bids_path,'error_heudiconv.txt'), os.path.join(destination_bids_path,'error_heudiconv.txt'))

# merge participants.tsv using pandas dataframes
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

# remove local_bids_path tree
os.system("rm -rf " + local_bids_path)
print(local_bids_path + " local BIDS directory was SUCCESSFULLY REMOVED")
