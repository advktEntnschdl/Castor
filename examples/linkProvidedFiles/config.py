import os

studyName = "_linkedMesh"

inputTemplate = "input.inp"

paramDict = {
    "_E_": [190000, 210000],
    "_Nu_": [0.2, 0.3],
}


def writeSummary(study):
    with open(os.path.join(study.resDir, "summary.csv"), "w") as fOut:
        fOut.write("job, maxU, maxRF\n")
        for job in study.jobList:
            with open(os.path.join(job.resDir, "U.csv")) as fU:
                maxU = fU.readlines()[-1].split()[1]
            with open(os.path.join(job.resDir, "RF.csv")) as fRF:
                maxRF = fRF.readlines()[-1].split()[1]
            fOut.write("{}, {}, {}\n".format(job.name, maxU, maxRF))

    return


# show which files were linked to the study and to the jobs
def reportProvidedFiles(study):
    print()
    for shareDir in [study.shareDir] + [job.shareDir for job in study.jobList]:
        linked = 0
        copied = 0
        for root, dirs, files in os.walk(shareDir):
            for file in files:
                if os.path.islink(os.path.join(root, file)):
                    linked += 1
                else:
                    copied += 1
        print(
            "{:<40s} {:d} file(s) linked, {:d} copied".format(
                os.path.relpath(shareDir, os.path.dirname(study.resDir)),
                linked,
                copied,
            )
        )
    print()

    return


config = {
    "parameterStudies": {
        studyName: {
            "name": studyName,
            "type": "bash",
            "simConfig": {
                "command": "bash share/solve.sh",
                "inputFile": inputTemplate,
            },
            "resDir": studyName,
            "providedFiles": [inputTemplate, "solve.sh", "mesh"],
            # the mesh is shared by all jobs, so the jobs link it
            "linkProvidedFiles": ["mesh"],
            "replaceInstructions": {
                inputTemplate: paramDict,
            },
            "preProcessingInstructions": {},
            "postProcessingInstructions": {
                "afterStudy": [writeSummary, reportProvidedFiles],
            },
            "active": True,
        },
    },
}
