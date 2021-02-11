import logging
import logging.handlers
from DistributedAlgorithms.TopKPathManager import  TopKPathManager
import ConfigConst as ConfConst
from P4Runtime.P4DeviceManager import SwitchType

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
        if self.p4dev.fabric_device_config.switch_type == SwitchType.LEAF:
            self.topKPathManager = TopKPathManager(dev = self.p4dev, k=len(self.p4dev.portToSpineSwitchMap.keys()))
        elif self.p4dev.fabric_device_config.switch_type == SwitchType.SPINE:
            self.topKPathManager = TopKPathManager(dev = self.p4dev, k=len(self.p4dev.portToSuperSpineSwitchMap.keys()))
        elif self.fabric_device_config.switch_type == SwitchType.SUPER_SPINE:
            self.topKPathManager = TopKPathManager(dev = self.p4dev, k=16) # by default add space for 16 ports in super spine. This is not actually used in our simulation
            pass
        return

        pass

    def setup(self):
        '''
        This function setup all the relevant stuffs for running the algorithm
        '''

        # if self.p4dev.fabric_device_config.switch_type == jp.SwitchType.LEAF:
        #     leafUtils.addUpStreamRoutingGroupForLeafSwitch(self.p4dev, list(self.p4dev.portToSpineSwitchMap.keys())) #this creates a group for upstream routing with  group_id=InternalConfig.LEAF_SWITCH_UPSTREAM_PORTS_GROUP
        #     self.p4dev.addLPMMatchEntryWithGroupAction( tableName = "IngressPipeImpl.upstream_ecmp_routing_control_block.upstream_routing_table", fieldName = "hdr.ipv6.dst_addr",
        #                                           fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
        #                                           actionName="IngressPipeImpl.upstream_ecmp_routing_control_block.set_upstream_egress_port", actionParamName=None, actionParamValue=None,
        #                                           groupID = InternalConfig.LEAF_SWITCH_UPSTREAM_PORTS_GROUP, priority = None)
        #     return
        # elif self.p4dev.fabric_device_config.switch_type == jp.SwitchType.SPINE:
        #     spineUtils.addUpStreamRoutingGroupForSpineSwitch(self.p4dev, list(self.p4dev.portToSuperSpineSwitchMap.keys()))  #this creates a group for upstream routing with  group_id=InternalConfig.SPINE_SWITCH_UPSTREAM_PORTS_GROUP
        #     self.p4dev.addLPMMatchEntryWithGroupAction( tableName = "IngressPipeImpl.upstream_ecmp_routing_control_block.upstream_routing_table", fieldName = "hdr.ipv6.dst_addr",
        #                                           fieldValue= InternalConfig.DCN_CORE_IPv6_PREFIX, prefixLength = InternalConfig.DCN_CORE_IPv6_PREFIX_LENGTH,
        #                                           actionName="IngressPipeImpl.upstream_ecmp_routing_control_block.set_upstream_egress_port", actionParamName=None, actionParamValue=None,
        #                                           groupID = InternalConfig.SPINE_SWITCH_UPSTREAM_PORTS_GROUP, priority = None)
        #     pass
        # elif self.p4dev.fabric_device_config.switch_type == jp.SwitchType.SUPER_SPINE:
        #     pass
        #self.p4dev.setupECMPUpstreamRouting()
        return

    def processFeedbackPacket(self, parsedPkt, dev):
        #print("Called the algo")
        #TODO: for each of the different types of the packet, we have to write a separate function to process them

        pass

