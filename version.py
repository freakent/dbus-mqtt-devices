import logging
import os
import sys

def VERSION():
    try:                                                    
        base = os.path.dirname(os.path.realpath(__file__))  
        with open(os.path.join(base, 'VERSION'), 'r') as version_file:
            version = version_file.read().strip()
            return version
    except IOError as e:                                                                            
        logging.error("I/O error(%s): %s", e.errno, e.strerror)
    except: #handle other exceptions such as attribute errors                                       
        logging.error("Unexpected error: %s", sys.exc_info()[0])