import logging.handlers
import threading
import time

import ConfigConst as ConfConst
import InternalConfig as intCoonfig
from DistributedAlgorithms.TopKPathManager import TopKPathManager

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

    def setup(self):
        '''
        This function setup all the relevant stuffs for running the algorithm
        '''

        #self.p4dev.setupECMPUpstreamRouting()
        if self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.LEAF:
            for k in self.p4dev.portToSpineSwitchMap.keys():
                pkt = self.topKPathManager.insertPort(port = int(k), k = 0)
                self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        elif self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.SPINE:
            for k in self.p4dev.portToSuperSpineSwitchMap.keys():
                pkt = self.topKPathManager.insertPort(port = int(k), k = int(k))
                self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        elif self.p4dev.fabric_device_config.switch_type == intCoonfig.SwitchType.SUPER_SPINE:
            self.topKPathManager = TopKPathManager(dev = self.p4dev, k=16) # by default add space for 16 ports in super spine. This is not actually used in our simulation
            pass
        # self.x = threading.Thread(target=self.topKpathroutingTesting, args=())
        # self.x.start()
        # logger.info("TopKpathroutingTesting thread started")
        return

    def processFeedbackPacket(self, parsedPkt, dev):
        #print("Called the algo")
        #TODO: for each of the different types of the packet, we have to write a separate function to process them

        pass

    def testPerRankMaxPortCapacity(self):
        for i in range(1, 25):
            pkt = self.topKPathManager.insertPort(port = int(i), k = 10)
            self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        for i in range(50, 75):
            pkt = self.topKPathManager.insertPort(port = int(i), k = 0)
            self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)

    def topKpathroutingTesting(self):
        time.sleep(40)
        while(True):
            self.testPerRankMaxPortCapacity()
            time.sleep(10)
            pkt = self.topKPathManager.deletePort(5)
            self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
            pkt = self.topKPathManager.deletePort(20)
            self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
            self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        # while(True):
        #     self.testOperationIndex = self.testOperationIndex + 1
        #     if(self.testOperationIndex == 1):
        #         pkt = self.topKPathManager.deletePort(5)
        #         self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        #         pkt = self.topKPathManager.insertPort(port = 5, k = 12)
        #         self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        #         pkt = self.topKPathManager.insertPort(port = 5, k = 11)
        #         self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        #         pkt = self.topKPathManager.insertPort(port = 12, k = 12)
        #         self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        #         pkt = self.topKPathManager.insertPort(port = 9, k = 2)
        #         self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        #         pkt = self.topKPathManager.deletePort(port=6)
        #         self.p4dev.send_already_built_control_packet_for_top_k_path(pkt)
        #         time.sleep(10)

