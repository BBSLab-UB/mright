# MRIght

MRIght is a standardized MRI preprocessing and conversion pipeline. It organizes DICOMs, converts them to BIDS format, performs quality control, and runs FreeSurfer `recon-all`.

This pipeline allows you to go from raw DICOMs directly from the scanner to BIDS-compliant data with FreeSurfer recon-all outputs. It's designed to be used directly from the terminal.

## Table of Contents

- [Exporting MRI images](#exporting-mri-images)
- [Step-by-Step Workflow](#step-by-step-workflow)
  - [Install the virtual environment](#install-the-virtual-environment)
  - [1. Sort the DICOMs](#1-sort-the-dicoms)
  - [2. Convert to BIDS](#2-convert-to-bids)
  - [3. Quality Control (QC)](#3-quality-control-qc)
  - [4. Run FreeSurfer recon-all](#4-run-freesurfer-recon-all)
- [License](#license)

---
### Exporting MRI images:

1. Log in using the *usuario predeterminado* (no password required).
2. Open the patient navigator.
3. Select the subject you want to export (this automatically selects all images).  
   - Tip: You can sort by project name (e.g., sort by “BBS Lab” subjects first).
4. Click *Exportar* to open the export pop-up.
5. In the pop-up:
   - Choose your hard drive as the *Destino* using the *Examinar* button.
   - Under *Propiedades*, set:
     - *Conversión de imagen*: *mejorada*
     - *Hacer anónimo como*: *mantenimiento*
     - Tick only the *hacer anónimo como* box
     - Enter the subject ID (e.g., `4132`)

---
## Step-by-Step Workflow

### Install the virtual environment

* 
    ```bash
    conda env create -f 0-env_config/linux_environment.yml
    conda activate mright-env
    ```

---

### 1. Sort the DICOMs

* 
    ```bash
    python 1-sort/Sort_DICOMS.py
    ```

    **Prompts for:** DICOM directory, timepoint folder name (e.g., TP2)

    **Output:** Organizes images into subfolders by subject and sequence.

---

### 2. Convert to BIDS

* 
    ```bash
    python 2-convert/DICOM_to_BIDS.py
    ```

    **Prompts for:** Path to DICOM directory, timepoint folder name, path to shared BIDS directory (for determining subjects who have already been processed), path to local (temporary) BIDS output directory, path to project heuristic file (i.e., `2-convert/heuristic_general.py`).

    **Output:** Creates a BIDS-compliant dataset in the specified temporary output directory.

* 
    ```bash
    python 2-convert/move_and_merge.py
    ```

    **Prompts for:** Path to local (temporary) BIDS output directory, path to shared BIDS destination directory.

    **Output:** Moves the BIDS compliant data from a local (temporary) directory to a shared destination directory.

---

### 3. Quality Control (QC)

* 
    ```bash
    python 3-bidsqc/DICOMS_BIDS_inventory.py
    ```

    **Prompts for:** Path to shared BIDS directory, path to DICOM directory, path to recon-all directory, path to preprocessed BOLD images (enter ‘.’ if none exist), path to QC output directory, session label (e.g., 02).

    **Output:** Creates an inventory of which subjects have completed each processing step.

    > **Note:** Run this script before generating GIFs; otherwise, the GIF script will throw an error.

* 
    ```bash
    python 3-bidsqc/anat_animate.py
    ```

    **Prompts for:** Path to shared BIDS directory, path to QC output directory, session label (e.g., 02).

    **Output:** Creates T1 and T2 GIFs for manual QC inspection.

* 
    ```bash
    python 3-bidsqc/play_anat_gifs.sh
    ```

    **Behavior:** Automatically opens each GIF for manual inspection. After closing a GIF, you’ll be prompted to enter a QC rating and any comments. T1 QC ratings: 1, 2A, 2B, 3, or 4 and T2 QC ratings: 1, 2, 3, 4. 

    **Output:** Creates a .txt file with all QC ratings.
 
* 
    ```bash
    python 3-bidsqc/rename_runs_qc_anat.py
    ```

    **Prompts for:** Path to shared BIDS folder, path to QC folder, path to project heuristic file, session label (e.g., 02), sequence to rename (e.g., T1).

    **Output:** Renames T1/T2 files when a subject has two runs and run 2 is better than run 1, or when a run is rated as unusable (i.e., rated as a 4).

    > **Note:** You need to run this script after doing QC, before running recon-all, to ensure the highest quality runs are used in recon-all.

* 
    ```bash
    python 3-bidsqc/rename_runs_qc_others.py
    ```

    **Prompts for:** Path to list of individual files that need to be renamed.

    **Output:** Renames BIDS files that are not T1 nor T2, from a given list that contains their paths.

    > **Note:** This script is relevant for updating the metadata files such that BIDS standard compliance is maintained.

---

### 4. Run FreeSurfer recon-all

* 
    ```bash
    bash 4-reconall/recon-all_parallel.sh -i <BIDS_DIR> -o <FREESURFER_SUBJECTS_DIR> -p <N_CORES> [-s <session>] [-l <list_file>]
    ```

    **Arguments:** `-i` shared BIDS directory, `-o` recon-all output directory, `-p` number of cores per job, `-s` optional session ID (e.g., `ses-02`), `-l` optional list file with subject IDs; if not included, the list is automatically generated.

    **Example:**  
    ```bash
    bash 4-reconall/recon-all_parallel.sh -i /pool/guttmann/institut/UB/Superagers/MRI/BIDS -o /pool/guttmann/institut/UB/Superagers/MRI/derivatives/freesurfer-reconall -p 3 -s 02
    ```

    **Output:** Generates recon-all outputs in the specified directory.

---

## License 

MRIght © BBSLab, University of Barcelona.  

Please cite appropriately if using this pipeline in publications.
