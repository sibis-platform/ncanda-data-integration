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


def extract_unique_subject_ids(text: str) -> list:
    subject_id_regex = "[A-EX]-\d{5}-[FMTX]-\d"
    subject_ids = sorted(list(set(re.findall(subject_id_regex, text))))
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
