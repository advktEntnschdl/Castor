import itertools
import os
import time
import subprocess

from .journal import message


class Job:
    def __init__(self, replaceDef, studyDict):
        self.name = getParamStr(replaceDef)
        self.resDir = os.path.abspath(self.name)
        self.replaceDef = replaceDef
        self.type = studyDict.get("type")

        self.studyDict = studyDict

    def generateInputFromTemplates(self):
        for templateFile, replaceDict in self.replaceDef:
            fileFromTemplateFile(
                os.path.join(self.resDir, templateFile),
                os.path.join(self.studyDict["resDir"], templateFile),
                replaceDict,
            )

    def run(self):
        message(" ... running job " + self.name)
        os.mkdir(self.resDir)
        self.generateInputFromTemplates()

        os.chdir(self.resDir)

        if self.type == "edelweiss":
            envVars = dict(os.environ)
            envVars.update(
                {
                    "OMP_NUM_THREADS": str(
                        self.studyDict["edelweissConfig"]["numThreads"]
                    )
                }
            )
            args = [
                "python",
                self.studyDict["edelweissConfig"]["executable"],
                self.studyDict["edelweissConfig"]["inputFile"],
                "--noplot",
            ]
            with open("outStream.txt", "w+") as f:
                subprocess.run(args, stdout=f, stderr=f, env=envVars)
            while not any(".csv" in fn for fn in os.listdir(self.resDir)):
                time.sleep(0.1)

        os.chdir(self.studyDict["resDir"])

        return 0


def generateJobListFromConfig(studyName, studyDict):
    replaceDefsPerJob = getReplaceDefsPerJob(studyName, studyDict)

    jobList = []
    for replaceDef in replaceDefsPerJob:
        jobList.append(Job(replaceDef, studyDict))
    return jobList


def fileFromTemplateFile(filename, templatefilename, replacedict):
    templatefile = open(templatefilename, "r")
    file = open(filename, "w+")

    for line in templatefile:
        for param in replacedict:
            line = line.replace(param, str(replacedict[param]))
        file.write(line)

    templatefile.close()
    file.close()


def getReplaceDefsPerJob(studyName, studyDict):
    replaceDefsPerFile = []
    for templateFile, paramDict in studyDict["replaceInstructions"].items():
        replaceDefsPerFile.append(
            [
                (templateFile, replaceDict)
                for replaceDict in getReplaceDictList(paramDict)
            ]
        )
    replaceDefsPerJob = list(itertools.product(*replaceDefsPerFile))

    return replaceDefsPerJob


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
