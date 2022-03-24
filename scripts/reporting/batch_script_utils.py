from subprocess import run
import re
import issues

STUDY_ID_REGEX = "[A-EX]-\d{5}-[FMTX]-\d"
YEAR_EVENT_REGEX = "(baseline|[0-9]{1,2}y)_visit"
MIDYEAR_EVENT_REGEX = "[0-9]{1,3}month_followup"
EVENT_REGEX = f"({year_event_regex}|{midyear_event_regex})_arm_[123]"


def extract_unique_study_ids(text: str) -> list:
    study_ids = sorted(list(set(re.findall(STUDY_ID_REGEX, text))))
    return study_ids


def prompt_y_n(prompt: str) -> bool:
    while True:
        confirm = input(prompt + " (y/n)\n")
        if confirm in ["n", "y"]:
            return confirm == "y"
        print("Invalid input")

def get_open_issues(slog):
    ncanda_operations = slog.log.postGithubRepo
    issues = ncanda_operations.get_issues(state="open")
    return issues


def scrape_matching_issues(
    slog, metadata, verbose, title_string, target_label, issue_numbers, issue_class
):
    """Returns a list of issues which match the passed title, label, and issue_numbers. Issues
    are instances of the passed issue class."""
    open_issues = get_open_issues(slog)
    scraped_issues = []
    for open_issue in open_issues:
        if len(issue_numbers) == 0 or open_issue.number in issue_numbers:
            if title_string in open_issue.title:
                for label in open_issue.get_labels():
                    if target_label == label.name:
                        try:
                            scraped_issue = issue_class(verbose, open_issue, metadata)
                        except ValueError as e:
                            if verbose:
                                print(e)
                        else:
                            scraped_issues.append(scraped_issue)
                        break
    return scraped_issues


def verify_scraped_issues(scraped_issues: list):
    print("\nFound the following issues:")
    for scraped_issue in scraped_issues:
        print(scraped_issue.stringify())
    return prompt_y_n("Are all issues valid?")


def update_issues(scraped_issues, verbose: bool):
    """Loops through the list of issues, tests them, and updates them on GitHub."""
    closed_issues = []
    commented_issues = []

    for scraped_issue in scraped_issues:
        if verbose:
            print("\n" * 20)
            print(f"#{scraped_issue.number}")

        scraped_issue.test_commands()
        scraped_issue.update()
        if scraped_issue.resolved:
            closed_issues.append(f"#{scraped_issue.number}")
        else:
            commented_issues.append(f"#{scraped_issue.number}")

    if verbose:
        print(f"\n\nClosed:\n{', '.join(closed_issues)}")
        print(f"Commented:\n{', '.join(commented_issues)}")


def get_class_for_label(label: str):
    """Returns the issue class for the passed label."""
    issue_class = None
    if label == "redcap_update_summary_scores":
        issue_class = issues.RedcapUpdateSummaryScoresIssue
    elif label == "update_visit_data":
        issue_class = issues.UpdateVisitDataIssue
    elif label == "update_summary_forms":
        issue_class = issues.UpdateSummaryFormsIssue
    elif label == "import_mr_sessions":
        issue_class = issues.ImportMRSessionsIssue
    elif label == "check_new_sessions":
        issue_class = issues.CheckNewSessionsIssue
    elif label == "check_phantom_scans":
        issue_class = issues.CheckPhantomScansIssue
    assert issue_class != None
    return issue_class
