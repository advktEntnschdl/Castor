import itertools


def file_from_template_file(filename, templatefilename, replacedict):
    templatefile = open(templatefilename, "r")
    file = open(filename, "w+")

    for line in templatefile:
        for param in replacedict:
            line = line.replace(param, str(replacedict[param]))
        file.write(line)

    templatefile.close()
    file.close()


def getJobDict(studyDict):
    jobDict = {}
    paramDict = studyDict["paramDict"]

    groupedVals = list(itertools.product(*(paramDict[key] for key in paramDict)))
    params = paramDict.keys()

    for valGroup in groupedVals:
        auxList = [None] * (len(params) * 2)
        auxList[1::2] = [str(item) for item in valGroup]  # type: ignore <- pyright does not like slices of type None lists
        auxList[::2] = [item.replace("_", "") for item in params]  # type: ignore

        paramStr = "_".join(auxList)  # type: ignore

        # jobName = "_".join([studyDict["studyName"], paramStr])
        jobName = paramStr
        replaceDict = dict(zip(params, valGroup))

        jobDict.update(
            {
                jobName: {
                    "name": jobName,
                    "subfolder": paramStr,
                    "replaceDict": replaceDict,
                    "paramStr": paramStr,
                }
            }
        )
    return jobDict
