import batch_script_utils as utils

class Command(object):

    def __init__(self, issue_body, verbose):
        self.success = False
        self.error = {'stdout': "",
                      'stderr': "",
        }
        self.verbose = verbose
        
    def test(self):
        if self.verbose:
            print(self.stringify)
        completed_process = run(command, capture_output=True)
        if self.verbose:
            print(self)

    def stringify_commmand(self):
        return " ".join(self.command)

    def stringify_result(self):
        

class Issue(object):
      
    def __init__(self, issue, batch_script_filename):
        self.issue = issue
        rehydrate_issue_body(issue.body)
        self.commands = []

    def rehydrate_issue_body(body: str) -> dict:
        bulletpoints = body.split("\n-")[1:]
        for bulletpoint in bulletpoints:
            key, value = bulletpoint.split(":", 1)
            key = key.strip()
            value = value.strip()
            self.key = value

    def comment(self, comment):
        self.issue.create_comment(comment)

    def close(self):
        self.issue.edit(state="closed")

    def comment_and_close():
        close_comment = "Error no longer produced, closing."
        self.comment(close_comment)
        self.close()
        
    def get_commands(self):
        return self.commands

    def stringify(self):
        return f"#{self.issue.number}" + "\n" + "\n".join([command.stringify() for command in self.commands])


        
