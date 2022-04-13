import itertools
import operator
import os
import time
import subprocess
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
import inspect

from .journal import message


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

        self.ppInstructions = studyDict["postProcessingInstructions"]
        ppFuns = self.ppInstructions.get("afterStudy")
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
        possibleTypes = ["EdelweissFE"]

        if studyDict["type"] not in possibleTypes:
            raise ValueError(
                "Type '{}' not a valid study type. Valid study types: {}".format(
                    self.type, ", ".join(map(lambda x: "'{}'".format(x), possibleTypes))
                ),
            )

        return

    def run(self, args):
        os.mkdir(self.resDir)
        os.mkdir(self.inpDir)

        for templateFile in self.replaceInstructions:
            shutil.copy(
                templateFile, os.path.join(self.inpDir, os.path.basename(templateFile))
            )

        if self.type == "EdelweissFE":
            inputFile = self.simConfig["inputFile"]
            if not os.path.basename(inputFile) in map(
                os.path.basename, self.replaceInstructions.keys()
            ):
                shutil.copy(
                    inputFile, os.path.join(self.inpDir, os.path.basename(inputFile))
                )

        os.chdir(self.resDir)

        runJob = operator.methodcaller("run")
        if args.parallel:
            nJobs = len(self.jobList)
            with ProcessPoolExecutor(max_workers=nJobs) as executor:
                futures = list(
                    map(lambda job: executor.submit(runJob, job), self.jobList)
                )

                for future in as_completed(futures):
                    job = future.result()
                    message(" Job finished: " + job.name)
                    pass
        else:
            for result in map(runJob, self.jobList):
                message(" Job finished: " + self.name)
                pass

        self.performPostProcessing()

        return

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


class Job:
    def __init__(self, replaceDef, study):
        self.name = getParamStr(replaceDef)
        self.resDir = os.path.join(study.resDir, self.name)
        self.inpDir = os.path.join(self.resDir, "input")
        self.replaceDef = replaceDef
        self.type = study.type
        self.study = study

        ppFuns = study.ppInstructions.get("afterJob")
        if ppFuns:
            if type(ppFuns) == list:
                self.ppFunList = ppFuns
            else:
                self.ppFunList = [ppFuns]
        else:
            self.ppFunList = []

        return

    def performPostProcessing(self):
        for ppFun in self.ppFunList:
            ppFun(self)

        return

    def generateInputFromTemplates(self):
        for templateFile, replaceDict in self.replaceDef:
            templateFile = os.path.basename(templateFile)
            fileFromTemplateFile(
                os.path.join(self.inpDir, templateFile),
                os.path.join(self.study.inpDir, templateFile),
                replaceDict,
            )
        return

    def run(self):
        message(" Job started: " + self.name)
        os.mkdir(self.resDir)
        os.mkdir(self.inpDir)
        self.generateInputFromTemplates()

        os.chdir(self.resDir)

        if self.type == "EdelweissFE":
            inputFile = os.path.join(
                self.inpDir, os.path.basename(self.study.simConfig["inputFile"])
            )
            envVars = dict(os.environ)
            if self.study.simConfig["numThreads"]:
                envVars.update(
                    {"OMP_NUM_THREADS": str(self.study.simConfig["numThreads"])}
                )
            args = [
                "python",
                self.study.simConfig["executable"],
                inputFile,
                "--noplot",
            ]
            with open("outStream.txt", "w+") as f:
                subprocess.run(args, stdout=f, stderr=f, env=envVars)
            while not any(".csv" in fn for fn in os.listdir(self.resDir)):
                time.sleep(0.1)

        self.performPostProcessing()

        os.chdir(self.study.resDir)

        return self


def fileFromTemplateFile(filename, templatefilename, replacedict):
    templatefile = open(templatefilename, "r")
    file = open(filename, "w+")

    for line in templatefile:
        for param in replacedict:
            line = line.replace(param, str(replacedict[param]))
        file.write(line)

    templatefile.close()
    file.close()

    return


def getReplaceDictList(paramDict):
    replaceDictList = []

    params = paramDict.keys()
    groupedVals = list(itertools.product(*(paramDict[key] for key in paramDict)))

    for valGroup in groupedVals:
        auxList = [None] * (len(params) * 2)
        auxList[1::2] = [str(item) for item in valGroup]  # type: ignore <- pyright does not like slices of type None lists
        auxList[::2] = [item.replace("_", "") for item in params]  # type: ignore

        replaceDictList.append(dict(zip(params, valGroup)))

    return replaceDictList


def getParamStr(replaceDefsPerJob):
    auxList = []
    for replaceDefPerJob in replaceDefsPerJob:
        for key, value in replaceDefPerJob[1].items():
            auxList.append("_".join([key.replace("_", ""), str(value)]))
    paramStr = "_".join(auxList)

    return paramStr
