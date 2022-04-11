import itertools
import os


class Job:
    def __init__(self, replaceDef, studyDict):
        self.name = getParamStr(replaceDef)
        self.resDir = os.path.abspath(self.name)
        self.replaceDef = replaceDef
        self.type = studyDict.get("type")

        self.studyDict = studyDict

    def run(self):
        os.mkdir(self.resDir)
        os.chdir(self.resDir)
        os.mkdir("test2")
        os.chdir(self.studyDict["resDir"])
        return True


def generateJobListFromConfig(studyName, studyDict):
    replaceDefsPerJob = getReplaceDefsPerJob(studyName, studyDict)

    jobList = []
    for replaceDef in replaceDefsPerJob:
        jobList.append(Job(replaceDef, studyDict))
    return jobList


def file_from_template_file(filename, templatefilename, replacedict):
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


# def getJobDict(studyDict):
#    jobDict = {}
#    paramDict = studyDict["paramDict"]
#
#    params = paramDict.keys()
#    groupedVals = list(itertools.product(*(paramDict[key] for key in paramDict)))
#
#    for valGroup in groupedVals:
#        auxList = [None] * (len(params) * 2)
#        auxList[1::2] = [str(item) for item in valGroup]  # type: ignore <- pyright does not like slices of type None lists
#        auxList[::2] = [item.replace("_", "") for item in params]  # type: ignore
#
#        paramStr = "_".join(auxList)  # type: ignore
#
#        # jobName = "_".join([studyDict["studyName"], paramStr])
#        jobName = paramStr
#        replaceDict = dict(zip(params, valGroup))
#
#        jobDict.update(
#            {
#                jobName: {
#                    "name": jobName,
#                    "subfolder": paramStr,
#                    "replaceDict": replaceDict,
#                    "paramStr": paramStr,
#                }
#            }
#        )
#    return jobDict
