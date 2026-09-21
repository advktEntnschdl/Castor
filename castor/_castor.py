import argparse
import os

from castor.journal import infoMessage, message, printHeader, printSepline
from castor.reader import readConfig
from castor.study import Study, loadStudy


def main():

    parser = argparse.ArgumentParser(
        prog="study",
        description="A tool for running parameter studies",
    )

    parser.add_argument("file", type=str, nargs=1)
    parser.add_argument("--parallelJobs", type=int, default=[1], nargs=1)
    parser.add_argument("--overwrite", default=False, action="store_true")
    parser.add_argument("--onlyPostProcessing", default=False, action="store_true")

    args = parser.parse_args()
    printHeader()

    message("reading config from {:}... ".format(args.file[0]))
    config = readConfig(args.file[0])

    printSepline()

    upmostDir = os.getcwd()
    if "parameterStudies" in config:
        for studyName, studyDict in config["parameterStudies"].items():
            # check before constructing; the constructor already sets up the
            # result directories
            if not studyDict.get("active", True):
                message(" -->  " + studyName + "(inactive)")
                continue

            if args.onlyPostProcessing:
                # reuse the existing study; constructing a new one would
                # discard the results to be post processed
                study = loadStudy(studyDict)
                message(
                    "Functions provided to study are not overwritten by design; this may be changed later."
                )
                for job in study.jobList:
                    job.performPostProcessing()
                study.performPostProcessing()
            else:
                study = Study(studyDict, args)
                study.run(args)

            os.chdir(upmostDir)
    else:
        infoMessage(
            'Use field "parameterStudies" in config dictionary to define a study.'
        )


if __name__ == "__main__":
    main()
