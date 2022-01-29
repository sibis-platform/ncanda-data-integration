from subprocess import run


def rehydrate_issue_body(body: str) -> dict:
    return {
        x.split(":", 1)[0].strip(): x.split(":", 1)[1].strip()
        for x in body.split("\n-")[1:]
    }


def extract_unique_subject_ids(text: str) -> list:
    subject_id_regex = "\w-\d{5}-\w-\d"
    subject_ids = list(set(re.findall(subject_id_regex, text)))
    return subject_ids


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


def prompt_close_or_comment(issue, close_comment: str):
    if prompt_y_n("Close issue? (y/n)"):
        issue.create_comment(close_comment)
        issue.edit(state="closed")
    elif prompt_y_n("Comment on issue? (y/n)"):
        comment = input("Enter comment:\n")
        issue.create_comment(comment)


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
            "-a",
            "-e",
        ]
    elif label == "update_visit_data":
        return [
            "/sibis-software/ncanda-data-integration/scripts/import/laptops/update_visit_data",
            "-a",
            "--study-id",
        ]


def get_id_type(label):
    if label in ["import_mr_sessions"]:
        return "subject_id"
    elif label in ["check_new_sessions"]:
        return "eid"


def get_id(id_type, issue_dict):
    if id_type == "subject_id":
        scraped_id = issue_dict["experiment_site_id"][:11]
    elif id_type == "eid":
        scraped_id = issue_dict["eid"]
    return scraped_id
