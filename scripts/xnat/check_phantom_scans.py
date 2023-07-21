#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

from __future__ import print_function
from builtins import str
import os
import re
import json
import time
import argparse
import datetime
from typing import Sequence
import yaml
import sys

import sibispy
from sibispy import sibislogger as slog
from sibispy import sibis_email, xnat_util
from settings import XNAT_DATE_FORMAT


#
# Functions
#

PHANTOM_DAY_LIMIT = 7

# Find a phantom scan within 24h of the given experiment
def find_phantom_scan_24h(
    prj,
    experiment_label,
    seid,
    xnat_url,
    experiment_last_modified,
    phantom_id,
    edate,
    etime,
    scanner,
    args,
    email,
):
    # Compute the date before and after the experiment date
    today = datetime.datetime.today()
    today_str = today.strftime("%Y-%m-%d")
    this_date = datetime.datetime.strptime(edate, "%Y-%m-%d")
    edate_tomorrow = (this_date + datetime.timedelta(PHANTOM_DAY_LIMIT)).strftime(
        "%Y-%m-%d"
    )
    edate_yesterday = (this_date - datetime.timedelta(PHANTOM_DAY_LIMIT)).strftime(
        "%Y-%m-%d"
    )
                    
    # Simple approach: search only on dates (meaning we might accidentally pick
    # something that's N days + M hours later):
    # constraints = [('xnat:mrSessionData/SUBJECT_ID', 'LIKE', phantom_id), 'AND',
    #                [('xnat:mrSessionData/DATE', '>=', edate_yesterday),
    #                 ('xnat:mrSessionData/DATE', '<=', edate_tomorrow),
    #                 'AND']]

    # Full approach:
    # eligible phantom happens *either*
    # - ON the upper/lower bound dates, at which point time matters, OR
    # - BETWEEN lower and upped bound dates, in which case we just need DATE to
    #   be greater than lower bound and smaller than upper bound.
    constraints = [
        ("xnat:mrSessionData/SUBJECT_ID", "LIKE", phantom_id),
        "AND",
        [
            [
                [
                    ("xnat:mrSessionData/DATE", "=", edate_yesterday),
                    ("xnat:mrSessionData/TIME", ">=", etime),
                    "AND",
                ],
                [
                    ("xnat:mrSessionData/DATE", "=", edate_tomorrow),
                    ("xnat:mrSessionData/TIME", "<=", etime),
                    "AND",
                ],
                "OR",
            ],
            [
                [
                    ("xnat:mrSessionData/DATE", ">", edate_yesterday),
                    ("xnat:mrSessionData/DATE", "<", edate_tomorrow),
                    "AND",
                ]
            ],
            "OR",
        ],
    ]

    phantom_scans = list(
        ifc.search(
            "xnat:mrSessionData",
            [
                "xnat:mrSessionData/SESSION_ID",
                "xnat:mrSessionData/DATE",
                "xnat:mrSessionData/TIME",
            ],
        )
        .where(constraints)
        .items()
    )

    # Still haven't found anything - then there is no phantom scan
    if (len(phantom_scans) == 0) and (today_str >= edate_tomorrow):
        if args.sendmail:
            email.add_admin_message(
                "%s %s - no phantom scan for %s, last modified %s (scanner: %s)"
                % (prj, edate, experiment_label, experiment_last_modified, scanner)
            )
        else:
            error = "No phantom scan."
            try:
                dag = prj.replace("_incoming", "")
            except AttributeError:
                dag = None

            slog.info(
                experiment_label,
                error,
                project_id=prj,
                experiment_id=seid,
                xnat_url=xnat_url,
                experiment_date=edate,
                search_range=[edate_yesterday,edate_tomorrow],
                site_forward=dag,
                site_resolution="If a phantom exists within the "
                f"{PHANTOM_DAY_LIMIT}-day limit, please upload it to "
                "XNAT. If a phantom does not exist within this limit, "
                "please inform the Datacore so that they can set the "
                "respective XNAT flag. If you believe a phantom scan exists, make sure its subject id is '" +  phantom_id +"'",
            )
    else:
        if args.warn_same_day_phantom:
            if args.sendmail:
                email.add_admin_message(
                    "%s %s - no same-day phantom scan for %s, last modified %s (scanner: %s), but found one within %d days"
                    % (
                        prj,
                        edate,
                        experiment_label,
                        experiment_last_modified,
                        scanner,
                        PHANTOM_DAY_LIMIT,
                    )
                )
            else:
                error = (
                    "ERROR: no same-day phantom scan for session acquired;But found one within %dd"
                    % PHANTOM_DAY_LIMIT
                )
                slog.info(
                    experiment_label,
                    error,
                    project_id=prj,
                    experiment_date=edate,
                    experiment_last_modified=experiment_last_modified,
                    scanner=scanner,
                )

    # Sanity-check that we're detecting scans with pending phantoms
    if (len(phantom_scans) == 0) and (today_str < edate_tomorrow) and args.verbose:
        print(
            "{}: No phantom, but site has until {} to upload one.".format(
                seid, edate_tomorrow
            )
        )


# Check one experiment for matching phantom scans
def check_experiment(session, ifc, sibis_config, args, email, eid, xnat_url, experiment):
    expUtil = xnat_util.XNATSessionElementUtil(experiment)
    try:
        experiment_last_modified = expUtil.get("last_modified")
        if experiment_last_modified == "":
            experiment_last_modified = expUtil.get("insert_date")
        date_last_modified = time.strptime(
            experiment_last_modified[0:19], XNAT_DATE_FORMAT
        )  # truncate ".###" fractional seconds by using only 0..19th characters
    except:
        # default to right now
        date_last_modified = time.localtime()

    experiment_last_modified = ""

    try:
        prj, sid, seid, experiment_label, edate, etime, scanner = expUtil.mget(
            ["project", "subject_ID", "ID", "label", "date", "time", "scanner"]
        )
    except:
        error = "ERROR: failed to get data for experiment"
        slog.info(
            eid,
            error,
            info="Please check if eid still exists in xnat. If not ignore error and otherwise run ./check_phantom_scans -e "
            + eid,
            xnat_url=xnat_url
        )
        return False

    # RegExp pattern for subject IDs
    subject_id_pattern_nophantom = "^([A-F])-[0-9]{5}-[MF]-[0-9]$"
    subject_label_match = re.match(
        subject_id_pattern_nophantom,
        session.xnat_get_subject_attribute(prj, sid, "label")[0],
    )
    if subject_label_match:
        # This is a dictionary that maps subjects who changed sites to the correct phantom.
        with open(os.path.join(sibis_config, "special_cases.yml"), "r") as fi:
            site_change_map = yaml.safe_load(fi).get("site_change")
            phantom_scan_map = site_change_map.get("check_phantom_scans")

        changed_sites_phantom = phantom_scan_map.get(experiment_label)
        try:
            # If the subject changed sites, then use the correct site phantom ID.
            if changed_sites_phantom:
                phantom_label = changed_sites_phantom
                if args.verbose:
                    print("Phantom switched sites - checking ", phantom_label)
            else:
                phantom_label = "%s-99999-P-9" % subject_label_match.group(1)

            [phantom_id, issue_url] = session.xnat_get_subject_attribute(
                prj, phantom_label, "ID"
            )
            if not phantom_id:
                slog.info(
                    eid,
                    "Could not get phantom id for phantom " + phantom_label,
                    project_id=prj,
                    phantom=phantom_label,
                    related_issues=issue_url,
                    cmd=" ".join(sys.argv),
                )
                return False

            try:
                phantom_scans = ifc.array.experiments(experiment_type='xnat:mrSessionData', constraints={ 'xnat:mrSessionData/subject_id':phantom_id, 'date': edate})
            except Exception as e:
                error=f"Failed to retrieve phantom scan with id {phantom_id} on {edate}."
                slog.info(experiment_label,error,
                          site_id=sid,
                          project=prj,
                          subject_experiment_id=seid,
                          error_msg = str(e) )
                return False

            # handle check for phantoms on the same day but wrong scanner
            eids = phantom_scans.get("ID", always_list=True)
            phantom_scanners = [
                ifc.select.experiments[eid].get("scanner") for eid in eids
            ]
            if args.verbose:
                print("Phantom scans: {0}".format(phantom_scans))
                
            if scanner not in phantom_scanners and len(phantom_scans) != 0:

                err = "Error: {0} - scanner mismatch for session {1} (scanner: {2}) and phantom {3} (scanner: {4}).".format(
                    prj, experiment_label, scanner, eids, phantom_scanners
                )
                slog.info(
                    experiment_label,
                    err,
                    phantom_experiment_id=eids,
                    experiment_xnat_id=seid,
                    xnat_url=xnat_url,
                    project=prj,
                )
            elif len(phantom_scans) == 0:
                find_phantom_scan_24h(
                    prj,
                    experiment_label,
                    seid,
                    xnat_url,
                    experiment_last_modified,
                    phantom_id,
                    edate,
                    etime,
                    scanner,
                    args,
                    email,
                )
        except IndexError as e:
            error = "ERROR: Subject likely switched sites if site_id > NCANDA_S01010"
            slog.info(
                experiment_label,
                error,
                site_id=sid,
                project=prj,
                changed_sites_phantom=str(changed_sites_phantom),
                subject_experiment_id=seid,
                xnat_url=xnat_url,
                info="Most likely entry missing for this visit in section 'check_phantom_scans' of file 'special_cases.yml'",
                error_msg=str(e),
            )


def _parse_args(input_args: Sequence[str] = None) -> argparse.Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--send-mail",
        action="store_true",
        dest="sendmail",
        default=False,
        help="Send emails with problem reports to users and site admin.",
    )
    parser.add_argument(
        "-a",
        "--check-all",
        action="store_true",
        dest="check_all",
        default=False,
        help="Check all sessions, regardless of modification date.",
    )
    parser.add_argument(
        "-w",
        "--warn-same-day-phantom",
        action="store_true",
        dest="warn_same_day_phantom",
        default=False,
        help="Warn if no same-day ADNI phantom scan was found "
        "(default: warn only if no phantom scan within 24h).",
    )
    parser.add_argument(
        "-e",
        "--experiment-id",
        dest="eid",
        default=False,
        help="Check only session indicated, regardless of modification date.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Turn on verbose reporting.",
    )
    parser.add_argument(
        "-p",
        "--post-to-github",
        help="Post all issues to GitHub instead of std out.",
        action="store_true",
    )

    parser.add_argument(
        "-t",
        "--time-log-dir",
        help="If set then time logs are written to that directory",
        action="store",
        default=None,
    )
    args = parser.parse_args()
    return args


def _initialize(args: argparse.Namespace) -> sibispy.Session:
    """
    Initialize sibispy.Session and start the logger
    """
    slog.init_log(
        verbose=args.verbose,
        post_to_github=args.post_to_github,
        github_issue_title="NCANDA_XNAT",
        github_issue_label="check_phantom_scans",
        timerDir=args.time_log_dir,
    )

    session = sibispy.Session()
    if not session.configure():
        raise RuntimeError("sibispy is not configured; aborting!")
        sys.exit(1)

    return session


# =============================================================
# MAIN Section
# =============================================================
if __name__ == "__main__":
    args = _parse_args()
    session = _initialize(args)
    slog.startTimer1()

    # Get the sibis config
    sibis_config = session.get_operations_dir()
    if not sibis_config:
        if args.verbose:
            print("Error: Could not retrieve configuration")

        sys.exit()

    # Create interface using stored configuration
    if args.verbose:
        print("Connecting to XNAT...")
    ifc = session.connect_server("xnat", True)

    if not ifc:
        if args.verbose:
            print("Error: Could not connect to XNAT")

        sys.exit()

    ifc._memtimeout = 0

    # Date format for XNAT dates
    now_str = time.strftime(XNAT_DATE_FORMAT)

    # Set up email object to contact users and admin
    email = sibis_email.xnat_email(session)

    # Date (and time) when we last checked things
    date_last_checked = time.localtime(0)
    config_uri = "/data/config/pyxnat/check_phantom_scans"
    try:
        content = ifc._exec(config_uri, format="json")
        creation_date = json.loads(content)["ResultSet"]["Result"][0]["create_date"]
        date_last_checked = time.strptime(creation_date[0:19], XNAT_DATE_FORMAT)
        if args.verbose:
            print(
                "Last checked on: {0}".format(
                    time.strftime(XNAT_DATE_FORMAT, date_last_checked)
                )
            )
    except:
        pass

    experiment_ids = list()
    count_phantom = 0

    if args.eid:
        experiment_ids.append(args.eid)
    else:
        # Get a list of all MR imaging sessions
        experiment_ids = list(ifc.select.experiments)

    for eid in experiment_ids:
        xnat_url = session.get_xnat_session_address(eid, 'html')
        # For each experiment, see if the override variable is set. Otherwise check it
        try:
            experiment = ifc.select.experiments[eid]
        except KeyError as e:
            slog.info(
                eid,
                "ERROR: failed to retrieve experiment from XNAT",
                info="Please check if eid still exists in xnat. If not ignore error and otherwise run ./check_phantom_scans -e "
                + eid,
                xnat_url=xnat_url,
                error_msg=str(e),
            )
            continue

        # Do not change to True ! as xnat saves it as 'true'
        if experiment.fields.get("phantommissingoverride") != "true":
            count_phantom += 1
            check_experiment(session, ifc, sibis_config, args, email, eid, xnat_url, experiment)

    if args.sendmail:
        email.send_all(ifc)

    uri_addr = "%s?inbody=true" % config_uri
    try:
        with sibispy.session.Capturing() as xnat_output:
            content = ifc._exec(
                uri=uri_addr,
                method="PUT",
                body=now_str,
                headers={"content-type": "text/plain"},
            )
    except Exception as e:
        slog.info(
            eid,
            "Warning: failed to update XNAT server location " + uri_addr,
            error_msg=str(e),
            xnat_url=xnat_url,
            xnat_api_output=xnat_output,
        )

    slog.takeTimer1(
        "script_time", "{'TotalCheckedPhantoms': " + str(count_phantom) + "}"
    )
