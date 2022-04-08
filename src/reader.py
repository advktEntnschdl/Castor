import sys
import os


def readConfig(configFile):
    (head, tail) = os.path.split(configFile)
    sys.path.append(head)
    (root, ext) = os.path.splitext(tail)
    config = __import__(root).config

    return config
