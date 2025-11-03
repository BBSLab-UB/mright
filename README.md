# MRIght

MRIght is a standardized MRI preprocessing and conversion pipeline.  
It organizes MRI DICOMs, converts them to BIDS format, performs quality control, and runs FreeSurfer `recon-all`.

---

## Quick Overview

This pipeline allows you to go from **raw DICOMs** directly from the scanner to **BIDS-compliant data** with FreeSurfer recon-all outputs.  
It's designed to be used directly from the terminal.

---
### Before running the pipeline, export the MRI images as specified below:

**Instructions:**
1. Log in using the *usuario predeterminado* (no password required).
2. Open the patient navigator.
3. Select the subject you want to export (this automatically selects all images).  
   - Tip: You can sort by project name (e.g., sort by “BBS Lab” subjects first).
4. Click **Exportar** to open the export window.
5. In the pop-up:
   - Choose your **hard drive** as the “Destino” using the **Examinar** button.
   - Under **Propiedades**, set:
     - **Conversión de imagen:** *mejorada*
     - **Hacer anónimo como:** *mantenimiento*
     - Tick only **“hacer anónimo como”**
     - Enter the **subject ID** (e.g., `4132`).

---

## Installation for the pipeline

### Linux
```bash
conda env create -f 0-env_config/linux_environment.yml
conda activate mright-env
```
This installs all dependencies including **HeuDiConv**, **dcm2niix**, and **FreeSurfer tools**.

---

## Step-by-Step Workflow

### 1. Sort the DICOMs

Organize DICOMs by series and sequence.

```bash
python 1-sort/Sort_DICOMS.py
```

**You’ll be prompted for:**
- Path to DICOM directory.
- Timepoint folder name (e.g., TP2)

**Output:**  
Organizes subfolders by subject and sequence.

---

### 2. Convert to BIDS

Convert the sorted DICOMs to BIDS format using HeuDiConv.

```bash
python 2-convert/DICOM_to_BIDS.py
```

**You’ll be prompted for:**
- Path to DICOM directory
- Timepoint folder name
- Path to shared BIDS directory (for determining subjects who have already been processed)
- Path to local (temporary) BIDS output directory  
- Path to project heuristic file (e.g., `2-convert/heuristic_general.py`)  

**Output:**  
Creates a BIDS-compliant dataset in the specified temporary output directory.

Then move and merge it into the shared BIDS folder:

```bash
python 2-convert/move_and_merge.py
```

**You’ll be prompted for:**
- Path to local (temporary) BIDS output directory  
- Path to shared BIDS destination directory

**Output:**  
Moves the BIDS compliant data from a local (temporary) directory to a shared destination directory.
---

### 3. Quality Control (QC)

Run quick checks to verify conversions and data integrity.

#### Inventory Check
```bash
python 3-bidsqc/DICOMS_BIDS_inventory.py
```
**You’ll be prompted for:**
- Path to shared BIDS directory  
- Path to DICOM directory  
- Path to recon-all directory
- Path to preprocessed BOLD images (enter ‘.’ if none exist)
- Path to QC output directory
- Session label (e.g., 02)

**Output:**  
Creates an inventory of which subjects have completed each processing step.

> **Note:** Run this script before generating GIFs; otherwise, the GIF script will throw an error.

#### Generate Anatomical GIFs
```bash
python 3-bidsqc/anat_animate.py
```
**You’ll be prompted for:**
- Path to shared BIDS directory 
- Path to QC output directory 
- Session label (e.g., 02)

**Output:**  
Creates T1 and T2 GIFs for manual QC inspection.

#### Run QC Review
```bash
python 3-bidsqc/play_anat_gifs.sh
```
**Behavior:**  
This script automatically opens each GIF for manual inspection.  
After closing a GIF, you’ll be prompted to enter a QC rating and any comments.

**Output:**  
Creates a .txt file with all QC ratings.

#### Update Filenames Post-QC
```bash
python 3-bidsqc/rename_runs_qc_anat.py
```
**You’ll be prompted for:**
- Path to shared BIDS folder  
- Path to QC folder 
- Path to project heuristic file
- Session label (e.g., 02)
- The sequence you want to rename (e.g., T1)

**Output:**  
Renames BIDS files where run 2 is better than run 1. 

> **Note:** You need to run this script after doing QC, before running recon-all, to ensure the highest quality runs are used in recon-all.

---

### 4. Run FreeSurfer recon-all

Run FreeSurfer `recon-all` in parallel for all subjects and sessions. 

```bash
bash 4-reconall/recon-all_parallel.sh -i <BIDS_DIR> -o <FREESURFER_SUBJECTS_DIR> -p <N_CORES> [-s <session>] [-l <list_file>]
```

**Arguments:**
- `-i`: Shared BIDS directory 
- `-o`: Recon-all output directory
- `-p`: Number of cores per job
- `-s`: Optional session ID (e.g., `ses-02`)
- `-l`: Optional list file with subject IDs; if not included, the list is automatically generated.

**Example:**
```bash
bash 4-reconall/recon-all_parallel.sh -i /pool/guttmann/institut/UB/Superagers/MRI/BIDS -o /pool/guttmann/institut/UB/Superagers/MRI/freesurfer-reconall -p 3 -s 02
```

**Output:**  
Generates recon-all outputs in the specified directory.

---

## License and Citation

MRIght © BBSLab, University of Barcelona.  

Please cite appropriately if using this pipeline in publications.

---
