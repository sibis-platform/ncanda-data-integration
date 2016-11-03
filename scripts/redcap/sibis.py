"""
Temporary SIBIS Logging
"""
import json

def logging(id, message, **kwargs):
    log = dict(experiment_site_id=id,
               error=message)
    log.update(kwargs)
    try:  
      print(json.dumps(log, sort_keys=True))

    except Exception as e: 
      print "ERROR: redcap/sibis.py: logging: " + id + "  ===== message: " + message + " ====== kwargs" + str(kwargs)   

