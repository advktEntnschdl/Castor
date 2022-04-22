import argparse
import os

from src.journal import message, printHeader, printSepline
from src.reader import readConfig
from src.study import Study

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="study",
        description="A tool for running parameter studies",
    )

    parser.add_argument("file", type=str, nargs=1)
    parser.add_argument("--parallelJobs", type=int, default=[1], nargs=1)
    parser.add_argument("--overwrite", default=False, action="store_true")

    args = parser.parse_args()
    printHeader()

    message("reading config from {:}... ".format(args.file[0]))
    config = readConfig(args.file[0])

    printSepline()

    upmostDir = os.getcwd()
    if "parameterStudies" in config:
        for studyName, studyDict in config["parameterStudies"].items():
            study = Study(studyDict)
            if study.active:
                message(study.name + " (active) ")
                study.run(args)
                os.chdir(upmostDir)
            else:
                message(" -->  " + studyName + "(inactive)")

    printSepline()
