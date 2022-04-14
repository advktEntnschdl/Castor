from rich.pretty import pprint
from rich import print


def printHeader():
    printSepline()
    print("|{:^70s}|".format("CASTOR"))
    print("|{:^70s}|".format(""))
    print("|{:^70s}|".format("-- MaterialModelingToolbox --"))
    print("|{:^70s}|".format("github.com/MAteRialMOdelingToolbox"))
    print("|{:^70s}|".format(""))
    printSepline()


def errorMessage(*args):

    message(*(" ERROR:", *args))


def message(*args):

    string = str(args[0])
    for arg in args[1:]:
        string += " " + str(arg)

    print("|{:<70s}|".format(string))


def printSepline():
    message(70 * "=")


def printLine():
    message(70 * "-")
