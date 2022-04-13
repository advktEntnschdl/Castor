import subprocess
import time
from datetime import datetime
import os
import numpy as np
from datetime import datetime

# ---------------------------------------
# post processing
# ---------------------------------------
import matplotlib
import matplotlib.style
from matplotlib import pyplot as plt
from matplotlib import rcParams
import PyPDF4

paper = (5.875, 4.125)  # size in inches
# paperA4 = (5.875, 4.125) # size in inches

matplotlib.style.use("seaborn-colorblind")
rcParams["font.family"] = ["monospace"]
rcParams["font.monospace"] = ["FreeMono"]

import PyPDF4

mergedPdf = PyPDF4.PdfFileMerger()
# ---------------------------------------

studyName = "_SET"
studyName += "_"
studyName += datetime.now().strftime("%Y%m%dT%H%M")

templateFile = "triaxTemplate.inp"


def generatePdfPage(job):
    os.chdir(job.resDir)

    fig, ax = plt.subplots()
    fig.set_size_inches(paper[0], paper[1])
    ax.set_xlabel("U")
    ax.set_ylabel("RF")
    ax.grid()
    lines = []

    xData = -np.loadtxt("U.csv")[:, 1]
    yData = -np.loadtxt("RF.csv")[:, 1]

    # if len(lines):
    #    lines[-1].set_alpha(0.0)  # alpha = 0.0 hides the previously drawn line
    #    lines[-1].set_color("gray")

    lines.extend(ax.plot(xData, yData))

    ax.set_title(job.name)
    fig.savefig("plot.pdf")

    clrString = "POINTS displacement magnitude"
    # clrString = "CELLS strain \\(partial\\)"
    # clrString = "CELLS e \\(partial\\)"

    pythonCmd = "/usr/bin/python"
    args = [
        pythonCmd,
        "~/projects/pvpython/renderWarped3D.py",
        "--case=esExport.case",
        "--dpi=300",
        "--width={}".format(paper[0] / 2),
        "--height={}".format(paper[1]),
        "--scalefactor=1.0",
        "--out=contour.png",
        "--colorby",
        clrString,
    ]
    subprocess.run(" ".join(args), shell=True)

    args = [
        "pdfjam",
        "--quiet",
        "--a5paper",
        "--templatesize",
        "'{\\paperwidth}{\\paperheight}'",
        "--outfile",
        "temp.pdf",
        "plot.pdf",
        "contour.png",
    ]
    subprocess.run(" ".join(args), shell=True)

    args = [
        "pdfjam",
        "--quiet",
        "--a4paper",
        "--landscape",
        "--nup",
        "2x1",
        "--outfile",
        "{}.pdf".format(job.name),
        "temp.pdf",
    ]
    subprocess.run(" ".join(args), shell=True)
    os.remove("temp.pdf")

    args = [
        "pdftk",
        os.path.join(job.study.shareDir, "UIBK_A4Landscape.pdf"),
        "stamp",
        "{}.pdf".format(job.name),
        "output",
        "temp.pdf",
    ]
    subprocess.run(" ".join(args), shell=True)
    os.rename("temp.pdf", job.name + ".pdf")

    return


def generateOverview(study):
    mergedPdf = PyPDF4.PdfFileMerger()

    fig, ax = plt.subplots()
    fig.set_size_inches(paper[0], paper[1])
    ax.set_xlabel("U")
    ax.set_ylabel("RF")
    ax.grid()
    ax.set_title(study.name)
    lines = []

    for job in study.jobList:
        os.chdir(job.resDir)

        mergedPdf.append("{}.pdf".format(job.name))
        mergedPdf.addBookmark(job.name, len(mergedPdf.pages) - 1)

        xData = -np.loadtxt("U.csv")[:, 1]
        yData = -np.loadtxt("RF.csv")[:, 1]

        # if len(lines):
        #    lines[-1].set_alpha(0.0)  # alpha = 0.0 hides the previously drawn line
        #    lines[-1].set_color("gray")

        lines.extend(ax.plot(xData, yData, label=job.name))

    os.chdir(study.resDir)
    fig.savefig("plot.pdf")

    mergedPdf.write("{}.pdf".format(studyName))


paramDict = {
    "_PINI_": [10, 20],
    "_GC2G_": [0.1, 0.2],
}

config = {
    "parameterStudies": {
        studyName: {
            "name": studyName,
            "type": "EdelweissFE",
            "edelweissConfig": {
                "executable": "/home/paul/projects/EdelweissFE/edelweiss.py",
                "inputFile": "inputfiles/triaxTemplate.inp",
                "numThreads": 1,
            },
            "resDir": studyName,
            "replaceInstructions": {
                "inputfiles/triaxTemplate.inp": paramDict,
                # add replace instructions here
            },
            "postProcessingInstructions": {
                "afterJob": generatePdfPage,
                "afterStudy": generateOverview,
            },
            "active": True,
        },
    },
}
