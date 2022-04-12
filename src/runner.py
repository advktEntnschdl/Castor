import os

from .journal import *
from .jobUtils import *


def runStudies(config, args):
    printSepline()

    upmostDir = os.getcwd()
    if "parameterStudies" in config:
        for studyName, studyDict in config["parameterStudies"].items():

            study = Study(studyDict)

            if not study.active:
                message("  -->  " + studyName + "(inactive)")
                return

            message(" " + study.name + " (active) ")

            study.run(args)

            os.chdir(upmostDir)

    return True
