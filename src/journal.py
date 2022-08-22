# from rich import print
import os
import time
from textwrap import wrap

# from rich import print

maxCharCentered = os.get_terminal_size()[0] - 2  # 70
maxCharAligned = maxCharCentered - 2  # 68


def printHeader():
    printSepline()
    printCenteredLine("")
    printCenteredLine("CASTOR")
    printCenteredLine("")
    printCenteredLine("-- MaterialModelingToolbox --")
    printCenteredLine("github.com/MAteRialMOdelingToolbox")
    printCenteredLine("")
    printSepline()


def infoMessage(*args):
    message(*("INFO:", *args))


def errorMessage(*args):
    message(*("ERROR:", *args))


def message(*args, **kwargs):
    if kwargs.get("align") == "right":
        printFun = printRightAlignedLine
    else:
        printFun = printLeftAlignedLine

    if args:
        string = str(args[0])
        for arg in args[1:]:
            string += " " + str(arg)
        if len(string) < maxCharAligned:
            if not kwargs.get("makeSpace"):
                printFun(string)
            else:
                print("\033[F", end="")
        else:
            stringList = wrap(string, maxCharAligned - 3)
            printFun(stringList[0])
            for string in stringList[1:]:
                if not kwargs.get("makeSpace"):
                    printFun("..." + string)
                else:
                    print("\033[F", end="")
    else:
        printFun(" ")


# class StatusMonitor:
#    def __init__(self, study):
#        self.study = study #Name = study.name
#        self.statusDict = {}
#
#
#    def initializeStatusMonitor(self):
#        for job in self.study.jobList:
#            self.statusDict[job.id] = job.status
#        #message(self.study.name)
#        #for job in self.study.jobList:
#        #    message(job.name)
#        #    message(" " * len(job.name), align="right")
#
#    def updateStatusMonitor(self, job):
#        self.statusDict[job.id] = job.status
#        self.printStatus()
#


def monitor(study, event):
    lastChange = 0.0
    latestChange = 0.0
    printStatus(study)
    while not event.is_set():
        for job in study.jobList:
            latestChange = max(latestChange, os.path.getmtime(job.staFile))
        if latestChange > lastChange:
            lastChange = latestChange
            printStatus(study)
        time.sleep(0.1)
    else:
        return


def printStatus(study):
    message("Study: ", study.name)
    printLine()
    for job in study.jobList:
        message("Job: ", job.name)
        with open(job.staFile, "r") as f:
            line = ""
            for line in f:
                pass
            message(line.strip(), align="right")
    printSepline()


def printSepline():
    printCenteredLine(maxCharCentered * "=")


def printLine():
    printCenteredLine(maxCharCentered * "-")


def printCenteredLine(string):
    print("|{:^{}s}|".format(string, maxCharCentered))


def printLeftAlignedLine(string):
    print("| {:<{}s} |".format(string, maxCharAligned))


def printRightAlignedLine(string):
    print("| {:.>{}s} |".format(string, maxCharAligned))
