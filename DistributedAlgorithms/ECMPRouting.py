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
        j = 0
        if(self.p4dev.devName == "device:p0l0"):
            portCfg = tstConst.TOP_K_PATH_EXPERIMENT_PORT_RATE_CONFIGS[j]
            for k in range(0,len(portCfg[1])): # k gives the rank iteslf as the port configs are already sorted
                if self.p4dev.fabric_device_config.switch_type == InternalConfig.SwitchType.LEAF:
                    port =portCfg[1][k][0]
                    portRank = portCfg[1][k][1]
                    portRate = portCfg[1][k][2]
                    bufferSize = portCfg[1][k][3]
                    if(portRate <= 0): # if 0 that means the port is  down
                        del self.p4dev.portToSpineSwitchMap[port]
                    setPortQueueRatesAndDepth(self.p4dev, port, portRate, bufferSize)
            leafUtils.addUpStreamRoutingGroupForLeafSwitch(self.p4dev, list(
                self.p4dev.portToSpineSwitchMap.keys()))  # this creates a group for upstream routing with  group_id=InternalConfig.LEAF_SWITCH_UPSTREAM_PORTS_GROUP
            self.p4dev.addLPMMatchEntryWithGroupAction(
                tableName="IngressPipeImpl.upstream_ecmp_routing_control_block.upstream_routing_table",
                fieldName="hdr.ipv6.dst_addr",
                fieldValue=InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength=InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
                actionName="IngressPipeImpl.upstream_ecmp_routing_control_block.set_upstream_egress_port",
                actionParamName=None, actionParamValue=None,
                groupID=InternalConfig.LEAF_SWITCH_UPSTREAM_PORTS_GROUP, priority=None)
        else:
            self.p4dev.setupECMPUpstreamRouting()
        # self.x = threading.Thread(target=self.topKpathroutingTesting, args=())
        # self.x.start()
        # logger.info("ECMP-VS-TopKpathroutingTesting thread started( This Thread is ECMP)")
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
                if(portRate<= 0): # if 0 that means the port is  down
                    self.p4dev.setupECMPUpstreamRouting
            print("Installed routes ",portCfg)
            topologyConfigFilePath =  ConfConst.TOPOLOGY_CONFIG_FILE
            if(self.p4dev.devName == "device:p0l0"):
                testEvaluator = TestCommandDeployer(topologyConfigFilePath,
                                                    "/home/deba/Desktop/Top-K-Path/testAndMeasurement/TestConfigs/TopKPathTesterWithECMP.json",
                                                    ConfConst.IPERF3_CLIENT_PORT_START, ConfConst.IPERF3_SERVER_PORT_START, testStartDelay= 5)
            testEvaluator.setupTestCase()
            i = i+ 1


            # after reconfiguration start the testcase with 3 special flows


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