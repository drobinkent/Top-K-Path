#from p4.v1 import p4runtime_pb2
import json
import logging.handlers
import sys

import ConfigConst as ConfConst
import InternalConfig as intCoonfig
import P4Runtime.StatisticsPuller
import P4Runtime.StatisticsPuller
import P4Runtime.StatisticsPuller
import P4Runtime.StatisticsPuller
import P4Runtime.SwitchUtils as swUtils
import P4Runtime.leafSwitchUtils
import P4Runtime.leafSwitchUtils
import P4Runtime.leafSwitchUtils
import P4Runtime.leafSwitchUtils
from P4Runtime import P4DeviceManager as jp
from P4Runtime.P4DeviceManager import DeviceType
from P4Runtime.utils import getDeviceTypeFromName, reverseAndCreateNewLink

logger = logging.getLogger('DCNTEController')
logger.handlers = []
# read initial config file
#logging.config.fileConfig("logging.conf")
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)


class MyP4Controller():
    def __init__(self, cfgFileName, dpAlgo = ConfConst.DataplnaeAlgorithm.DP_ALGO_BASIC_ECMP):
        self.nameToSwitchMap = {}
        self.nameToHostMap = {}
        self.cfgFileName = cfgFileName
        self.dpAlgo = dpAlgo
        print("Starting MyP4Controller with config file ",cfgFileName)
        self.loadCFG(cfgFileName)


    def loadCFG(self,cfgfileName):
        cfgFile = open(cfgfileName)
        obj = json.load(fp=cfgFile)
        for devName in obj["devices"]:
            try:
                dev = jp.Device.from_dict(devName, obj["devices"][devName], dpAlgo= self.dpAlgo )
                s = devName.index("device:") + len("device:")  #Strp from "device:" prefix from device name. this was created for onos.
                devName = devName[s:len(devName)]
                self.nameToSwitchMap[devName] = dev
                logger.info("New dev is "+str(dev))
                #dev.initialSetup()
            except:
                e = sys.exc_info()
                logger.info("Error in initializing ", devName)
                logger.info("Error is "+str( e))
        for portLoc in obj["ports"]:
            p = jp.Port.from_dict(obj["ports"][portLoc])
            logger.info("New port is "+ str(p))
            pass
        for hostMac in obj["hosts"]:
            h = jp.Host.from_dict( obj["hosts"][hostMac])
            self.nameToHostMap[h.basic.name] = h
            logger.info("New host is "+str(h))
        for i in range (0, len(obj["alllinks"]["links"])):
            l = jp.Link.from_dict(obj["alllinks"]["links"][i])
            logger.info("Attching :Link is "+str(l))
            self.attachLink(l)
            logger.info("Attching link from reverse direction:Link is "+str(l))
            self.attachLink(reverseAndCreateNewLink(l))
        cfgFile.close()
        logger.info("Finished reading and loading cfg")

    def attachLink(self, l):
        #logger.debug("Processing link:"+str(l))
        #logger.debug("link Start node "+str(l.node1)+" is of type "+str(getDeviceTypeFromName(l.node1)))
        #logger.debug("link end node "+str(l.node2)+" is of type "+str(getDeviceTypeFromName(l.node2)))
        if(getDeviceTypeFromName(l.node1) == DeviceType.INVALID) :
            logger.info("Node 1 of link: "+l+" is of type INVALID. Exiting")
            exit(-1)
        if(getDeviceTypeFromName(l.node2) == DeviceType.INVALID) :
            logger.info("Node 2 of link: "+l+" is of type INVALID. Exiting")
            exit(-1)
        # From here it means both end of the link is valid.
        if((getDeviceTypeFromName(l.node1) == DeviceType.LEAF_SWITCH) or
        (getDeviceTypeFromName(l.node1) == DeviceType.SPINE_SWITCH) or
        (getDeviceTypeFromName(l.node1) == DeviceType.SUPER_SPINE_SWITCH)):
            srcSwitch = self.nameToSwitchMap.get(l.node1)
            if (srcSwitch == None):
                logger.critical("Node 1 of link"+str(l)+"Not found in nameToSwitchMap")
                exit(-1)
            else:
                if((getDeviceTypeFromName(l.node2) == DeviceType.LEAF_SWITCH) or
                (getDeviceTypeFromName(l.node2) == DeviceType.SPINE_SWITCH) or
                (getDeviceTypeFromName(l.node2) == DeviceType.SUPER_SPINE_SWITCH)):
                    destSwitch = self.nameToSwitchMap.get(l.node2)
                    if (destSwitch == None):
                        logger.critical("Node 2 of link"+str(l)+"Not found in nameToSwitchMap")
                        exit(-1)
                    else:
                        if (getDeviceTypeFromName(l.node2) == DeviceType.LEAF_SWITCH):
                            srcSwitch.portToLeafSwitchMap[l.port1] = destSwitch
                        elif (getDeviceTypeFromName(l.node2) == DeviceType.SPINE_SWITCH):
                            srcSwitch.portToSpineSwitchMap[l.port1] = destSwitch
                        elif (getDeviceTypeFromName(l.node2) == DeviceType.SUPER_SPINE_SWITCH):
                            srcSwitch.portToSuperSpineSwitchMap[l.port1] = destSwitch
                elif(getDeviceTypeFromName(l.node2) == DeviceType.HOST):
                    destHost = self.nameToHostMap.get(l.node2)
                    if (destHost == None):
                        logger.critical("Node 2 of link"+str(l)+"Not found in nametoHostMap")
                        exit(-1)
                    else:
                        srcSwitch.portToHostMap[l.port1] = destHost
        elif (getDeviceTypeFromName(l.node1) == DeviceType.HOST):
            srcHost = self.nameToHostMap.get(l.node1)
            if (srcHost == None):
                logger.critical("Node 1 of link"+str(l)+"Not found in nameToHostMap")
                exit(-1)
            else:
                if (getDeviceTypeFromName(l.node2) == DeviceType.LEAF_SWITCH):
                    destSwitch = self.nameToSwitchMap.get(l.node2)
                    if (destSwitch == None):
                        logger.critical("Node 2 of link"+str(l)+"Not found in nameToSwitchMap")
                        exit(-1)
                    else:
                        srcHost.portToLeafSwitchMap[l.port1] = destSwitch

        pass

    # For leaf switches, incoming ports from leaf switches will have queue rate " hostToLeafMaxQueueRate =  baseQueueRate*hosttoLeafOverSupscriptionRatio" and
    # outgoing ports toward spine switches will have queue rate of leafToSpineMaxQueueRate =  baseQueueRate. This queue rate setup is equivalent to link speed for bmv2 simpleSwitch.
    # Same way, in spine switches, incoming ports from leaf switches will have queue rate of baseQuerate
    def initialDeviceRouteAndRateSetup(self, queueRateForHostFacingPortsOfLeafSwitch, queueRateForSpineFacingPortsOfLeafSwitch,
                                       queueRateForLeafSwitchFacingPortsOfSpineSwitch, queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch,
                                       queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch, queueRateForExternalInternetFacingPortsOfSuperSpineSwitch):
        #------------Usually  buffer size should be Delay *  bandwidth . for bmv2 based testing this have to be represented and configured through Queue depth.
        # ------ So we will multiply port bandwidth by a factor to estimate the Delay *  BW . So by this factor we are actually estimating the Delay factor.
        queueRateToDepthFactor = ConfConst.QUEUE_RATE_TO_QUEUE_DEPTH_FACTOR

        for sName in self.nameToSwitchMap.keys():
            s = (self.nameToSwitchMap.get(sName))
            logger.info("Setting up Queue rate for all switch. This is equavalent to setup line rate setup in bmv2 devices")

            # #s = Device()
            if (s.fabric_device_config.switch_type == intCoonfig.SwitchType.LEAF ):
                s.queueRateSetupForLeafSwitch(queueRateForHostFacingPortsOfLeafSwitch, queueRateForSpineFacingPortsOfLeafSwitch,queueRateToDepthFactor)
            if (s.fabric_device_config.switch_type == intCoonfig.SwitchType.SPINE ):
                s.queueRateSetupForSpineSwitch(queueRateForLeafSwitchFacingPortsOfSpineSwitch, queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch, queueRateToDepthFactor)
            if (s.fabric_device_config.switch_type == intCoonfig.SwitchType.SUPER_SPINE ):
                s.queueRateSetupForSuperspineSwitch(queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch, queueRateForExternalInternetFacingPortsOfSuperSpineSwitch, queueRateToDepthFactor)
            swUtils.addCloneSessionForEachPort(s, s.maxPort)
            #TODO : need to save the metric level in device. So that we4 can later use dynamic scale up for metrices

            s.initialCommonSetup(self.nameToSwitchMap)
            #====================
            # -- execute initial setup tasks
            s.ctrlPlaneLogic.setup(self.nameToSwitchMap)
            # if (testScenario == ConfConst.TestScenario.BASIC_ECMP):
            #     print("This call is for baseline setup and should only work if in P4 file we have enabled Baseline flag.")
            #     s.initialBaseLineSetup()
            #     s.ctrlPlaneLogic.addGroupsForStepBasedRouting()
            #     s.ctrlPlaneLogic.initializeUpstreamRouting()
            # elif (testScenario == ConfConst.DP_ALGO_CP_ASSISTED_POLICY_ROUTING):
            #     print("Setting Data plane programs for our medianet dcn solution")
            #     # this section will have code for evaluation that are special to our solution. For example how many times a table entry habe been updated and other.
            #     pass
            # This section will contain code for evaluation report of both the solution

    def startMonitoringFromController(self):
        # this method will pull various counter and register values from the switches and plot data accordingly.
        #Also save the collected statitstics for each device in corresponding data structure.
        for dev in self.nameToSwitchMap:
            self.statisticsPuller = P4Runtime.StatisticsPuller.StatisticsPuller(self.nameToSwitchMap, dev)





p4ctrlr = MyP4Controller("./MininetSimulator/Build/Internalnetcfg.json", dpAlgo=ConfConst.ALGORITHM_IN_USE)
print(p4ctrlr)

p4ctrlr.initialDeviceRouteAndRateSetup( queueRateForHostFacingPortsOfLeafSwitch = ConfConst.queueRateForHostFacingPortsOfLeafSwitch ,
                                        queueRateForSpineFacingPortsOfLeafSwitch = ConfConst.queueRateForSpineFacingPortsOfLeafSwitch,
                                        queueRateForLeafSwitchFacingPortsOfSpineSwitch= ConfConst.queueRateForLeafSwitchFacingPortsOfSpineSwitch,
                                        queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch=ConfConst.queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch,
                                        queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch=ConfConst.queueRateForSpineSwitchFacingPortsOfSuperSpineSwitch,
                                        queueRateForExternalInternetFacingPortsOfSuperSpineSwitch=ConfConst.queueRateForExternalInternetFacingPortsOfSuperSpineSwitch
                                        )

p4ctrlr.startMonitoringFromController()







