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
from getLayout import *

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


def generateJobPage(job):
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
    fig.savefig(os.path.join(job.resDir, "plot.pdf"))

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


def generateStudyPage(study):
    os.chdir(study.resDir)

    fig, ax = plt.subplots()
    fig.set_size_inches(paper[0], paper[1])
    ax.set_xlabel("U")
    ax.set_ylabel("RF")
    ax.grid()
    ax.set_title(study.name)
    contourList = []
    lines = []

    for job in study.jobList:
        xData = -np.loadtxt(os.path.join(job.resDir, "U.csv"))[:, 1]
        yData = -np.loadtxt(os.path.join(job.resDir, "RF.csv"))[:, 1]

        # if len(lines):
        #    lines[-1].set_alpha(0.0)  # alpha = 0.0 hides the previously drawn line
        #    lines[-1].set_color("gray")

        lines.extend(ax.plot(xData, yData, label=job.name))
        contourList.append(os.path.join(job.resDir, "contour.png"))

    ax.legend()
    fig.savefig("plot.pdf")

    layout = getLayout(len(contourList), np.sqrt(2))
    args = [
        "pdfjam",
        "--quiet",
        "--a5paper",
        "--templatesize",
        "'{\\paperwidth}{\\paperheight}'",
        "--nup",
        "{}x{}".format(layout[0], layout[1]),
        "--outfile",
        "contour.pdf",
        " ".join(contourList),
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
        "contour.pdf",
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
        "{}.pdf".format(study.name),
        "temp.pdf",
    ]
    subprocess.run(" ".join(args), shell=True)
    os.remove("temp.pdf")

    args = [
        "pdftk",
        os.path.join(study.shareDir, "UIBK_A4Landscape.pdf"),
        "stamp",
        "{}.pdf".format(study.name),
        "output",
        "temp.pdf",
    ]
    subprocess.run(" ".join(args), shell=True)
    os.rename("temp.pdf", study.name + ".pdf")

    os.remove("plot.pdf")
    os.remove("contour.pdf")

    return


def mergePDFs(study):
    mergedPdf = PyPDF4.PdfFileMerger()

    mergedPdf.append(os.path.join(study.resDir, "{}.pdf".format(study.name)))
    mergedPdf.addBookmark(study.name, len(mergedPdf.pages) - 1)

    for job in study.jobList:
        mergedPdf.append(os.path.join(job.resDir, "{}.pdf".format(job.name)))
        mergedPdf.addBookmark(job.name, len(mergedPdf.pages) - 1)

    os.remove(os.path.join(study.resDir, "{}.pdf".format(study.name)))
    mergedPdf.write("{}.pdf".format(studyName))
    return


paramDict = {
    "_PINI_": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
}


config = {
    "parameterStudies": {
        studyName: {
            "name": studyName,
            "type": "EdelweissFE",
            "simConfig": {
                "executable": "~/projects/EdelweissFE/edelweiss.py",
                "inputFile": "triaxTemplate.inp",
                "numThreads": 1,
            },
            "resDir": studyName,
            "replaceInstructions": {
                "triaxTemplate.inp": paramDict,
                # add replace instructions here
            },
            "postProcessingInstructions": {
                "afterJob": generateJobPage,
                "afterStudy": [generateStudyPage, mergePDFs],
            },
            "active": True,
        },
    },
}
