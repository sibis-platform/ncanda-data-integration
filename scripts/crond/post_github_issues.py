#!/usr/bin/env python

##
##  Copyright 2015 SRI International
##  License: https://ncanda.sri.com/software-license.txt
##
##  $Revision$
##  $LastChangedBy$
##  $LastChangedDate$
##
"""
Post GitHub Issues
------------------

Take the stdout and stderr passed to the catch_output_email and create an issue
on GitHub that uses a tag corresponding to the script any error was detected with.

Example Usage:

python post_github_issues.py -o sibis-platform -r ncanda-issues \
                             -t "NCANDA: Laptop Data Import Stage 2 (update_visit_date)" \
                             -b /tmp/test.txt -v
"""
__author__ = 'Nolan Nichols <https://orcid.org/0000-0003-1099-3328>'

import os
import sys
import json
import hashlib
import ConfigParser

import github
from github.GithubException import UnknownObjectException


def create_connection(cfg, verbose=None):
    """
    Get a connection to github api

    :param cfg: path to configuration file
    :return: github.MainClass.Github
    """
    if verbose:
        print "Parsing config: {0}".format(cfg)
    # Get the redcap mysql configuration
    config = ConfigParser.RawConfigParser()
    config_path = os.path.expanduser(cfg)
    config.read(config_path)

    user = config.get('github', 'user')
    passwd = config.get('github', 'password')

    g = github.Github(user, passwd)
    if verbose:
        print "Connected to GitHub..."
    return g


def get_label(repo, title, verbose=None):
    """
    Get a label object to tag the issue

    :param repo: github.Repository
    :param title: str
    :return: github.Label
    """
    if verbose:
        print "Checking for label..."
    label = None
    label_text = None
    try:
        label_start = 1 + title.index('(')
        label_end = title.index(')')
        label_text = title[label_start:label_end]
    except ValueError, e:
        print "Warning: This tile has no embeded label. {0}".format(e)
    if label_text:
        try:
            label = [repo.get_label(label_text)]
            if verbose:
                print "Found label: {0}".format(label)
        except UnknownObjectException, e:
            print "Error: The label '{0}' does not exist on Github. {1}".format(label_text, e)
    return label


def is_open_issue(repo, subject, verbose=None):
    """
    Verify if issue already exists, if the issue is closed, reopen it.
    :param repo: github.Repository
    :param subject: str
    :return: bool
    """
    if verbose:
        print "Checking for open issue: {0}".format(subject)
    for issue in repo.get_issues(state='all'):
        if issue.title == subject and issue.state == 'open':
            if verbose:
                print "Open issue already exists... See: {0}".format(issue.url)
            return True
        if issue.title == subject and issue.state == 'closed':
            if verbose:
                print "Closed issue already exists, reopening... See: {0}".format(issue.url)
            issue.edit(state='open')
            return True
    if verbose:
        print "Issue does not already exist... Creating.".format(subject)
    return False


def generate_body(issue):
    """
    Generate Markdown for body of issue.

    :param issue:
    :return: str
    """
    markdown = "### {}\n".format(issue.pop('title'))
    for k, v in issue.iteritems():
        markdown += "- {}: {}\n".format(k, v)
    return markdown


def create_issues(repo, title, body, verbose=None):
    """
    Create a GitHub issue for the provided repository with a label

    :param repo: github.Repository
    :param title: str
    :param body: str
    :return: None
    """
    label = get_label(repo, title)
    if not label:
        raise NotImplementedError("A label embedded in parentheses is currently required. "
                                  "For example 'Title of Error (title_tag).' You provided:"
                                  "{0}".format(title))
    # get stdout written to file
    with open(body) as fi:
        issues = fi.readlines()
        fi.close()
    # Handle empty body
    if not issues:
        raise RuntimeWarning("The body text is empty and no issue will be created for "
                             "file: {}.".format(body))
    # Handle multiline error messages.
    if 'Traceback' in ''.join(issues):
        if verbose:
            print "Issue is a Traceback..."
        string = "".join(issues)
        sha = hashlib.sha1(string).hexdigest()[0:6]
        error = dict(experiment_site_id = "Traceback:{}".format(sha)
                    error = "Traceback"
                    message = string)
    for issue in issues:
        # Check for new format
        try:
            issue_dict = json.loads(issue)
            issue_dict.update({'title': title})
            error_msg = issue_dict.get('error')
            experiment_site_id = issue_dict.get('experiment_site_id')
            subject = "{}, {}".format(experiment_site_id, error_msg)
            body = generate_body(issue_dict)
        except:
            if verbose:
                print("Falling back to old issue formatting.")
            # Old error handling approach.
            # Create a unique id.
            sha1 = hashlib.sha1(issue).hexdigest()[0:6]
            subject_base = title[0:title.index(' (')]
            subject = subject_base + ": {0}".format(sha1)
            body = issue
        if is_open_issue(repo, subject, verbose=verbose):
            pass
        else:
            github_issue = repo.create_issue(subject, body=body, labels=label)
            if verbose:
                print "Created issue... See: {0}".format(github_issue.url)
    return None


def main(args=None):
    if args.verbose:
        print "Initializing..."
    g = create_connection(args.config, verbose=args.verbose)
    organization = g.get_organization(args.org)
    repo = organization.get_repo(args.repo)
    create_issues(repo, args.title, args.body, verbose=args.verbose)
    if args.verbose:
        print "Finished!"

if __name__ == "__main__":
    import argparse

    formatter = argparse.RawDescriptionHelpFormatter
    default = 'default: %(default)s'
    parser = argparse.ArgumentParser(prog="post_github_issues.py",
                                     description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument("-c", "--config", dest="config",
                        default=os.path.expanduser('~/.server_config/github.cfg'),
                        help="GitHub authentication info.".format(default))
    parser.add_argument("-o", "--org", dest="org", required=True,
                        help="GitHub organization.")
    parser.add_argument("-r", "--repo", dest="repo", required=True,
                        help="GitHub repo.")
    parser.add_argument("-t", "--title", dest="title", required=True,
                        help="GitHub issue title with label in parentheses.")
    parser.add_argument("-b", "--body", dest="body", required=True,
                        help="GitHub issue body.")
    parser.add_argument("-v", "--verbose", dest="verbose", action='store_true',
                        help="Turn on verbose.")
    argv = parser.parse_args()
    sys.exit(main(args=argv))
