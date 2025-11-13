import os
import sys
import re
from pathlib import Path
import pandas as pd
import json

# Add the root directory to the Python path to enable importing from parent directory
root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)
from meta import meta_func, meta_create

meta_create()
files_to_rename_txt = meta_func("rename_others_list", "your list file containing the file paths you want to rename")

with open(files_to_rename_txt) as file:
    files_to_rename = [line.rstrip() for line in file]

files_to_discard = []

def check_bids_format(fn: str, good_fn: list, bad_fn: list) -> bool:
    """
    Check if the file name meets the BIDS standard.
    """
    name = Path(fn).name
    patron_bids = re.compile(
        r"^sub-[a-zA-Z0-9]+"
        r"(_[a-zA-Z0-9]+-[a-zA-Z0-9]+)*"
        r"_[a-zA-Z0-9]+"
        r"\.(nii\.gz|nii|json|tsv|bval|bvec|edf|set|fdt|mat)$"
    )

    if bool(patron_bids.match(name)) == False:
        good_fn.remove(fn)
        bad_fn.append(fn)
        print(f"WARNING: {fn} does not follow the BIDS standard. File renaming will be skipped.")
    return bool(patron_bids.match(name))

def check_run_entity(fn: str, good_fn: list, bad_fn: list) -> bool:
    """
    Check if the filename has a run-XX entity-label pair.
    """
    if bool(re.search(r"run-\d{2}(?!\d)", fn)) == False:
        good_fn.remove(fn)
        bad_fn.append(fn)
        print(f"WARNING: {fn} does not have a valid 'run-XX' entity-label pair. File renaming will be skipped.")
    return bool(re.search(r"run-\d{2}(?!\d)", fn))

def discard_t1_t2(fn: str, good_fn: list, bad_fn: list) -> bool:
    """
    Check if the file is not T1 nor T2.
    """
    stem = Path(fn).name.removesuffix("".join(Path(fn).suffixes))
    not_anat = True
    if stem[-3:] == "T1w" or stem[-3:] == "T2w":
        good_fn.remove(fn)
        bad_fn.append(fn)
        not_anat = False
        print(f"WARNING: {fn} is a T1 or T2 file, use rename_runs_qc_anat.py instead. File renaming will be skipped.")
    return not_anat

def discard_run00(fn: str, good_fn: list, bad_fn: list) -> bool:
    """
    Discard 'run-00' files.
    """
    no_run00 = True
    if 'run-00' in fn:
        good_fn.remove(fn)
        bad_fn.append(fn)
        no_run00 = False
        print(f"WARNING: {fn} is a 'run-00' file, therefore it has already been renamed. File renaming will be skipped.")
    return no_run00

def discard_multiple_0x(fn: str, good_fn: list, bad_fn: list) -> bool:
    """
    Discard files if there is more than one run eligible to be renamed to run-01.
    """
    fn_not_discarded = True
    patron_run = re.compile(r"(.*)_run-(\d{2})(.*)")
    m = patron_run.match(fn)
    if not m:
        return []

    preffix, run, suffix = m.groups()
    discards = []

    for f in good_fn:
        m2 = patron_run.match(f)
        if m2:
            preffix2, run2, suffix2 = m2.groups()
            if preffix2 == preffix and suffix2 == suffix:
                # Incloem totes les runs > 01
                if run2 != "01":
                    discards.append(f)
                    fn_not_discarded = False

    # Si el fitxer base no és run-01, l'afegim també
    if run != "01" and fn not in discards:
        discards.append(fn)
        fn_not_discarded = False

    discards = sorted(discards)

    for file in discards:
        good_fn.remove(file)
        bad_fn.append(file)
        print(f"WARNING: {file} can't be renamed to 'run-01' as there are multiple runs in the list. File renaming will be skipped.")
    
    return fn_not_discarded

def find_sidecars(fn: str, good_fn: list) -> list:
    """
    Find all the sidecars and image files that need to be renamed.
    """
    path = Path(fn)
    folder = path.parent
    stem = path.name.removesuffix("".join(Path(fn).suffixes))

    for sibling in folder.iterdir():
        if not sibling.is_file():
            continue

        sibling_stem = sibling.name.removesuffix("".join(sibling.suffixes))

        if (
            sibling_stem == stem
            and sibling != path
            and str(sibling) not in good_fn
        ):
            good_fn.append(str(sibling))
            print(f"\n{sibling} will also be renamed.")

    return sorted(good_fn)

def rename_01_to_00(fn:str):
    """
    Rename a 'run-01' files to 'run-00'.
    """
    path = Path(fn)
    stem = path.name
    if "run-01" in stem:
        new_name = stem.replace("run-01", "run-00")
        new_path = path.with_name(new_name)
        new_fn = str(new_path)
        print(f"\nTrying to rename {fn} -> {new_fn}")
        if new_path.exists():
            print(f"WARNING: {new_fn} already exists, therefore the renaming was already done. File renaming will be skipped.")
            return None
        else:
            try:
                path.rename(new_path)
                print(f"{fn} -> {new_fn} Successfully renamed!")
                return new_fn
            except Exception as e:
                print(f"ERROR: Could not rename {fn} -> {new_fn}. Reason: {e}")
                return None

def rename_0x_to_01(fn:str):
    """
    Rename a 'run-0x' (not run-00, not run-01) files to 'run-01'.
    """
    path = Path(fn)
    stem = path.name
    match = re.search(r"run-0([2-9])\b", stem)
    if match:
        old_run = match.group(0)
        new_name = stem.replace(old_run, "run-01")
        new_path = path.with_name(new_name)
        new_fn = str(new_path)
        print(f"\nTrying to rename {fn} -> {new_fn}")
        if new_path.exists():
            print(f"WARNING: {new_fn} still exists, so you will to also add it to the list. File renaming will be skipped.")
            return None
        else:
            try:
                path.rename(new_path)
                print(f"{fn} -> {new_fn} Successfully renamed!")
                return new_fn
            except Exception as e:
                print(f"ERROR: Could not rename {fn} -> {new_fn}. Reason: {e}")
                return None

def modify_scans_tsv(fn:str, new_fn:str):
    path = Path(fn)
    path_new = Path(new_fn)
    csv_fn = f"{path.parent.name}/{path.name}"
    csv_fn_new = f"{path_new.parent.name}/{path_new.name}"
    scans_file = list(Path(path).parent.parent.glob('*scans.tsv'))[0]
    scans_df = pd.read_csv(scans_file, sep="\t")
    scans_df.loc[scans_df['filename'] == csv_fn, 'filename'] = csv_fn_new
    scans_df.to_csv(scans_file, sep="\t", index=False)
    print(f"{csv_fn} modified to {csv_fn_new} in 'filename' column of {scans_file}")

def modify_intendedfor(fn:str, new_fn:str):
    path = Path(fn)
    new_path = Path(new_fn)
    def get_path_after_sub(full_path):
        parts = full_path.parts
        for i, part in enumerate(parts):
            if part.startswith("sub-"):
                rel_path = Path(*parts[i+1:])
                return str(rel_path)
            else:
                continue
        print(f"WARNING: {full_path} is not in a BIDS folder.")
        return None
    fn_aftersub = get_path_after_sub(path)
    new_fn_aftersub = get_path_after_sub(new_path)
    if path.parent.name == 'dwi' or path.parent.name == 'func':
        fmap_folder = path.parent.parent / "fmap"
        fmap_jsons = sorted(fmap_folder.glob("*.json"))
        for json_path in fmap_jsons:
            with open(json_path, "r") as f:
                fmap_data = json.load(f)
            intended = fmap_data.get("IntendedFor", None)
            if isinstance(intended, list) and fn_aftersub in intended:
                fmap_data["IntendedFor"] = [
                    new_fn_aftersub if x == fn_aftersub else x for x in intended
                    ]
                with open(json_path, "w") as f:
                    json.dump(fmap_data, f, indent=4)
                print(f"{fn_aftersub} modified to {new_fn_aftersub} in 'IntendedFor' field of {json_path}")

for file in files_to_rename[:]:
    print(f"\nNow processing file {file}")

    print("\nChecking if the file follows the BIDS file structure...")
    bids_check = check_bids_format(file, files_to_rename, files_to_discard)
    if bids_check == False:
        continue

    print("\nChecking if the file has a 'run' entity...")
    run_entity_check = check_run_entity(file, files_to_rename, files_to_discard)
    if run_entity_check == False:
        continue

    print("\nChecking if the file is not T1 nor T2...")
    no_t1_t2 = discard_t1_t2(file, files_to_rename, files_to_discard)
    if no_t1_t2 == False:
        continue

    print("\nChecking if the file has not been renamed before...")
    no_run_00 = discard_run00(file, files_to_rename, files_to_discard)
    if no_run_00 == False:
        continue

    print("\nChecking if the list does not contain several runs other than run-01...")
    no_multiple_0x = discard_multiple_0x(file, files_to_rename, files_to_discard)
    if no_multiple_0x == False:
        continue

    print("\nAdding image and sidecar files to the renaming list...")
    files_to_rename = find_sidecars(file, files_to_rename)

for file in files_to_rename:
    path = Path(file)
    stem = path.name
    if "run-01" in stem:
        new_file = rename_01_to_00(file)
    else:
        new_file = rename_0x_to_01(file)

    suffixes = ''.join(Path(file).suffixes)
    if suffixes == ".nii.gz":
        print("\nUpdating the scans.tsv file...")
        modify_scans_tsv(file, new_file)
    
    print("\nUpdating the fieldmaps metadata...")
    modify_intendedfor(file, new_file)


