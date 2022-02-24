from subprocess import run
import re


def rehydrate_issue_body(body: str) -> dict:
    rehydrated_body = {}
    bulletpoints = body.split("\n-")[1:]
    for bulletpoint in bulletpoints:
        key, value = bulletpoint.split(":", 1)
        key = key.strip()
        value = value.strip()
        rehydrated_body[key] = value
    return rehydrated_body


def extract_unique_study_ids(text: str) -> list:
    study_id_regex = "[A-EX]-\d{5}-[FMTX]-\d"
    study_ids = sorted(list(set(re.findall(study_id_regex, text))))
    return study_ids


def prompt_y_n(prompt: str) -> bool:
    while True:
        confirm = input(prompt + "\n")
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

def comment_and_close(issue, close_comment: str):
    issue.create_comment(close_comment)
    issue.edit(state="closed")
    
def prompt_close_or_comment(issue, close_comment: str):
    if prompt_y_n("Close issue? (y/n)"):
        comment_and_close(issue, close_comment)
    elif prompt_y_n("Comment on issue? (y/n)"):
        comment = input("Enter comment:\n")
        issue.create_comment(comment)

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
                    scraped_tuple = scrape_tuple_from_issue(issue)
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


def get_id_type(label):
    id_type = None
    if label in ["import_mr_sessions"]:
        id_type = "study_id"
    elif label in ["check_new_sessions", "check_phantom_scans"]:
        id_type = "xnat_experiment_id"
    assert id_type is not None
    return id_type


def get_id(id_type, issue_dict):
    scraped_id = None
    if id_type == "study_id":
        if "study_id" in issue_dict:
            scraped_id = issue_dict["study_id"]
    elif id_type == "xnat_experiment_id":
        if "xnat_experiment_id" in issue_dict:
            scraped_id = issue_dict["xnat_experiment_id"]
    return scraped_id
