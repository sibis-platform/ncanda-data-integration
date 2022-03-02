from subprocess import run
import re

def extract_unique_subject_ids(text: str) -> list:
    subject_id_regex = "[A-EX]-\d{5}-[FMTX]-\d"
    subject_ids = sorted(list(set(re.findall(subject_id_regex, text))))
    return subject_ids


def prompt_y_n(prompt: str) -> bool:
    while True:
        confirm = input(prompt + " (y/n)\n")
        if confirm in ["n", "y"]:
            return confirm == "y"
        print("Invalid input")


def run_command(command: list):
    completed_process = run(command, capture_output=True)
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
                    scraped_tuple = scrape_tuple_from_issue(issue)
                    if scraped_tuple:
                        scraped_tuples.append(scraped_tuple)
                    break
    return scraped_tuples

def get_base_command(label: str):
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
    if label in ["import_mr_sessions"]:
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

def verify_scraped_tuples(scraped_tuples: list, display_scraped_tuple):
    print("\nFound the following tuples:")
    for scraped_tuple in scraped_tuples:
        display_scraped_tuple(scraped_tuple)
    return prompt_y_n("Are all tuples valid?")


def update_issues(scraped_tuples, display_scraped_tuple, process_scraped_tuple, close_comment, error_comment, verbose):
    closed_issues = []
    commented_issues = []

    for scraped_tuple in scraped_tuples:
        issue = scraped_tuple[0]
        errors = process_scraped_tuple(scraped_tuple)
        if errors:
            if verbose:
                print("\n\nErrors:\n")
                for error in errors:
                    print(f"stdout:{error[0]}\nstderr:\n{error[1]}")

            scraped_tuple.comment()
            commented_issues.append(f"#{issue.number}")
        else:
            if verbose:
                print(f"Closing #{issue.number}")

            scraped_tuple.close()
            closed_issues.append(f"#{issue.number}")

    if verbose:
        print(f"\n\nClosed:\n{', '.join(closed_issues)}")
        print(f"Commented:\n{', '.join(commented_issues)}")

def get_scraper_for_label(label: str):
    scraper = None
    if label in ["redcap_update_summary_scores"]:
    def scrape_tuple_from_issue(issue):
        issue_dict = utils.rehydrate_issue_body(issue.body)
        request_error = issue_dict['requestError']
        subject_ids = utils.extract_unique_subject_ids(request_error)
        first_field = request_error.split('","')[1]
        field_row = metadata[metadata["field_name"] == first_field]
        form = field_row["form_name"].item()
        instrument = issue_dict['experiment_site_id'].split("-")[0]

        scraped_tuple = (issue, subject_ids, form, instrument)
        if verbose:
            print(
                f"\nFound the following subject id's in #{issue.number}:\n{subject_ids}"
            )
        return scraped_tuple

