import sys
import hashlib
from sibispy import sibislogger as slog

# have to post issues that way so that github is not overwhelmed with calls 
def post_issue_and_exit(script, infile, verbose, post_to_github, issue_label, issue_title, **kwargs) : 
    slog.init_log(verbose, post_to_github,'NCANDA Import-Laptop: ' + script + ' Message', script)

    if 'post_resolution_instructions' not in kwargs:
        infoTxt="After this issue is resolved please run 'harvester --file-to-upload " + infile + " --overwrite' to insure that data is upload to redcap" 
    else:
        infoTxt = kwargs['post_resolution_instructions']
        del kwargs['post_resolution_instructions']
    
    slog.info(issue_label + "-" + hashlib.sha1(infile.encode()).hexdigest()[0:6], issue_title, cmd = " ".join(sys.argv), post_resolution_instructions = infoTxt, **kwargs) 
  
    sys.exit(1)

