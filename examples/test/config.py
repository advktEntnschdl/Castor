# import os
from datetime import datetime

edelwCmd = "python ~/projects/EdelweissFE/edelweiss.py"
# edelwCmd = "OMP_NUM_THREADS=12 python ~/projects/EdelweissFE/edelweiss.py"
pythonCmd = "/usr/bin/python"

studyName = "_SET"
studyName += "_"
studyName += datetime.now().strftime("%Y%m%dT%H%M")

templateFile = "triaxTemplate.inp"

paramDict1 = {
    "_A_": [1, 2, 3, 4],
    "_B_": [2],
}
paramDict2 = {
    "_C_": [3, 4],
    "_D_": [4],
}

# wDir = os.getcwd()

# ---------------------- only config dir is read
config = {
    "parameterStudies": {
        studyName: {
            "type": "edelweiss",
            "edelweissConfig": {
                "executable": "~/projects/EdelweissFE/edelweiss.py",
                "numThreads": 1,
            },
            "resDir": studyName,
            "replaceInstructions": {
                # add replace instructions here:
                "templateFile1.inc": paramDict1,
                "templateFile2.inc": paramDict2,
            },
            "active": True,
        },
    },
}
