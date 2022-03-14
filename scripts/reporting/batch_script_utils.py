from subprocess import run
import re
import issues


def extract_unique_study_ids(text: str) -> list:
    study_id_regex = "[A-EX]-\d{5}-[FMTX]-\d"
    study_ids = sorted(list(set(re.findall(study_id_regex, text))))
    return study_ids


def prompt_y_n(prompt: str) -> bool:
    while True:
        confirm = input(prompt + " (y/n)\n")
        if confirm in ["n", "y"]:
            return confirm == "y"
        print("Invalid input")


def run_command(command: list, verbose: bool):
    if verbose:
        print(" ".join(command))
    completed_process = run(command, capture_output=True)
    if verbose:
        print(f"stdout:\n{completed_process.stdout}")
        print(f"\nstderr:\n{completed_process.stderr}")
    return completed_process


def get_open_issues(slog):
    ncanda_operations = slog.log.postGithubRepo
    issues = ncanda_operations.get_issues(state="open")
    return issues
def scrape_matching_issues(slog, title_string, target_label, scrape_tuple_from_issue):
    issues = get_open_issues(slog)
    scraped_tuples = []
    for issue in issues:
        if title_string in issue.title:
            for label in issue.get_labels():
                if target_label == label.name:
                    issue_body = rehydrate_issue_body(issue.body)
                    scraped_tuple = scrape_tuple_from_issue_body(issue_body)
                    scraped_tuples.append(scraped_tuple)
                    break
    return scraped_tuples

def get_base_command(label):
    if label == "import_mr_sessions":
        return [
            "/sibis-software/ncanda-data-integration/scripts/redcap/import_mr_sessions",
            "-f",
            "--pipeline-root-dir",
            "/fs/ncanda-share/cases",
            "--run-pipeline-script",
            "/fs/ncanda-share/scripts/bin/ncanda_all_pipelines",
            "--study-id",
        ]
    elif label == "check_new_sessions":
        return [
            "/sibis-software/ncanda-data-integration/scripts/xnat/check_new_sessions",
            "-f",
            "-e",
        ]
    elif label == "update_visit_data":
        return [
            "/sibis-software/ncanda-data-integration/scripts/import/laptops/update_visit_data",
            "-a",
            "--study-id",
        ]
    elif label == "check_phantom_scans":
        return [
            "/sibis-software/ncanda-data-integration/scripts/xnat/check_phantom_scans",
            "-a",
            "-e",
        ]


def get_id_type(label: str):
    id_type = None
    if label in ["import_mr_sessions", "update_visit_data"]:
        id_type = "subject_id"
    elif label in ["check_new_sessions"]:
        id_type = "eid"
    elif label in ["check_phantom_scans"]:
        id_type = "experiment_id"
    assert id_type is not None
    return id_type


def get_id(id_type: str, issue_dict: dict):
    scraped_id = None
    if id_type == "subject_id":
        if "experiment_site_id" in issue_dict:
            scraped_id = issue_dict["experiment_site_id"][:11]
    elif id_type == "eid":
        if "eid" in issue_dict:
            scraped_id = issue_dict["eid"]
    elif id_type == "experiment_id":
        if "experiment_id" in issue_dict:
            scraped_id = issue_dict["experiment_id"]
    return scraped_id

def update_issues(scraped_issues, verbose: bool):
    """Loops through the list of issues, tests them, and updates them on GitHub."""
    closed_issues = []
    commented_issues = []

    for scraped_issue in scraped_issues:
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
    assert issue_class != None
    return issue_class
