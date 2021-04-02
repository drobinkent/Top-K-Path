import logging.handlers
import threading
import time
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

class TopKPathRouting:

    def __init__(self, dev):
        self.p4dev = dev
        self.testOperationIndex =0
        if self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.LEAF:
            #self.topKPathManager = TopKPathManager(dev = self.p4dev, k=len(self.p4dev.portToSpineSwitchMap.keys()))
            self.topKPathManager = TopKPathManager(dev = self.p4dev, k=16)
        elif self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.SPINE:
            # self.topKPathManager = TopKPathManager(dev = self.p4dev, k=len(self.p4dev.portToSuperSpineSwitchMap.keys()))
            self.topKPathManager = TopKPathManager(dev = self.p4dev, k=16)
        elif self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.SUPER_SPINE:
            self.topKPathManager = TopKPathManager(dev = self.p4dev, k=16) # by default add space for 16 ports in super spine. This is not actually used in our simulation
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
            # switchObject.addTernaryMatchEntry( "IngressPipeImpl.k_path_selector_control_block.best_path_finder_mat",
            #                                    fieldName = "local_metadata.best_path_selector_bitmask",
            #                                    fieldValue = allOneMAskBinaryString, mask = maskAsString,
            #                                    actionName = "IngressPipeImpl.k_path_selector_control_block.best_path_finder_action_with_param",
            #                                    actionParamName = "rank",
            #                                    actionParamValue = str(j), priority=bitMaskLength-j+1)
            switchObject.addTernaryMatchEntry( "IngressPipeImpl.k_path_selector_control_block.kth_path_finder_mat",
                                               fieldName = "local_metadata.kth_path_selector_bitmask",
                                               fieldValue = allOneMAskBinaryString, mask = maskAsString,
                                               actionName = "IngressPipeImpl.k_path_selector_control_block.kth_path_finder_action_with_param",
                                               actionParamName = "rank",
                                               actionParamValue = str(j), priority=bitMaskLength-j+1)
            # switchObject.addTernaryMatchEntry( "IngressPipeImpl.k_path_selector_control_block.worst_path_finder_mat",
            #                                    fieldName = "local_metadata.worst_path_selector_bitmask",
            #                                    fieldValue = allOneMAskBinaryString, mask = maskAsString,
            #                                    actionName = "IngressPipeImpl.k_path_selector_control_block.worst_path_finder_action_with_param",
            #                                    actionParamName = "rank",
            #                                    actionParamValue = str(j), priority=j+1)




    def setup(self):
        '''
        This function setup all the relevant stuffs for running the algorithm
        '''
        startingRankForTestingTopKPathProblem = 0
        #swUtils.setupFlowtypeBasedIngressRateMonitoringForKPathProblem(self.p4dev)
        self.initMAT(self.p4dev, ConfConst.K)
        if self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.LEAF:
            i=0
            for k in self.p4dev.portToSpineSwitchMap.keys():
                pkt = self.topKPathManager.insertPort(port = int(k), k = startingRankForTestingTopKPathProblem)
                self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
                i=i+1
        elif self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.SPINE:
            for k in self.p4dev.portToSuperSpineSwitchMap.keys():
                pkt = self.topKPathManager.insertPort(port = int(k), k = int(k))
                self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        elif self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.SUPER_SPINE:
            self.topKPathManager = TopKPathManager(dev = self.p4dev, k=16) # by default add space for 16 ports in super spine. This is not actually used in our simulation
            pass
        self.x = threading.Thread(target=self.topKpathroutingTesting, args=())
        self.x.start()
        logger.info("TopKpathroutingTesting thread started")
        return

    def processFeedbackPacket(self, parsedPkt, dev):
        #print("Called the algo")
        #TODO: for each of the different types of the packet, we have to write a separate function to process them

        pass



    def topKpathroutingTesting(self):
        time.sleep(25)
        i = 0
        while(True):
            j = i % len(tstConst.TOP_K_PATH_EXPERIMENT_PORT_RATE_CONFIGS)
            if(self.p4dev.devName != "device:p0l0"):
                return
            portCfg = tstConst.TOP_K_PATH_EXPERIMENT_PORT_RATE_CONFIGS[j]
            time.sleep(portCfg[0])
            for k in range(0,len(portCfg[1])): # k gives the rank iteslf as the port configs are already sorted
                if self.p4dev.fabric_device_config.switch_type == InternalConfig.SwitchType.LEAF:
                    port =portCfg[1][k][0]
                    portRank = portCfg[1][k][1]
                    portRate = portCfg[1][k][2]
                    bufferSize = portCfg[1][k][3]
                    setPortQueueRatesAndDepth(self.p4dev, port, portRate, bufferSize)
                if self.p4dev.fabric_device_config.switch_type == InternalConfig.SwitchType.SPINE:
                    port =portCfg[1][k][0]
                    portRank = portCfg[1][k][1]
                    portRate = portCfg[1][k][2]
                    bufferSize = portCfg[1][k][3]
                dltPkt = self.topKPathManager.deletePort(port)
                self.p4dev.send_already_built_control_packet_for_top_k_path(dltPkt)
                if(portRate> 0): # if 0 that means the port is not down . So need to iinsert it. but for rate < 0 we delete the port but do not insert it agian to simulate delete behavior
                    insertPkt = self.topKPathManager.insertPort(port, portRank)
                    self.p4dev.send_already_built_control_packet_for_top_k_path(insertPkt)
                else:
                    logger.info("Port : "+str(port)+" will not be configured into system as it's rate is <0 = ")
            print("Installed routes ",portCfg)
            topologyConfigFilePath =  ConfConst.TOPOLOGY_CONFIG_FILE
            # if(self.p4dev.devName == "device:p0l0"):
            #     testEvaluator = TestCommandDeployer(topologyConfigFilePath,
            #                                         "/home/deba/Desktop/Top-K-Path/testAndMeasurement/TestConfigs/TopKPathTesterWithTopKPath.json",
            #                                         ConfConst.IPERF3_CLIENT_PORT_START, ConfConst.IPERF3_SERVER_PORT_START, testStartDelay= 5)
            # testEvaluator.setupTestCase()
            i = i+ 1


            # after reconfiguration start the testcase with 3 special flows





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
    logger.info("Executing queuerate and depth setup commmand for device "+ str(dev))
    logger.info("command is: "+cmdString)
    #dev.executeCommand(cmdString)