"""
Temporary SIBIS Logging
"""
import json

def logging(id, message, **kwargs):
    log = dict(experiment_site_id=id,
               error=message)
    log.update(kwargs)
    print(json.dumps(log, sort_keys=True))
