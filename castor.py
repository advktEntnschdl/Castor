import argparse

from src.reader import readConfig
from src.runner import runStudies
from src.journal import *

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

    success = runStudies(config, args)
