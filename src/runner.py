import os
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed

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

            studyDir = os.path.abspath(studyDict["resDir"])
            studyDict["resDir"] = studyDir

            os.mkdir(studyDir)

            for templateFile in studyDict["replaceInstructions"]:
                shutil.copy(templateFile, os.path.join(studyDir, templateFile))

            os.chdir(studyDir)

            jobList = generateJobListFromConfig(studyName, studyDict)

            if args.parallel:
                message("parallel execution")
                nJobs = len(jobList)
                with ProcessPoolExecutor(max_workers=nJobs) as executor:
                    futureRes = {executor.submit(job.run()): job for job in jobList}

                # for future in as_completed(futureRes):

            else:
                for job in jobList:
                    job.run()

            os.chdir(upmostDir)

    return True
