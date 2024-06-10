#!/bin/bash

############################################
#########  T1/T2 VALIDATOR FOR QC  #########
#########     BBSLab Jun 2024      #########
############################################

read -p "Please, enter your GIF folder path: " ROOT
ROOT="${ROOT//"'"/}"
ROOT="${ROOT//" "/}"

session_foldername=$(basename $(dirname $(dirname $ROOT)))
if [[ $session_foldername == "ses-"* ]]; then
    TXT_QUALITY_FILE="$(dirname $ROOT)"/"$session_foldername""_""$(basename $(dirname $ROOT))"_QC.txt
else
    TXT_QUALITY_FILE="$(dirname $ROOT)"/"$(basename $(dirname $ROOT))"_QC.txt
fi
TXT_QUALITY_FILE="${TXT_QUALITY_FILE//"'"/}"
TXT_QUALITY_FILE="${TXT_QUALITY_FILE//" "/}"
# Example of TXT_QUALITY_FILE path = /[...]/QC/ses-02/T1/ses-02_T1.txt

echo "COUNTING FILES TO BE CHECKED..."

done=0
todo=0

for file_path in $ROOT/*; do

    file=$(basename $file_path)

    if [[ $file == *"checked"* ]]; then
    ((done=done+1))
    else
        ((todo=todo+1))
    fi

done

echo "## CHECKED FILES: $done"
echo "## FILES TO BE CHECKED: $todo"

read -p "Press any key to start" trashkey

declare -A quality_array=(["T1"]="1 2A 2B 3 4 EXCLUDED" ["T2"]="1 2 3 4 EXCLUDED")


n=0
for file_path in $ROOT/*; do

    file=$(basename $file_path)
    suj=$(echo $file | grep -oP '(?<=sub-)[^_]+')
    ses=$(echo $file | grep -oP '(?<=ses-)[^_]+')
    run=$(echo $file | grep -oP '(?<=run-)[^_]+')
    imgtype=$(echo $file | grep -oP '(?<=_)[^_]+(?=\.)')
    declare -a qc_values=(${quality_array[$imgtype]})
    if [[ $file == *"checked"* ]]; then
        echo "Subject $suj already checked"
    else
        echo
        echo "####"
        echo
        echo "Checking subject $suj run $run..."

        #Opening gif
        eom --fullscreen $file_path

        #Asking for rating
        read -p 'Rate quality: ' quality
        quality="${quality//"."/}"
        while ! echo ${qc_values[@]} | grep -i -w -q ${quality} ; do
            read -p 'Invalid rating value. Please rate quality with a valid value: ' quality
            quality="${quality//"."/}"
        done

        read -p "Comment here (press ENTER to skip): " comment
        #Writing rate
        if [ ! -f $TXT_QUALITY_FILE ]; then
            echo "subject,run,rating_value,comment" >> $TXT_QUALITY_FILE
        fi
        echo "$suj,"$run",${quality^^},\"$comment\"" >> $TXT_QUALITY_FILE

        #Marking as checked by changing filename
        if [ -z "$ses" ]; then
            mv $ROOT/sub-${suj}_run-${run}_${imgtype}.gif $ROOT/sub-${suj}_run-${run}_${imgtype}_checked.gif
        else
            mv $ROOT/sub-${suj}_ses-${ses}_run-${run}_${imgtype}.gif $ROOT/sub-${suj}_ses-${ses}_run-${run}_${imgtype}_checked.gif
        fi

        ((n=n+1))
        if [[ $n == 10 ]]; then
            read -p "Take a breath; 10 checkings in a row. Press any key to continue" trashkey
            n=0
        fi
    fi

done
