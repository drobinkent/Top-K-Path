import random as rnd
import Testingconst as tstConst

def generateRandomProbeResult(allPortsAsList = [5,6,7,8]):
    totalNormalizedRate = len(allPortsAsList)
    newPortRateList = []
    for i in range(0, len(allPortsAsList)):
        x = rnd.uniform(0.2, 0.5)
        x = round(x, 1)
        tple1 = (allPortsAsList[i], x)
        newPortRateList.append(tple1)
    newPortRateList.sort(key=lambda x: x[1], reverse=False)
    return newPortRateList


def printRandomProbeResults(randomProberesult):
    for i in range(0, len(randomProberesult)):
        print(randomProberesult[i])

def generateAndStoreRandomProbeResults(times):
    probeResultsAsList = []
    for i in range(0, times):
        probeResult = generateRandomProbeResult()
        probeResultsAsList.append(probeResult)

    print(probeResultsAsList)
        #printRandomProbeResults(probeResultsAsList)

generateAndStoreRandomProbeResults(times=100) # for each 5 sec create a new config
for i in range (0, len(tstConst.portRateConfigs)):
    print(tstConst.portRateConfigs[i][0][0])  # this gives port
    print("\n")
    print(tstConst.portRateConfigs[i][0][1]) # this gives rate

    #if any port have rate 0 that means the port will be deleted
