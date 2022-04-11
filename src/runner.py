import os
import shutil

from .journal import *
from .jobUtils import *

def runStudy(config, args):
    printSepline()

    upmostDir = os.getcwd()
    if "parameterStudies" in config:
        for studyName, studyDict in config["parameterStudies"].items():

            if not studyDict.get("active"):
                message("  -->  " + studyName + "(inactive)")
                return

            message(" " + studyName + " (active) ")
            
            studyDict["resDir"] = os.path.abspath(studyDict["resDir"])
            os.mkdir(studyDict["resDir"])
            os.chdir(studyDict["resDir"])
        
            jobList = generateJobListFromConfig(studyName, studyDict)

            for job in jobList:
                job.run()

            os.chdir(upmostDir)

    return True
