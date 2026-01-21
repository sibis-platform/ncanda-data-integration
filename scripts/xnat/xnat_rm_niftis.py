#!/usr/bin/env python3

"""
Script is to remove niftis from XNAT
Input is a 2 column csv file that contains SID-datestring xnat session label, nifti to be deleted
    e.g.: C-70002-F-4-20130315,1_ncanda-mlalcpic-v1
Alternatively can pass specific eid and niftis.
Original command example to generate said csv: 
    ls -lad duke_incoming/arc001/*/RESOURCES/nifti/*mlalcpic*/image1.nii.gz | grep Jan | grep 2025 | tr -s ' ' | cut -d' ' -f9 | tr '/' ',' | cut -d, -f3,6 
"""

import sys
import re
import yaml
import pandas as pd
import numpy as np
import pathlib
import argparse

import sibispy
from sibispy import config_file_parser as cfg_parser
from sibispy import sibislogger as slog
from sibispy.xnat_util import XNATSessionElementUtil, XNATExperimentUtil, XNATResourceUtil

def file_relpath(f) -> str:
    """
    In your xnatpy build, FileData.id is the full relative path like:
      '1_ncanda-mlalcpic-v1/image1.nii.gz'
    """
    v = getattr(f, "id", None)
    if v:
        return str(v)

    # fallbacks (rarely needed)
    for attr in ("path", "filepath", "name"):
        v = getattr(f, attr, None)
        if v:
            return str(v)
    return str(f)


def delete_nifti_files(ifc, nifti_files_to_delete: pd.DataFrame, dry_run: bool = True, verbose: bool = False) -> None:
    """
    Deletes files by URI. If dry_run=True, only prints what would be deleted.
    """
    if nifti_files_to_delete.empty:
        print("No nifti files matched; nothing to do.")
        return

    # Use the underlying xnatpy session
    xnat_sess = ifc.client if hasattr(ifc, "client") else ifc

    for _, row in nifti_files_to_delete.iterrows():
        uri = row["file_uri"]
        eid = row["eid"]
        rel = row["file_relpath"]

        if dry_run:
            print(f"DRY RUN: would delete {eid}: {rel} ({uri})")
            continue

        if verbose:
            print(f"Deleting {eid}: {rel} ({uri})")

        xnat_sess.delete(uri)


def _res_label(res: dict) -> str:
    return (res.get("label")
            or res.get("xnat:abstractResource/label")
            or res.get("xnat:resource/label")
            or "")

def _res_id(res: dict) -> str | None:
    # most common key in ncanda scripts:
    return (res.get("xnat_abstractresource_id")
            or res.get("xnat:abstractResource/id")
            or res.get("ID")
            or res.get("id"))

def _file_name(f: dict) -> str:
    """
    Return relpath under the resource.
    On your XNAT, dict['Name'] is just the basename, but URI contains
    '<nifti_label>/<filename>' after '/files/'.
    """
    uri = f.get("URI") or f.get("uri") or ""
    if "/files/" in uri:
        return uri.split("/files/", 1)[1].lstrip("/")

    # fallback 
    nm = f.get("Name") or f.get("name") or ""
    return str(nm).lstrip("/")


def _file_uri(f: dict) -> str:
    return str(f.get("URI") or f.get("uri") or "")

def get_resource_id_by_label(xnat, eid: str, wanted_label: str = "nifti") -> str | None:
    resources = xnat._get_json(f"/data/experiments/{eid}/resources/") or []
    wanted = wanted_label.lower()
    for r in resources:
        if _res_label(r).lower() == wanted:
            return _res_id(r)
    return None

def list_resource_files_json(xnat, eid: str, resource_id: str):
    return xnat._get_json(f"/data/experiments/{eid}/resources/{resource_id}/files") or []

def build_nifti_files_to_delete_df_json(xnat, niftis_to_remove: pd.DataFrame, resource_label: str = "nifti") -> pd.DataFrame:
    """
    Input:  niftis_to_remove: columns ['eid','nifti_label']
    Output: rows per file under RESOURCES/nifti/<nifti_label>/...
            ['eid','nifti_label','resource_id','file_relpath','file_uri']
    """
    rows = []
    missing_resource = []
    missing_nifti_label = []

    # cache resource id per eid so we only hit /resources once per eid
    rid_cache: dict[str, str | None] = {}

    for eid, grp in niftis_to_remove.groupby("eid", sort=True):
        wanted = set(grp["nifti_label"].astype(str).tolist())
        found = set()

        rid = rid_cache.get(eid)
        if rid is None and eid not in rid_cache:
            rid = get_resource_id_by_label(xnat, eid, resource_label)
            rid_cache[eid] = rid

        if not rid:
            missing_resource.append(eid)
            continue

        # ONE /files call per eid
        files = list_resource_files_json(xnat, eid, rid)

        # ONE pass through files; treat "folder" as Name.split('/')[0]
        for f in files:
            rel = _file_name(f)
            if not rel or "/" not in rel:
                continue
            folder = rel.split("/", 1)[0]
            if folder not in wanted:
                continue

            found.add(folder)
            row = {
                    "eid": eid,
                    "nifti_label": folder,
                    "resource_id": str(rid),
                    "file_relpath": rel,
                    "file_uri": _file_uri(f),
                }
            print(f"Found {row}")
            rows.append(row)

        for nifti_label in sorted(wanted - found):
            missing_nifti_label.append((eid, nifti_label))

    out = (
        pd.DataFrame(rows, dtype=str)
        .sort_values(["eid", "nifti_label", "file_relpath"])
        .reset_index(drop=True)
    )

    if missing_resource:
        print(f"WARNING: missing RESOURCES/{resource_label} for EIDs: {sorted(set(missing_resource))}")

    if missing_nifti_label:
        sample = "\n  ".join([f"{e},{n}" for e, n in missing_nifti_label[:25]])
        print("WARNING: no files matched some (eid,nifti_label) (showing up to 25):\n  " + sample)

    return out


def get_experiment(ifc, eid: str):
    # xnatpy experiment object
    return ifc.select.experiments(eid)

EID_RE = re.compile(r"^[A-Za-z]+_E\d+$")  # e.g. NCANDA_E00001

def resolve_to_eid_sibis(sibis_session, token: str) -> str | None:
    """
    Accepts either experiment ID (NCANDA_E00001) or session label (C-70002-F-4-20130315).
    Returns experiment ID (EID) or None if not found.
    """
    token = (token or "").strip()
    if not token:
        return None

    # If it already looks like an EID, try it directly first
    if EID_RE.match(token):
        exp = sibis_session.xnat_get_experiment(token)
        return exp.id if exp else None

    # Otherwise treat as label (xnat_get_experiment handles this too)
    exp = sibis_session.xnat_get_experiment(token)
    return exp.id if exp else None


def build_niftis_to_remove_df(args, sibis_session) -> pd.DataFrame:
    # Read input to a normalized df with: session_or_eid, nifti_label
    if args.src:
        df = pd.read_csv(args.src, header=None, names=["session_or_eid", "nifti_label"], dtype=str)
    else:
        niftis = [s.strip() for s in (args.niftis or "").split(",") if s.strip()]
        df = pd.DataFrame({"session_or_eid": [args.eid.strip()] * len(niftis), "nifti_label": niftis}, dtype=str)

    df["session_or_eid"] = df["session_or_eid"].astype(str).str.strip()
    df["nifti_label"] = df["nifti_label"].astype(str).str.strip()
    df = df.replace({"": np.nan}).dropna(subset=["session_or_eid", "nifti_label"])

    if df.empty:
        raise RuntimeError("No rows found in deletion list after cleaning.")

    # Resolve to eid with caching
    uniq = df["session_or_eid"].unique().tolist()
    eid_map = {t: resolve_to_eid_sibis(sibis_session, t) for t in uniq}
    df["eid"] = df["session_or_eid"].map(eid_map)

    bad = df["eid"].isna()
    if bad.any():
        missing = sorted(df.loc[bad, "session_or_eid"].unique().tolist())
        raise RuntimeError(
            "Could not resolve the following to an XNAT experiment ID:\n  " + "\n  ".join(missing)
        )

    out = (
        df.loc[:, ["eid", "nifti_label"]]
          .drop_duplicates()
          .sort_values(["eid", "nifti_label"])
          .reset_index(drop=True)
    )
    return out


def set_config():
    """Set config file location to default and read in values"""
    config_path = pathlib.Path("/home/ncanda/.sibis/.sibis-general-config.yml")
    if not config_path.is_file():
        print(f"ERROR: Couldn't access config file at {config_path}")
        sys.exit(1)

    config_data = cfg_parser.config_file_parser()
    err_msg = config_data.configure(config_path)
    if err_msg:
        print("Error:post_issues_to_github: Reading config file " + config_path + " (parser tried reading: " + config_data.get_config_file() + ") failed: " + str(err_msg))

        return None

    return config_data


def main():
    parser = argparse.ArgumentParser(description="Remove bad niftis from XNAT based on SID-datestring session label and n" )
    # Input either needs to be a csv file containing the list of sessions and niftis to delete or individual eid and list of comma separated niftis
    mx = parser.add_mutually_exclusive_group(required=True)
    mx.add_argument("-src", help="Path to 2-col CSV: <session_label>,<nifti_label>", action="store")
    mx.add_argument("-eid", help="XNAT experiment ID of session", action="store")
    parser.add_argument("-n", "--niftis", help="Comma-separated nifti labels to delete (required with -eid)")
    parser.add_argument("-v", "--verbose", help="Verbose operation", action="store_true")    
    parser.add_argument(
        "--dry-run",
        help="Do not delete anything; only print what would be deleted (default).",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "--delete",
        help="Actually delete the matched nifti files (disables --dry-run).",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    if args.delete:
        args.dry_run = False

    if args.eid and not args.niftis:
        parser.error("-eid requires -n/--niftis")

    # define config file (for now is just set to default sibis-general-config location)
    config_data = set_config()

    # connect to xnat
    slog.init_log()

    sibis_session = sibispy.Session()
    if not sibis_session.configure():
        print("Error: session configure file was not found")

        sys.exit()

    ifc = sibis_session.connect_server("xnat", True)
    if not ifc:
        print("Error: Could not connect to XNAT")
        sys.exit()

    # create df list of sessions and niftis to delete
    niftis_to_remove = build_niftis_to_remove_df(args, sibis_session)
    if args.verbose:
        print(f"Built list of {len(niftis_to_remove)} niftis to delete")

    # niftis_to_remove: columns ['eid','nifti_label']
    xnat = ifc   # same thing, just naming
    nifti_files_to_delete = build_nifti_files_to_delete_df_json(xnat, niftis_to_remove, resource_label="nifti")


    if args.verbose:
        print(f"niftis_to_remove rows: {len(niftis_to_remove)}")
        print(f"nifti_files_to_delete rows: {len(nifti_files_to_delete)}")
        if not nifti_files_to_delete.empty:
            print("Example first 10 rows:")
            print(nifti_files_to_delete.head(10).to_string(index=False))

    # Always show a short summary
    print(f"Matched {len(nifti_files_to_delete)} nifti files across "
        f"{nifti_files_to_delete['eid'].nunique() if not nifti_files_to_delete.empty else 0} sessions.")

    # Do the deletions (or dry run prints)
    delete_nifti_files(ifc, nifti_files_to_delete, dry_run=args.dry_run, verbose=args.verbose)

if __name__ == "__main__":
    main()
