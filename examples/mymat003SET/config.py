# import os
from datetime import datetime

edelwCmd = "python ~/projects/EdelweissFE/edelweiss.py"
# edelwCmd = "OMP_NUM_THREADS=12 python ~/projects/EdelweissFE/edelweiss.py"
pythonCmd = "/usr/bin/python"

studyName = "_SET"
studyName += "_"
studyName += datetime.now().strftime("%Y%m%dT%H%M")

templateFile = "triaxTemplate.inp"

paramDict = {
    "_PINI_": [10, 20],
    "_GC2G_": [0.1],
}

# wDir = os.getcwd()

# ---------------------- only config dir is read
config = (
    {
        "parameterStudies": {
            studyName: {
                "type": "EdelweissFE",
                "resDir": studyName,
                "replaceDefs": {
                    "inpFile": {"paramDict": paramDict, "templateFile": templateFile},
                    "": {"paramDict": {}, "templateFile": ""},
                    # add replace instructions here
                },
                "remove": True,
            },
        }
    },
)
