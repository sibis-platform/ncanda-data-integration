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


class RedcapUpdateSummaryScoresCommand(Command):
    """
    A subclass of Command. Represents redcap_update_summary_scores.py commands.

    ...

    Attributes
    ----------
    study_id : str
        id of subject to run command on, e.g. A-00002-F-2
    form : str
        Form to run command on, e.g. clinical
    instrument : str
        Instrument to run command on, e.g. ses
    """

    def __init__(self, verbose, study_id, form, instrument):
        Command.__init__(self, verbose)
        self.study_id = study_id
        self.form = form
        self.instrument = instrument
        script_path = "/sibis-software/python-packages/sibispy/cmds/redcap_update_summary_scores.py"
        self.command = (
            ["python"]
            + [script_path]
            + ["-a"]
            + ["-s"]
            + [study_id]
            + ["-i"]
            + [instrument]
        )


class ExecRedcapLockingData(Command):
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
            ["python"]
            + [script_path]
            + ["-f"]
            + [self.form]
            + ["-s"]
            + [self.study_id]
            + ["-e"]
            + events
        )
        if self.lock:
            self.command.append("--lock")
        else:
            self.command.append("--unlock")
