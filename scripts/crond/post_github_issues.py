#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##
"""
Post GitHub Issues
------------------

Take the stdout and stderr passed to the catch_output_email and create an issue
on GitHub that uses a tag corresponding to the script any error was detected
with.

Example Usage:

python post_github_issues.py -o sibis-platform -r ncanda-issues \
                             -t "NCANDA: Laptop Data (update_visit_date)" \
                             -b /tmp/test.txt -v
"""
import os
import re
import sys
import json
import hashlib
import ConfigParser

import github
from github.GithubException import UnknownObjectException, GithubException

import sibis

def create_connection(cfg, verbose=None):
    """Get a connection to github api.

    Args:
        cfg (str): Path to configuration file.
        verbose (bool): True turns on verbose.

    Returns:
        object: A github.MainClass.Github.
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


def get_label(repo, raw_title, verbose=None):
    """Get a label object to tag the issue.

    Args:
        repo (object): A github.Repository object.
        title (str): Title of posting.
        verbose (bool): True turns on verbose.

    Returns:
        object: A github.Label.

    """
    if verbose:
        print "Checking for label..."
    label = None
    try:
        label = [repo.get_label(raw_title)]
        if verbose:
            print "Found label: {0}".format(label)
    except UnknownObjectException as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        error = 'Not found label in github for string ', raw_title
        sibis.logging('{0} post_github_issues at line {1}'.format(hashlib.sha1(error).hexdigest()[0:6], exc_tb.tb_lineno),
                        error,
                        function='get_label()',
                        exception=str(e))
    return label


def is_open_issue(repo, subject, verbose=None):
    """Verify if issue already exists, if the issue is closed, reopen it.

    Args:
        repo (object): a github.Repository.
        subject (str): Subject line.
        verbose (bool): True turns on verbose.

    Returns:
        bool: True if issue is already open.
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
                print "Closed issue already exists, reopening... " \
                      "See: {0}".format(issue.url)
            try:
                issue.edit(state='open')
            except GithubException as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                error = 'Failed editing Issue state from closed to open after comparing issue.title and subject'
                sibis.logging('{0} post_github_issues at line {1}'.format(hashlib.sha1(str(e)).hexdigest()[0:6], exc_tb.tb_lineno),
                              error,
                              issue_title=issue.title,
                              subject=subject,
                              exception=str(e))
                return False
            return True
    if verbose:
        print "Issue does not already exist... Creating.".format(subject)
    return False


def generate_body(issue):
    """Generate Markdown for body of issue.

    Args:
        issue (dict): Keys for title and others.

    Returns:
        str: Markdown text.
    """
    markdown = "### {}\n".format(issue.pop('title'))
    for k, v in issue.iteritems():
        markdown += "- {}: {}\n".format(k, v)
    return markdown


def create_issues(repo, title, body, verbose=None):
    """Create a GitHub issue for the provided repository with a label

    Args:
        repo: github.Repository
        title (str): Contains label on github in parentheses.
        body (str):
        verbose (bool): True turns on verbose

    Returns:
        None
    """
    #Look for first match of string between parentheses in title.
    re_title = re.match('[^\(]*\(([^\)]+)\).*', title)
    if re_title:
        raw_title = re_title.group(1)
        label = get_label(repo, raw_title)
    else:
        error = 'Not able to create label from title, probably miss parentheses'
        sibis.logging('{} post_github_issues'.format((hashlib.sha1(error).hexdigest()[0:6])),
                      error,
                      repo=repo,
                      title=title,
                      function='create_issues')
        raise NotImplementedError(error.format(title))
    # get stdout written to file
    with open(body) as fi:
        issues = fi.readlines()
        fi.close()
    # Handle empty body
    if not issues:
        raise RuntimeWarning("The body text is empty and no issue will be "
                             "created for file: {}.".format(body))
    # Handle multiline error messages.
    if 'Traceback' in ''.join(issues):
        if verbose:
            print "Issue is a Traceback..."
        string = "".join(issues)
        sha = hashlib.sha1(string).hexdigest()[0:6]
        error = 'Unhandled Error in code. More information in the Traceback'
        sibis.logging('Traceback: {} post_github_issues'.format(sha),
                      error,
                      issue_stack=string)
    for issue in issues:
        # Check for new format
        try:
            issue_dict = json.loads(issue)
            #Get only the first 256 characters for Guthub validation
            issue_dict.update({'title': title[:255]})
            error_msg = issue_dict.get('error')
            experiment_site_id = issue_dict.get('experiment_site_id')
            subject = "{}, {}".format(experiment_site_id, error_msg)[:255]
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
    default_cfg = '~/.server_config/github.cfg'
    parser.add_argument("-c", "--config", dest="config",
                        default=os.path.expanduser(default_cfg),
                        help="GitHub authentication info.".format(default))
    parser.add_argument("-o", "--org", dest="org", required=True,
                        help="GitHub organization.")
    parser.add_argument("-r", "--repo", dest="repo", required=True,
                        help="GitHub repo.")
    parser.add_argument("-t", "--title", dest="title", required=True,
                        help="GitHub issue title with label in parentheses.")
    parser.add_argument("-b", "--body", dest="body", required=True,
                        help="GitHub issue body. It needs to be a text file")
    parser.add_argument("-v", "--verbose", dest="verbose", action='store_true',
                        help="Turn on verbose.")
    argv = parser.parse_args()
    sys.exit(main(args=argv))
