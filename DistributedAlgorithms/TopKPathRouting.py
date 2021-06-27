import logging.handlers
import math
import threading
import time

import ConfigConst
import DistributedAlgorithms.Testingconst as tstConst
import ConfigConst as ConfConst
import InternalConfig
import InternalConfig as intCoonfig
from DistributedAlgorithms.TopKPathManager import TopKPathManager
import P4Runtime.SwitchUtils as swUtils
from TestCaseDeployer import TestCommandDeployer

logger = logging.getLogger('Shell')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)


def getRank(pathRate):
    if(pathRate >= 0) and (pathRate <= 0.325):
        return 3
    if(pathRate > 0.325) and (pathRate <= 0.45):
        return 2
    if(pathRate > 0.45) and (pathRate <= 0.575):
        return 1
    if(pathRate > 0.575) and (pathRate <= 1):
        return 0

    return 0

class TopKPathRouting:


    def __init__(self, dev):
        self.p4dev = dev
        self.testOperationIndex =0
        self.torIdToKpathManagerMap = {}
        if self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.LEAF:
            for i in range (0,ConfConst.MAX_TOR_SUBNET):
                topKPathManager = TopKPathManager(dev = self.p4dev, k=ConfConst.K)
                self.torIdToKpathManagerMap[i] = topKPathManager
        elif self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.SPINE:
            # self.topKPathManager = TopKPathManager(dev = self.p4dev, k=len(self.p4dev.portToSuperSpineSwitchMap.keys()))
            self.topKPathManager = TopKPathManager(dev = self.p4dev, k=ConfConst.K)
        elif self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.SUPER_SPINE:
            self.topKPathManager = TopKPathManager(dev = self.p4dev, k=ConfConst.K) # by default add space for 16 ports in super spine. This is not actually used in our simulation
            pass

        return
    def initMAT(self, switchObject, bitMaskLength):
        allOneMAsk = BinaryMask(bitMaskLength)
        allOneMAsk.setAllBitOne()
        allOneMAskBinaryString = allOneMAsk.getBinaryString()
        for j in range(0, bitMaskLength):
            mask = BinaryMask(bitMaskLength)
            mask.setNthBitWithB(n=j,b=1)
            maskAsString = mask.getBinaryString()
            switchObject.addTernaryMatchEntry( "IngressPipeImpl.k_path_selector_control_block.kth_path_finder_mat",
                                               fieldName = "local_metadata.kth_path_selector_bitmask",
                                               fieldValue = allOneMAskBinaryString, mask = maskAsString,
                                               actionName = "IngressPipeImpl.k_path_selector_control_block.kth_path_finder_action_with_param",
                                               actionParamName = "rank",
                                               actionParamValue = str(j), priority=bitMaskLength-j+1)


    def p4kpUtilBasedReconfigureForLeafSwitches(self, linkUtilStats, oldLinkUtilStats):
        # logger.info("CLB ALGORITHM: For switch "+ self.p4dev.devName+ "new Utilization data is  "+str(linkUtilStats))
        # logger.info("CLB ALGORITHM: For switch "+ self.p4dev.devName+ "old Utilization data is  "+str(oldLinkUtilStats))

        for i in range (0, ConfConst.MAX_TOR_SUBNET):
            index = i* ConfConst.MAX_PORTS_IN_SWITCH
            pathUtilList = []
            for j in range (int(ConfConst.MAX_PORTS_IN_SWITCH/2), int(ConfConst.MAX_PORTS_IN_SWITCH)):
                port = index + j

                utilInLastInterval = linkUtilStats[port] -  oldLinkUtilStats[port]
                pathUtilList.append((j+1,utilInLastInterval))
            pathUtilList.sort(key=lambda x:x[1])
            rankInsertedIncurrentIteration = {}
            logger.info("Device "+str(self.p4dev.devName)+" Util data is "+str(pathUtilList))
            j=0
            rankArray= [2,2,1,0]
            while j< len(pathUtilList):
                port = pathUtilList[j][0]
                rank = rankArray[j]
                # if(rankInsertedIncurrentIteration.get(rank)== None):
                dltPkt = self.torIdToKpathManagerMap.get(i).deletePort(port,i)
                self.p4dev.send_already_built_control_packet_for_top_k_path(dltPkt )
                rankInsertedIncurrentIteration[rank] = rank
                logger.info("INserting rank "+str(rank)+" and port "+str(port))
                insertPkt = self.torIdToKpathManagerMap.get(i).insertPort(port, rank, i )
                self.p4dev.send_already_built_control_packet_for_top_k_path(insertPkt)
                j=j+1






    def processFeedbackPacket(self, parsedPkt, dev):
        #print("Called the algo")
        #TODO: for each of the different types of the packet, we have to write a separate function to process them
        pass


    def setup(self,nameToSwitchMap): #This one initially setup three path in same rank
        '''
        This function setup all the relevant stuffs for running the algorithm
        '''
        startingRankForTestingTopKPathProblem = 0
        self.initMAT(self.p4dev, ConfConst.K)
        if self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.LEAF:
            for i  in range (0, ConfConst.MAX_TOR_SUBNET):
                j=0
                for k in self.p4dev.portToSpineSwitchMap.keys():
                    pkt = self.torIdToKpathManagerMap.get(i).insertPort(port = int(k), k = startingRankForTestingTopKPathProblem+j, torId= i)
                    self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
                    j=j+1
        # elif self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.SPINE:
        #     for k in self.p4dev.portToSuperSpineSwitchMap.keys():
        #         pkt = self.topKPathManager.insertPort(port = int(k), k = startingRankForTestingTopKPathProblem)
        #         self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        # elif self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.SUPER_SPINE:
        #     self.topKPathManager = TopKPathManager(dev = self.p4dev, k=ConfConst.K) # by default add space for 16 ports in super spine. This is not actually used in our simulation
        #     pass

        return





class BinaryMask:
    def __init__(self, length):
        self.bits=[]
        self.length = length
        for i in range(0,self.length):
            self.bits.append(0)

    def setNthBitWithB(self,n,b):
        self.bits[(len(self.bits) - 1 )-n] = b
    def setAllBitOne(self):
        for i in range(0,self.length):
            self.bits[i]  = 1

    def setAllBitMinuxOneEqualX(self):
        for i in range(0,self.length):
            self.bits[i]  = -1

    def getBinaryString(self):
        val = "0b"
        for i in range(0, self.length):
            if(self.bits[i] == 0):
                val = val + "0"
            elif (self.bits[i] == 1):
                val = val + "1"
            else:
                val = val + "X"
        return  val


def modifyBit(n, position, b):
    '''
    # Python3 program to modify a bit at position
    # p in n to b.

    # Returns modified n.
        :param n:
        :param position:
        :param b:
        :return:
    '''
    mask = 1 << position
    return (n & ~mask) | ((b << position) & mask)

def setPortQueueRatesAndDepth(dev, port, queueRate, bufferSize):
    cmdString = ""
    cmdString = cmdString+  "set_queue_rate "+str(queueRate)+ " "+str(port)+"\n"
    dev.executeCommand(cmdString)
    cmdString = ""
    cmdString = cmdString+  "set_queue_depth "+str(bufferSize)+ " "+str(port)+"\n"
    dev.executeCommand(cmdString)
    # logger.info("Executing queuerate and depth setup commmand for device "+ str(dev))
    # logger.info("command is: "+cmdString)
    #dev.executeCommand(cmdString)