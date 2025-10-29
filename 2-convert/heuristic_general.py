############################################
#######  GENERAL-USE HEURISTIC FILE  #######
#######       BBSLab Oct 2025        #######
############################################

import os
import json

json_meta = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "meta.json")
with open(json_meta, 'r') as file:
    data = json.load(file)
if data['ses'] == "NOSESSION":        
    session_dir = ""
    session_str = ""
else:
    session_dir = "/{session}"
    session_str = "_{session}"

grouping = 'studyUID'                   # change it to 'all' if Study Identifier UID error appears

delete_scans = False
delete_events = True

# create files function
def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes


def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where

    allowed template fields - follow python string module:

    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """
    # paths for the desired output BIDS. Further BIDS paths must follow BIDS
    # specification filenames: https://bids-standard.github.io/bids-starter-kit/folders_and_files/files.html
    
    t1w=create_key('sub-{subject}'+session_dir+'/anat/sub-{subject}'+session_str+'_run-{item:02d}_T1w')
    t2w=create_key('sub-{subject}'+session_dir+'/anat/sub-{subject}'+session_str+'_run-{item:02d}_T2w')
    flair=create_key('sub-{subject}'+session_dir+'/anat/sub-{subject}'+session_str+'_run-{item:02d}_FLAIR')
    
    rest_bold_ap=create_key('sub-{subject}'+session_dir+'/func/sub-{subject}'+session_str+'_task-rest_dir-ap_run-{item:02d}_bold')
    rest_sbref_ap=create_key('sub-{subject}'+session_dir+'/func/sub-{subject}'+session_str+'_task-rest_dir-ap_run-{item:02d}_sbref')

    dwi_dir_ap=create_key('sub-{subject}'+session_dir+'/dwi/sub-{subject}'+session_str+'_dir-ap_run-{item:02d}_dwi') 
    dwi_dir_pa=create_key('sub-{subject}'+session_dir+'/dwi/sub-{subject}'+session_str+'_dir-pa_run-{item:02d}_dwi') 
    
    swi_mag=create_key('sub-{subject}'+session_dir+'/swi/sub-{subject}'+session_str+'_run-{item:02d}_part-mag_GRE')
    swi_phase=create_key('sub-{subject}'+session_dir+'/swi/sub-{subject}'+session_str+'_run-{item:02d}_part-phase_GRE')
    swi_comb=create_key('sub-{subject}'+session_dir+'/swi/sub-{subject}'+session_str+'_run-{item:02d}_swi')
    swi_mip=create_key('sub-{subject}'+session_dir+'/swi/sub-{subject}'+session_str+'_run-{item:02d}_minIP')
    
    pcasl_vol_ap=create_key('sub-{subject}'+session_dir+'/perf/sub-{subject}'+session_str+'_acq-pcasl_dir-ap_run-{item:02d}_asl') 
    pcasl_vol_pa=create_key('sub-{subject}'+session_dir+'/perf/sub-{subject}'+session_str+'_acq-pcasl_dir-pa_run-{item:02d}_asl')

    rest_sefm_ap=create_key('sub-{subject}'+session_dir+'/fmap/sub-{subject}'+session_str+'_acq-restsefm_dir-ap_run-{item:02d}_epi')
    rest_sefm_pa=create_key('sub-{subject}'+session_dir+'/fmap/sub-{subject}'+session_str+'_acq-restsefm_dir-pa_run-{item:02d}_epi')
    dwi_sefm_ap=create_key('sub-{subject}'+session_dir+'/fmap/sub-{subject}'+session_str+'_acq-dwisefm_dir-ap_run-{item:02d}_epi')
    dwi_sefm_pa=create_key('sub-{subject}'+session_dir+'/fmap/sub-{subject}'+session_str+'_acq-dwisefm_dir-pa_run-{item:02d}_epi')
    pcasl_sefm_ap=create_key('sub-{subject}'+session_dir+'/fmap/sub-{subject}'+session_str+'_acq-pcaslsefm_dir-ap_run-{item:02d}_epi') 
    pcasl_sefm_pa=create_key('sub-{subject}'+session_dir+'/fmap/sub-{subject}'+session_str+'_acq-pcaslsefm_dir-pa_run-{item:02d}_epi')    


    # dictionary: list of DICOMs for each BIDS file
    info =  {
                    t1w:[],
                    t2w:[],
                    flair:[],
                    rest_bold_ap:[],
                    rest_sbref_ap:[],
                    dwi_dir_ap:[],
                    dwi_dir_pa:[],
                    swi_mag:[],
                    swi_phase:[],
                    swi_comb:[],
                    swi_mip:[],
                    pcasl_vol_ap:[],
                    pcasl_vol_pa:[],
                    rest_sefm_ap:[],
                    rest_sefm_pa:[],
                    dwi_sefm_ap:[],
                    dwi_sefm_pa:[],
                    pcasl_sefm_ap:[],
                    pcasl_sefm_pa:[],
             }

    # append DICOMS to dictionary keys --> to change in function of protocol_name,
    # can be found in <bidspath>/.heudiconv/<subject>/ses-<session>/info/dicominfo_ses-<session>.tsv
    # test heudiconv can be done by 'heudiconv --files <dicoms_path>/<subject>/*/*.IMA -o <bids_path>/ -f convertall -s <subject> -c none' on command
    
    for s in seqinfo:
       
        #anat
        if s.protocol_name=='T1w_MPR':
            info[t1w].append(s.series_id)   
        if s.protocol_name=='T2w_SPC':
            info[t2w].append(s.series_id) 
        if s.protocol_name=='t2_tse_dark-fluid_tra_3mm':
            info[flair].append(s.series_id)
            
        #resting
        if s.protocol_name=='restinga-p':
            if s.sequence_name=='epfid2d1_104':
                if s.image_type[3]=='MB':             
                    info[rest_bold_ap].append(s.series_id)
                elif s.image_type[3]=='ND':               
                    info[rest_sbref_ap].append(s.series_id)
        if s.protocol_name=='resting a-p':
            if s.series_description == 'resting a-p':
                info[rest_bold_ap].append(s.series_id)
            elif s.series_description == 'resting a-p_SBRef':
                info[rest_sbref_ap].append(s.series_id)
        if s.protocol_name=='SPECHOGFMA-P' or s.protocol_name=='SPECHO GFM A-P':
            info[rest_sefm_ap].append(s.series_id)
        elif s.protocol_name=='SPECHOGFMP-A' or s.protocol_name=='SPECHO GFM P-A':
            info[rest_sefm_pa].append(s.series_id)
            
        #dwi
        if s.protocol_name=='cmrr_mbep2d_diff_99A-P':
            if s.sequence_name=='epse2d1_140':
                info[dwi_sefm_ap].append(s.series_id)
            else:
                info[dwi_dir_ap].append(s.series_id)
        elif s.protocol_name=='cmrr_mbep2d_diff_99 A-P':
            if s.series_description=='cmrr_mbep2d_diff_99 A-P_SBRef':
                info[dwi_sefm_ap].append(s.series_id)
            elif s.series_description=='cmrr_mbep2d_diff_99 A-P':
                info[dwi_dir_ap].append(s.series_id)

        if s.protocol_name=='cmrr_mbep2d_diff_99P-A':
            if s.sequence_name=='epse2d1_140':
                info[dwi_sefm_pa].append(s.series_id)
            else:
                info[dwi_dir_pa].append(s.series_id)
        elif s.protocol_name=='cmrr_mbep2d_diff_99 P-A':
            if s.series_description=='cmrr_mbep2d_diff_99 P-A_SBRef':
                info[dwi_sefm_pa].append(s.series_id)
            elif s.series_description=='cmrr_mbep2d_diff_99 P-A':
                info[dwi_dir_pa].append(s.series_id)
        
        #swi
        if s.protocol_name=='SWI':
            if s.image_type[2]=='P':
                info[swi_phase].append(s.series_id)  
            elif s.image_type[2]=='MNIP':
                info[swi_mip].append(s.series_id)
            elif s.image_type[3]=='SWI':
                info[swi_comb].append(s.series_id)
            else :
                info[swi_mag].append(s.series_id)

        #pCASL
        if s.protocol_name=='pCASL_AP': 
            if s.sequence_name=='epse2d1_86':
                info[pcasl_sefm_ap].append(s.series_id)
            elif s.sequence_name=='mbPCASL2d1_86':
                info[pcasl_vol_ap].append(s.series_id)
        if s.protocol_name=='pCASL_PA': 
            if s.sequence_name=='epse2d1_86':
                info[pcasl_sefm_pa].append(s.series_id)
            elif s.sequence_name=='mbPCASL2d1_86':
                info[pcasl_vol_pa].append(s.series_id)

    return info

# Fill the IntendedFor metadata field for fmap files
POPULATE_INTENDED_FOR_OPTS = {
        'matching_parameters': ['ImagingVolume', 'Shims'],
        'criterion': 'Closest'
}
