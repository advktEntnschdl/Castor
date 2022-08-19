import argparse
import os

from src.journal import infoMessage, message, printHeader, printSepline
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
    parser.add_argument("--onlyPostProcessing", default=False, action="store_true")

    args = parser.parse_args()
    printHeader()

    message("reading config from {:}... ".format(args.file[0]))
    config = readConfig(args.file[0])

    printSepline()

    upmostDir = os.getcwd()
    if "parameterStudies" in config:
        for studyName, studyDict in config["parameterStudies"].items():
            study = Study(studyDict, args)
            if study.active:
                # message("Study", study.name, "(active)")
                if not args.onlyPostProcessing:
                    study.run(args)
                else:
                    message(
                        "Functions provided to study are not overwritten by design; this may be changed later."
                    )
                    for job in study.jobList:
                        job.performPostProcessing()
                    study.performPostProcessing()

                os.chdir(upmostDir)
            else:
                message(" -->  " + studyName + "(inactive)")
    else:
        infoMessage(
            'Use field "parameterStudies" in config dictionary to define a study.'
        )
