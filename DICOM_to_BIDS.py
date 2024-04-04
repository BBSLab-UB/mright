############################################
##########  DICOM TO BIDS SCRIPT  ##########
##########    BBSLab Mar 2024     ##########
############################################

# import libraries
import os
import datetime
import shutil

# input paths
# remove '' from string
dicoms_path = os.path.normpath(input(r"Please, enter your DICOM source directory path (add TP folder to path if needed): ").replace("'","")) # /institut directory
dicoms_list = os.path.normpath(input(r"Please, enter your list of DICOMS file path: ").replace("'",""))         # copy subjects folders to a .txt --> a subject ID per line
bids_path = os.path.normpath(input(r"Please, enter your BIDS destination directory path: ").replace("'",""))    # recommended: local folder at /home, folder must be created before running the script
heuristic_file_path = os.path.normpath(input(r"Please, enter your heuristic file path: ").replace("'",""))
ses = input(r"Please, enter your session number: ")

#selecting DICOMS from list
with open(dicoms_list) as file:
    dicoms_in_list = [dicom_id.rstrip() for dicom_id in file]

# list of DICOMS in input directory
dicoms_in_dir = [s for s in os.listdir(dicoms_path)]

# is there any difference?
list_minus_dir = set(dicoms_in_list).difference(dicoms_in_dir)
if (list_minus_dir != set()) is True:                                           # Some subject not in dicoms_path
    print(f'WARNING: {str(list_minus_dir)} subject(s) not in source directory')
    with open(os.path.join(bids_path, "error_heudiconv.txt"), 'a') as f:        # error log
        f.write(str(datetime.datetime.now()) + "\t" + str(list_minus_dir) +
                " subject(s) not in source directory\n")

# is there any BIDS already in the bids_path? Is there any conflict? Do you want to overwrite?
bids = [s[4:] for s in os.listdir(bids_path) if s[4:].isdigit() and os.path.isdir(os.path.join(bids_path, s, "ses-{}".format(ses)))]
intersection_bids_list = set(dicoms_in_list).intersection(bids)

while (intersection_bids_list != set()) is True:                                # Some subject is both in list and bids_path
    overwrite_bids = input(str(intersection_bids_list) +
                           " already in BIDS directory, do you want to overwrite? (Y/N) ").upper()
    if overwrite_bids == "N":                                                   # No overwriting: todo_dicoms = dicoms in list not in bids_path
        todo_dicoms = list(set(dicoms_in_list).difference(bids))
        intersection_bids_list = set()
    elif overwrite_bids == "Y":                                                 # Overwriting: delete BIDS in conflict, convert the entire list
        for dicom_id in intersection_bids_list:
            shutil.rmtree(os.path.join(bids_path, 'sub-{}'.format(dicom_id)))
            shutil.rmtree(os.path.join(bids_path, '.heudiconv', dicom_id))
        todo_dicoms = dicoms_in_list
        intersection_bids_list = set()
    else:
        print("Please, enter a valid response.\n")                              # can't exit loop if Y/N is not entered


# heudiconv run
for suj in todo_dicoms:
    try:
        if not os.path.join("sub-{}".format(suj),"ses-{}".format(ses)) in os.listdir(bids_path):
            print(suj)
            command = 'heudiconv -d '+ os.path.join(dicoms_path,'{subject}','*','*.IMA') + ' -o '+ bids_path +' -f '+ heuristic_file_path +' -s '+ suj + ' -ss '+ ses +' -c dcm2niix -b --minmeta --overwrite'
            os.system(command)
        else:                                                                   # this should not happen, todo_dicoms subjects are never in bids_path previously
            with open(os.path.join(bids_path, "error_heudiconv.txt"), 'a') as f:
                f.write(str(datetime.datetime.now()) + "\t" +suj + " already processed\n")
           
    except:                                                                     # this could happen, especially if the script is run on Windows
        with open(os.path.join(bids_path, "error_heudiconv.txt"), 'a') as f:
            f.write(str(datetime.datetime.now()) + "\t" +suj + " error\n")
        continue

# .bidsignore file in case error_heudiconv.txt is created
if os.path.exists(os.path.join(bids_path, ".bidsignore")) == False:
    if os.path.exists(os.path.join(bids_path, "error_heudiconv.txt")) == True:
        with open(os.path.join(bids_path, ".bidsignore"), 'a') as f:
                    f.write('error_heudiconv.txt\n')
