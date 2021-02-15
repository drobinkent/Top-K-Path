import logging.handlers
import logging.handlers
import sys
import threading
import time
import DistributedAlgorithms.Testingconst as tstConst
import ConfigConst as ConfConst
import InternalConfig
from DistributedAlgorithms.RoutingInfo import RoutingInfo
import P4Runtime.leafSwitchUtils as leafUtils
import P4Runtime.spineSwitchUtils as spineUtils
import P4Runtime.superSpineSwitchUtils as superSpineUtils
import P4Runtime.SwitchUtils as swUtils
import P4Runtime.packetUtils as pktUtil
from TestCaseDeployer import TestCommandDeployer
import ConfigConst as confConst

logger = logging.getLogger('Shell')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

class ECMPRouting:

    def __init__(self, dev):
        self.p4dev = dev
        self.delayBasedRoutingInfo = RoutingInfo(name = "Delay Based Routing Info Store")
        self.egressQueueDepthBasedRoutingInfo = RoutingInfo(name = "Egress queue Depth Based Routing Info Store")
        pass

    def setup(self):
        '''
        This function setup all the relevant stuffs for running the algorithm
        '''


        self.p4dev.setupECMPUpstreamRouting()
        self.x = threading.Thread(target=self.topKpathroutingTesting, args=())
        self.x.start()
        logger.info("ECMP-VS-TopKpathroutingTesting thread started( This Thread is ECMP)")
        return

    def processFeedbackPacket(self, parsedPkt, dev):
        #print("Called the algo")
        #TODO: for each of the different types of the packet, we have to write a separate function to process them

        pass

    def topKpathroutingTesting(self):
        time.sleep(25)
        topologyConfigFilePath =  confConst.TOPOLOGY_CONFIG_FILE
        if(self.p4dev.devName == "device:p0l0"):
            testEvaluator = TestCommandDeployer(topologyConfigFilePath,
                            "/home/deba/Desktop/Top-K-Path/testAndMeasurement/TestConfigs/ECMP/l2strideSmallLarge-highRationForLargeFlows.json",
                            confConst.IPERF3_CLIENT_PORT_START, confConst.IPERF3_SERVER_PORT_START, testStartDelay= 20)
            testEvaluator.setupTestCase()
        i = 0
        while(True):
            j = i % len(tstConst.PORT_RATE_CONFIGS)
            if(self.p4dev.devName != "device:p0l0"):
                time.sleep(tstConst.RECONFIGURATION_GAP)
                return
            portCfg = tstConst.PORT_RATE_CONFIGS[j]
            for k in range(0,len(portCfg)): # k gives the rank iteslf as the port configs are already sorted
                if self.p4dev.fabric_device_config.switch_type == InternalConfig.SwitchType.LEAF:
                    port =portCfg[k][0]
                    portRate = int(self.p4dev.queueRateForSpineFacingPortsOfLeafSwitch * portCfg[k][1])
                    bufferSize = int(portRate * ConfConst.QUEUE_RATE_TO_QUEUE_DEPTH_FACTOR)
                    setPortQueueRatesAndDepth(self.p4dev, port, portRate, bufferSize)
                if self.p4dev.fabric_device_config.switch_type == InternalConfig.SwitchType.SPINE:
                    port =portCfg[k][0]
                    portRate = int(self.p4dev.queueRateForSuperSpineSwitchFacingPortsOfSpineSwitch * portCfg[k][1])
                    bufferSize = int(portRate * ConfConst.QUEUE_RATE_TO_QUEUE_DEPTH_FACTOR)
                    setPortQueueRatesAndDepth(self.p4dev, port, portRate, bufferSize)

            i = i+ 1
            time.sleep(tstConst.RECONFIGURATION_GAP)


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