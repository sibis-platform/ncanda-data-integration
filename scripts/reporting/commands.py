from subprocess import run


class Command(object):
    """
    A class used to represent a command.

    ...

    Attributes
    ----------
    verbose : bool
        Whether to print command and result when testing.
    been_run : bool
        Whether the command has been run yet.
    result : dict
        Stores stdout and stderr when command run.

    Methods
    -------
    run()
        Runs the command and stores the result.
    ran_successfully()
        Returns true if the command ran without printing to stderr or stdout.
    stringify_command()
        Returns the command as a string.
    stringify_result()
        Returns the result of runninng the command as a string.
    stringify()
        Returns the command and the result as a string.

    """

    def __init__(self, verbose):
        self.verbose = verbose
        self.been_run = False
        self.success = False
        self.result = {}

    def run(self):
        if self.verbose:
            print(self.stringify_command())
        completed_process = run(self.command, capture_output=True)
        self.result["stdout"] = completed_process.stdout
        self.result["stderr"] = completed_process.stderr
        self.been_run = True
        if self.verbose:
            print(self.stringify_result())

    def ran_successfully(self):
        if self.been_run and not self.result["stdout"] and not self.result["stderr"]:
            return True
        return False

    def stringify_command(self):
        return " ".join(self.command)

    def stringify_result(self):
        if not self.been_run:
            return "Command not run"
        if self.ran_successfully():
            return "Success! No errors printed to console."
        return f"stdout:\n{self.result['stdout']}\nstderr:\n{self.result['stderr']}"

    def stringify(self):
        return self.stringify_command() + "\n" + self.stringify_result()


class ExecRedcapLockingDataCommand(Command):
    """
    A subclass of Command. Represents exec_redcap_locking_data.py commands.

    ...

    Attributes
    ----------
    study_id : str
        id of subject to run command on, e.g. A-00002-F-2
    form : str
        Form to run command on, e.g. clinical
    lock : bool
        If true, locks the form. If false, unlocks the form.
    """

    def __init__(self, verbose, study_id, form, lock):
        Command.__init__(self, verbose)
        self.study_id = study_id
        self.form = form
        self.lock = lock

        events = ["Baseline", "1y", "2y", "3y", "4y", "5y", "6y", "7y"]
        script_path = (
            "/sibis-software/python-packages/sibispy/cmds/exec_redcap_locking_data.py"
        )
        self.command = (
            ["python", script_path, "-e"]
            + events
            + ["--forms", self.form, "--study-id", self.study_id]
        )
        if self.lock:
            self.command.append("--lock")
        else:
            self.command.append("--unlock")


class RedcapUpdateSummaryScoresCommand(Command):
    """
    A subclass of Command. Represents redcap_update_summary_scores.py commands.

    ...

    Attributes
    ----------
    study_id : str
        id of subject to run command on, e.g. A-00002-F-2
    instrument : str
        Instrument to run command on, e.g. ses
    """

    def __init__(self, verbose, study_id, instrument):
        Command.__init__(self, verbose)
        self.study_id = study_id
        self.instrument = instrument
        script_path = "/sibis-software/python-packages/sibispy/cmds/redcap_update_summary_scores.py"
        self.command = ["python", script_path, "-a", "-s", study_id, "-i", instrument]


class UpdateVisitDataCommand(Command):
    """
    A subclass of Command. Represents update_visit_data.py commands.

    ...

    Attributes
    ----------
    study_id : str
        id of subject to run command on, e.g. A-00002-F-2
    form : str
        Form to run command on, e.g. clinical
    """

    def __init__(self, verbose, study_id, form):
        Command.__init__(self, verbose)
        self.study_id = study_id
        self.form = form
        script_path = "/sibis-software/ncanda-data-integration/scripts/import/laptops/update_visit_data"
        self.command = (
            script_path,
            "-a",
            "--study-id",
            study_id,
            "--forms",
            form,
        )


class UpdateSummaryFormsCommand(Command):
    """
    A subclass of Command. Represents update_summary_forms.py commands.

    ...

    Attributes
    ----------
    study_id : str
        id of subject to run command on, e.g. A-00002-F-2
    """

    def __init__(self, verbose, study_id):
        Command.__init__(self, verbose)
        self.study_id = study_id
        script_path = "/sibis-software/ncanda-data-integration/scripts/import/webcnp/update_summary_forms"
        self.command = [script_path, "-a", "--study-id", study_id]


class ImportMRSessionsCommand(Command):
    """
    A subclass of Command. Represents import_mr_sessions.py commands.

    ...

    Attributes
    ----------
    study_id : str
        id of subject to run command on, e.g. A-00002-F-2
    """

    def __init__(self, verbose, study_id):
        Command.__init__(self, verbose)
        self.study_id = study_id
        script_path = (
            "/sibis-software/ncanda-data-integration/scripts/redcap/import_mr_sessions"
        )
        self.command = [
            script_path,
            "--pipeline-root-dir",
            "/fs/ncanda-share/cases",
            "--run-pipeline-script",
            "/fs/ncanda-share/scripts/bin/ncanda_all_pipelines",
            "-f",
            "--study-id",
            study_id,
        ]


class CheckNewSessionsCommand(Command):
    """
    A subclass of Command. Represents check_new_sessions.py commands.

    ...

    Attributes
    ----------
    experiment_id : str
        experiment_id of subject to run command on, e.g. NCANDA_E11304
    """

    def __init__(self, verbose, experiment_id):
        Command.__init__(self, verbose)
        self.experiment_id = experiment_id
        script_path = (
            "/sibis-software/ncanda-data-integration/scripts/xnat/check_new_sessions"
        )
        self.command = [
            script_path,
            "-f",
            "-e",
            experiment_id,
        ]


class CheckPhantomScansCommand(Command):
    """
    A subclass of Command. Represents check_phantom_scans.py commands.

    ...

    Attributes
    ----------
    experiment_id : str
        experiment_id of subject to run command on, e.g. NCANDA_E11304
    """

    def __init__(self, verbose, experiment_id):
        Command.__init__(self, verbose)
        self.experiment_id = experiment_id
        script_path = (
            "/sibis-software/ncanda-data-integration/scripts/xnat/check_phantom_scans.py"
        )
        self.command = [
            'python',
            script_path,
            "-a",
            "-e",
            experiment_id,
        ]


class UpdateBulkFormsCommand(Command):
    """
    A subclass of Command. Represents update_bulk_forms commands.

    ...

    Attributes
    ----------
    study_id : str
        id of subject to run command on, e.g. A-00002-F-2
    """

    def __init__(self, verbose, study_id):
        Command.__init__(self, verbose)
        self.study_id = study_id
        script_path = (
            "/sibis-software/ncanda-data-integration/scripts/redcap/update_bulk_forms"
        )
        self.command = [
            script_path,
            "-a",
            "--study-id",
            study_id,
        ]
