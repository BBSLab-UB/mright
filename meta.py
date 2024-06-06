#!/usr/bin/env python3
# -*- coding: utf-8 -*-

############################################
#######  MRIGHT METADATA EDITOR FILE  ######
#######        BBSLab Jun 2024        ######
############################################

import os
import json

json_meta = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "meta.json")

def meta_create():
    '''This function creates an empty meta.json file at the mright root'''
    if os.path.isfile(json_meta) == False:
        empty_dict = {
                      "dicom": "",
                      "dicom_list": "",
                      "bids_in": "",
                      "bids_out": "",
                      "heuristic": "",
                      "ses": "",
                      "recons": "",
                      "bold": "",
                      "qc": ""
                      }
        with open(json_meta, 'a') as file:
            json.dump(empty_dict, file)
            

def meta_func(var, msg, msg2="", ispath=True):
    '''This function collects, updates and returns all the user-inputed data needed
    for the MRIght pipeline. This data is stored at meta.json'''    
    with open(json_meta, 'r') as file:
        data = json.load(file)
    edit_data = False
    if data[var] != "":
        value_ok = False
        while value_ok == False:
            value_check = input("Is this {}?:\n{}\n(Y/N) ".format(msg, data[var])).upper()
            if value_check == 'Y':
                value_ok = True
            elif value_check == 'N':
                data[var] = input(r"Please, enter {}{}: ".format(msg, msg2))
                if ispath == True:
                    data[var] = os.path.normpath(data[var]).replace("'","").replace(" ","") # remove '' from string
                edit_data = True
                value_ok = True
            else:
                print("Please, enter a valid response.")
    else:
        data[var] = os.path.normpath(input(r"Please, enter {}{}: ".format(msg, msg2)).replace("'","").replace(" ",""))
        edit_data = True
    if edit_data == True:
        with open(json_meta, 'w') as file:
            json.dump(data, file)
    return data[var]
