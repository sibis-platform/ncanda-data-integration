import batch_script_utils as utils
import commands
import regex as re


class Issue(object):
    """
    A class used to represent an issue.

    ...

    Attributes
    ----------
    verbose : bool
        Whether to print when commenting on and closing issue.
    issue : PyGithub issue
        Issue to create wrapper for.
    number : int
        The number of the issue on GitHub.
    body : dict
        The body of the issue, rehydrated into a dict.
    commands : list
        List of commands which caused the issue.
    resolved : bool
        Whether the issue has been resolved.

    Methods
    -------
    comment()
    Comments on the issue.
    close()
    Closes the issue.
    update()
    Updates the issue with the results of the commands, and updates the resolved status.
    get_commands()
    Returns the list of commands.
    test_commands()
    Tests each of the commands.
    stringify()
    Returns a formatted string.

    """

    def __init__(self, verbose, issue):
        self.verbose = verbose

        self.issue = issue
        self.number = issue.number
        self.body = {}
        bulletpoints = self.issue.body.split("\n-")[1:]
        for bulletpoint in bulletpoints:
            key, value = bulletpoint.split(":", 1)
            key = key.strip()
            value = value.strip()
            self.body[key] = value

        self.commands = []
        self.resolved = False

    def comment(self, comment):
        if self.verbose:
            print(f"Commenting on #{self.number}")
        self.issue.create_comment(comment)

    def close(self):
        if self.verbose:
            print(f"Closing #{self.number}")
        self.issue.edit(state="closed")

    def update(self):
        self.resolved = True
        comment = ""
        for command in self.commands:
            self.resolved = self.resolved and command.ran_successfully()
            comment = comment + "\n" + command.stringify()

        self.comment(comment)
        if self.resolved:
            self.close()

    def get_commands(self):
        return self.commands

    def test_commands(self):
        for command in self.commands:
            command.run()

    def stringify(self):
        return f"#{self.issue.number}\n" + "\n".join(
            [command.stringify_command() for command in self.commands]
        )


class RedcapUpdateSummaryScoresIssue(Issue):
    """
    Subclass of Issue used for redcap-update-summary-scores issues.

    """

    def __init__(self, verbose, issue, metadata):
        Issue.__init__(self, verbose, issue)

        if "requestError" not in self.body or "experiment_site_id" not in self.body:
            raise ValueError(
                f"#{self.number}\nrequestError or experiment_site_id not in body"
            )

        study_ids = utils.extract_unique_study_ids(self.body["requestError"])
        first_field = self.body["requestError"].split('","')[1]
        field_row = metadata[metadata["field_name"] == first_field]
        self.form = field_row["form_name"].item()
        experiment_site_id_regex = (
            f"({utils.STUDY_ID_REGEX}_{utils.EVENT_REGEX}_)?(.*)-"
        )
        experiment_site_id_matches = re.match(
            experiment_site_id_regex, self.body["experiment_site_id"]
        )
        if not experiment_site_id_matches:
            raise ValueError(f"#{self.number}\nNo matches in experiment_site_id")
        instrument = experiment_site_id_matches[-1]

        for study_id in study_ids:
            command = commands.RedcapUpdateSummaryScoresCommand(
                self.verbose, study_id, instrument
            )
            self.commands.append(command)

        if self.verbose:
            print(self.stringify())


class UpdateVisitDataIssue(Issue):
    """
    Subclass of Issue used for update_visit_data issues.

    """

    def __init__(self, verbose, issue, metadata):
        Issue.__init__(self, verbose, issue)

        if "requestError" in self.body:
            study_ids = utils.extract_unique_study_ids(self.body["requestError"])
            first_field = self.body["requestError"].split('","')[1]
            field_row = metadata[metadata["field_name"] == first_field]
            self.form = field_row["form_name"].item()
            for study_id in study_ids:
                command = commands.UpdateVisitDataCommand(
                    self.verbose, study_id, self.form
                )
                self.commands.append(command)
        elif "form_name" in self.body:
            form = self.body["form_name"]
            study_ids = utils.extract_unique_study_ids(self.body["experiment_site_id"])
            if not study_ids:
                raise ValueError(f"#{self.number}\nNo study id in experiment_site_id")
            study_id = study_ids[0]
            command = commands.UpdateVisitDataCommand(self.verbose, study_id, form)
            self.commands.append(command)
        else:
            raise ValueError(f"#{self.number}\nrequestError and form_name not in body")

        if self.verbose:
            print(self.stringify())


class UpdateSummaryFormsIssue(Issue):
    """
    Subclass of Issue used for update_summary_forms issues.

    """

    def __init__(self, verbose, issue, metadata):
        Issue.__init__(self, verbose, issue)

        if "requestError" in self.body:
            study_ids = utils.extract_unique_study_ids(self.body["requestError"])
            first_field = self.body["requestError"].split('","')[1]
            field_row = metadata[metadata["field_name"] == first_field]
            self.form = field_row["form_name"].item()
            for study_id in study_ids:
                command = commands.UpdateSummaryFormsCommand(self.verbose, study_id)
                self.commands.append(command)
        elif "records_this_visit" in self.body:
            study_id = utils.extract_unique_study_ids(self.body["records_this_visit"])[
                0
            ]
            command = commands.UpdateSummaryFormsCommand(self.verbose, study_id)
            self.commands.append(command)
        else:
            raise ValueError(
                f"#{self.number}\nrequestError and records_this_visit not in body"
            )

        if self.verbose:
            print(self.stringify())


class ImportMRSessionsIssue(Issue):
    """
    Subclass of Issue used for import_mr_sessions issues.

    """

    def __init__(self, verbose, issue, metadata):
        Issue.__init__(self, verbose, issue)

        if "requestError" in self.body:
            study_ids = utils.extract_unique_study_ids(self.body["requestError"])
            first_field = self.body["requestError"].split('","')[1]
            field_row = metadata[metadata["field_name"] == first_field]
            self.form = field_row["form_name"].item()
            for study_id in study_ids:
                command = commands.ImportMRSessionsCommand(self.verbose, study_id)
                self.commands.append(command)
        elif "experiment_site_id" in self.body:
            study_ids = utils.extract_unique_study_ids(self.body["experiment_site_id"])
            if not study_ids:
                raise ValueError(f"#{self.number}\nNo study id in experiment_site_id")
            study_id = study_ids[0]
            command = commands.ImportMRSessionsCommand(self.verbose, study_id)
            self.commands.append(command)
        else:
            raise ValueError(f"#{self.number}\nrequestError not in body")

        if self.verbose:
            print(self.stringify())
