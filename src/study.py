import itertools
import operator
import os
from posixpath import relpath
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
import inspect
import pickle

from .journal import message, errorMessage
from .job import *


class Study:
    def __init__(self, studyDict):
        self.checkInput(studyDict)

        self.name = studyDict.get("name")
        self.resDir = os.path.abspath(studyDict.get("resDir"))
        self.inpDir = os.path.join(self.resDir, "input")
        head = os.path.split(inspect.stack()[1].filename)[0]
        self.shareDir = os.path.join(os.path.abspath(head), "share")

        self.type = studyDict.get("type")
        self.simConfig = studyDict["simConfig"]

        self.replaceInstructions = studyDict.get("replaceInstructions")

        self.preProcessingInstructions = studyDict["preProcessingInstructions"]
        prepFuns = self.preProcessingInstructions.get("beforeStudy")

        if prepFuns:
            if type(prepFuns) == list:
                self.prepFunList = prepFuns
            else:
                self.prepFunList = [prepFuns]
        else:
            self.prepFunList = []

        self.postProcessingInstructions = studyDict["postProcessingInstructions"]
        ppFuns = self.postProcessingInstructions.get("afterStudy")

        if ppFuns:
            if type(ppFuns) == list:
                self.ppFunList = ppFuns
            else:
                self.ppFunList = [ppFuns]
        else:
            self.ppFunList = []

        self.active = studyDict.get("active") == True

        self.generateJobListFromConfig()

        return

    def checkInput(self, studyDict):
        possibleTypes = ["EdelweissFE", "mpFEM"]

        if studyDict["type"] not in possibleTypes:
            raise ValueError(
                "Type '{}' not a valid study type. Valid study types: {}".format(
                    self.type, ", ".join(map(lambda x: "'{}'".format(x), possibleTypes))
                ),
            )

        return

    def run(self, args):
        if os.path.exists(self.resDir):
            if args.overwrite:
                message("Overwriting directory {}".format(self.resDir))
                shutil.rmtree(self.resDir)
            else:
                message(
                    "Directory {} exists. Use --overwrite keyword if you want to overwrite it.".format(
                        self.resDir
                    )
                )

        os.mkdir(self.resDir)
        self.export()

        if self.type == "EdelweissFE":

            os.mkdir(self.inpDir)
            for templateFile in self.replaceInstructions:
                shutil.copy(
                    templateFile,
                    os.path.join(self.inpDir, os.path.basename(templateFile)),
                )

            inputFile = self.simConfig["inputFile"]
            if not os.path.basename(inputFile) in map(
                os.path.basename, self.replaceInstructions.keys()
            ):
                shutil.copy(
                    inputFile, os.path.join(self.inpDir, os.path.basename(inputFile))
                )

        elif self.type == "mpFEM":
            inputFolder = self.simConfig["input"]
            shutil.copytree(inputFolder, self.inpDir)

        os.chdir(self.resDir)

        self.performPreProcessing()

        runJob = operator.methodcaller("run")
        if args.parallelJobs[0] > 1:
            nJobs = len(self.jobList)
            with ProcessPoolExecutor(max_workers=args.parallelJobs[0]) as executor:
                futures = list(
                    map(lambda job: executor.submit(runJob, job), self.jobList)
                )

                for future in as_completed(futures):
                    pass
        else:
            for result in map(runJob, self.jobList):
                pass

        self.performPostProcessing()

        return

    def performPreProcessing(self):
        for ppFun in self.prepFunList:
            ppFun(self)

    def performPostProcessing(self):
        for ppFun in self.ppFunList:
            ppFun(self)

        return

    def generateJobListFromConfig(self):
        replaceDefsPerJob = self.getReplaceDefsPerJob()

        jobList = []
        for replaceDef in replaceDefsPerJob:
            jobList.append(Job(replaceDef, self))
        self.jobList = jobList

        return

    def getReplaceDefsPerJob(self):
        replaceDefsPerFile = []
        for templateFile, paramDict in self.replaceInstructions.items():
            templateFile = os.path.basename(templateFile)
            replaceDefsPerFile.append(
                [
                    (os.path.join(self.inpDir, templateFile), replaceDict)
                    for replaceDict in getReplaceDictList(paramDict)
                ]
            )
        replaceDefsPerJob = list(itertools.product(*replaceDefsPerFile))

        return replaceDefsPerJob

    def export(self):
        exportName = "jobNames.pickle"
        jobNames = [job.name for job in self.jobList]

        with open(os.path.join(self.resDir, exportName), "wb") as fout:
            pickle.dump(jobNames, fout)

        return
