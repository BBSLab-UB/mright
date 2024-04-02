############################################
#######  SUPERAGERS HEURISTIC FILE  ########
#######       BBSLab Mar 2024       ########
############################################

# Heuristic file ONLY for Superagers project, not for general use

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
    
    t1w=create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:02d}_T1w')
    t2w=create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:02d}_T2w')
    flair=create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_run-{item:02d}_FLAIR')
    
    rest_bold_ap=create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-rest_dir-ap_run-{item:02d}_bold')
    rest_sbref_ap=create_key('sub-{subject}/{session}/func/sub-{subject}_{session}_task-rest_dir-ap_run-{item:02d}_sbref')
    rest_sefm_ap=create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-func_dir-ap_run-{item:02d}_sefm')
    rest_sefm_pa=create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-func_dir-pa_run-{item:02d}_sefm')

    dwi_dir_ap=create_key('sub-{subject}/{session}/dwi/sub-{subject}_{session}_dir-ap_run-{item:02d}_dwi') 
    dwi_dir_pa=create_key('sub-{subject}/{session}/dwi/sub-{subject}_{session}_dir-pa_run-{item:02d}_dwi') 
    dwi_sefm_ap=create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-dwi_dir-ap_run-{item:02d}_sefm')
    dwi_sefm_pa=create_key('sub-{subject}/{session}/fmap/sub-{subject}_{session}_acq-dwi_dir-pa_run-{item:02d}_sefm')
    
    # dictionary: list of DICOMs for each BIDS file
    info =  {
                    t1w:[],
                    t2w:[],
                    flair:[],
                    rest_bold_ap:[],
                    rest_sbref_ap:[],
                    rest_sefm_ap:[],
                    rest_sefm_pa:[],
                    dwi_dir_ap:[],
                    dwi_dir_pa:[],
                    dwi_sefm_ap:[],
                    dwi_sefm_pa:[],
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
        elif s.protocol_name=='SPECHOGFMA-P':
            info[rest_sefm_ap].append(s.series_id)
        elif s.protocol_name=='SPECHOGFMP-A':
            info[rest_sefm_pa].append(s.series_id)
            
        #dwi
        if s.protocol_name=='cmrr_mbep2d_diff_99A-P':
            if s.sequence_name=='epse2d1_140':
                 info[dwi_sefm_ap].append(s.series_id)
            else:
                 info[dwi_dir_ap].append(s.series_id)
        if s.protocol_name=='cmrr_mbep2d_diff_99P-A':
            if s.sequence_name=='epse2d1_140':
                 info[dwi_sefm_pa].append(s.series_id)
            else:
                 info[dwi_dir_pa].append(s.series_id)

    return info
