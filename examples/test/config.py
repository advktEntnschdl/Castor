# import os
import numpy as np
from datetime import datetime

# ---------------------------------------
# post processing
# ---------------------------------------
import matplotlib
import matplotlib.style
from matplotlib import pyplot as plt
from matplotlib import rcParams

paper = (5.875, 4.125)  # size in inches
# paperA4 = (5.875, 4.125) # size in inches

matplotlib.style.use("seaborn-colorblind")
rcParams["font.family"] = ["monospace"]
rcParams["font.monospace"] = ["FreeMono"]

import PyPDF4

mergedPdf = PyPDF4.PdfFileMerger()
# ---------------------------------------

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


def generatePdfPage(job):
    print("Nice Job " + job.name + "!")


def processStudy(study):
    for job in study.jobList:
        print("Nice Job " + job.name + "!")


config = {
    "parameterStudies": {
        studyName: {
            "name": studyName,
            "type": "EdelweissFE",
            "edelweissConfig": {
                "executable": "~/projects/EdelweissFE/edelweiss.py",
                "inputFile": "",
                "numThreads": 1,
            },
            "resDir": studyName,
            "replaceInstructions": {
                # add replace instructions here:
                "templateFile1.inc": paramDict1,
                "templateFile2.inc": paramDict2,
            },
            "postProcessingInstructions": {
                "afterJob": generatePdfPage,
                "afterStudy": processStudy,
            },
            "active": True,
        },
    },
}
