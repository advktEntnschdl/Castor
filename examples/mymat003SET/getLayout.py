import numpy as np
import math


def getLayout(count, aspect):
    def getAspect(tup):
        return tup[0] / tup[1]

    def getArea(tup):
        return tup[0] * tup[1]

    def getRelError(val, ref):
        return abs(val - ref) / ref

    def floorCeil(val):
        return (math.floor(val), math.ceil(val))

    def addsome(tup):
        return (tup[0] - 1, tup[0], tup[1], tup[1] + 1)

    def score(tup):
        errMeasures = {
            "area": {"weight": 0.6, "error": getRelError(getArea(tup), count)},
            "lastRow": {"weight": 0.2, "error": (getArea(tup) - count) / tup[0]},
            "aspect": {"weight": 1.0, "error": getRelError(getAspect(tup), aspect)},
        }

        weigthedScoreList = [
            item["weight"] * item["error"] for item in errMeasures.values()
        ]

        # return np.linalg.norm(weigthedScoreList, ord=2)
        return sum(weigthedScoreList)

    idealCols = np.sqrt(count / aspect)
    idealRows = idealCols * aspect

    possibleCols = floorCeil(idealCols)
    possibleRows = floorCeil(idealRows)

    possibleCols = addsome(possibleCols)
    possibleRows = addsome(possibleRows)

    # print([(r, c) for r in possibleRows for c in possibleCols])

    possibleLayouts = [
        (r, c) for r in possibleRows for c in possibleCols if r * c >= count
    ]

    scoreList = [score(Layout) for Layout in possibleLayouts]
    idxMin = np.argmin(scoreList)

    # print("--------------")
    # print(idealRows)
    # print(idealCols)
    # print(possibleLayouts[idxMin])
    # print("--------------")

    # print("--------------")
    # print("n: {}".format(count))
    # print(possibleLayouts)
    # print(scoreList)
    # print("--------------")

    return possibleLayouts[idxMin]
