import argparse
import os

from src.reader import readConfig
from src.journal import *
from src.jobUtils import *

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="study",
        description="A tool for running parameter studies",
    )

    parser.add_argument(
        "file",
        type=str,
        nargs=1,
    )
    parser.add_argument("--parallel", action="store_true", default=False)

    # help=" 0: no parallelization (default); 1: parallel execution of simulations; 2:run parallel minimize (L-BGFS method only); 3: combines option 1 and 2 (L-BGFS method only)")
    # parser.add_argument(    "--createPlots",
    #                        action="store_true",
    #                        default=False)

    args = parser.parse_args()
    printHeader()

    message(" reading config from {:}... ".format(args.file[0]))
    config = readConfig(args.file[0])

    printSepline()

    upmostDir = os.getcwd()
    if "parameterStudies" in config:
        for studyName, studyDict in config["parameterStudies"].items():
            study = Study(studyDict)
            if study.active:
                message(" " + study.name + " (active) ")
                study.run(args)
                os.chdir(upmostDir)
            else:
                message("  -->  " + studyName + "(inactive)")

    printSepline()
