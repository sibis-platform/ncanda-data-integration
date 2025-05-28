#!/usr/bin/env python
"""
Use make_redcap_inventory to make all available inventories
"""

import argparse
from make_redcap_inventory import make_redcap_inventory
import os
from pathlib import Path
import pdb
import sibispy
from sibispy import sibislogger as slog
import sys
from typing import List


def parse_args(input_args: List = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Verbose operation",
                        action="store_true")
    parser.add_argument("-p", "--post-to-github",
                        help="Post all issues to GitHub instead of stdout.",
                        action="store_true")
    parser.add_argument("-f", "--forms",
                        nargs='*')
    parser.add_argument("-e", "--events",
                        nargs='*')
    parser.add_argument('-o', '--output-dir',
                        help="Output directory for all inventories")
    parser.add_argument('-d', '--split-by-dag-to', dest='output_dag_dir',
                        help="Output directory for inventories split by DAG",
                        required=False, default=None)
    parser.add_argument('-s', '--api',
                        help="Source Redcap API to use",
                        default="data_entry")
    parser.add_argument('-a', '--arm',
                        help="What arm to export events from?",
                        default="1")
    args = parser.parse_args(input_args)
    return args


def main(args):
    # 1. export_fem to get event-form connections
    # 2. Optional: filter through the FEM based on CLI args
    # 3. for each event, create all needed subdirectories
    # 4. for each event/form, call make_redcap_inventory and write out full
    #    report to created subdir
    # 5. optionally, if --split-by-dag is called, split the received inventory
    #    by DAG
    args = parse_args()
    session = sibispy.Session()
    if not session.configure():
        sys.exit()

    slog.init_log(verbose=args.verbose,
                  post_to_github=args.post_to_github,
                  github_issue_title='QC: Save content stats for all forms',
                  github_issue_label='inventory',
                  timerDir=None)

    api = session.connect_server(args.api, timeFlag=True)

    # get form event mappings
    if args.arm:
        fem = api.export_instrument_event_mappings(format_type='df', arms=[args.arm])
    else:
        fem = api.export_instrument_event_mappings(format_type='df')

    if args.events:
        fem = fem.loc[fem['unique_event_name'].isin(args.events)]
        if fem.empty:
            print("No such events! {}".format(args.events))
            sys.exit(1)

    if args.forms:
        fem = fem.loc[fem['form'].isin(args.forms)]
        if fem.empty:
            print("No such forms! {}".format(args.forms))
            sys.exit(1)

    # check that target dir(s) are writable
    output_dir = Path(args.output_dir)
    __check_dir(output_dir)

    output_by_dag_dir = None
    if args.output_dag_dir:
        output_by_dag_dir = Path(args.output_dag_dir)
        __check_dir(output_by_dag_dir)

    # create directory for event
    for _, row in fem.iterrows():
        form = row['form']
        event = row['unique_event_name']
        if args.verbose:
            print(F"{form} / {event}: Beginning inventory")
        inventory = make_redcap_inventory(api=api,
                                          forms=[form],
                                          events=[event],
                                          post_to_github=args.post_to_github,
                                          include_dag=True,
                                          verbose=args.verbose)
        if inventory.empty:
            if args.verbose:
                print("\tNothing to inventorize!")
            continue

        target_dir = output_dir / event
        target_dir.mkdir(mode=0o775, exist_ok=True)

        target_path = target_dir / F"{form}.csv"
        if args.verbose:
            print(F"\tWriting inventory to {target_path}...")
        inventory.to_csv(target_path)

        # split by DAG:

        # 1. extract available DAGs from inventory, if any
        # 2. iterating over DAGs, subset the inventory dataframe
        # 3. if needed, create DAG subdir: output_by_dag_dir / dag / event
        # 4. if non-empty, save to output_by_dag_dir / dag / event / form
        if output_by_dag_dir:
            all_dags = (inventory['dag']
                        .drop_duplicates().tolist())
            if args.verbose:
                print(F"{form} / {event}: Subdividing by DAG, available DAGs: "
                      F"{all_dags}")

            for dag in all_dags:
                # TODO: Should really extract this logic into a separate code,
                # since it's an almost exact replica of the logic that's saving
                # the full inventory above
                dag = str(dag)
                target_dag_dir = output_by_dag_dir / dag / event
                target_dag_dir.mkdir(mode=0o775, parents=True, exist_ok=True)

                target_dag_path = target_dag_dir / F"{form}.csv"
                (inventory.loc[inventory['dag'] == dag]
                 .to_csv(target_dag_path))
                if args.verbose:
                    print(F"\tWriting {dag}-specific inventory to "
                          F"{target_dag_path}...")
    return 0


def __check_dir(dirpath: Path):
    try:
        dirpath.mkdir(mode=0o775, parents=True, exist_ok=True)
    except (IOError, PermissionError):
        sys.exit(F"{dirpath} could not be created!")

    assert dirpath.is_dir(), F"{dirpath} is not a directory!"
    assert os.access(dirpath, os.W_OK), F"{dirpath} is not writable!"


if __name__ == '__main__':
    args = parse_args()
    sys.exit(main(args))
