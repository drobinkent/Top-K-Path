import logging
import logging.handlers
import bitarray as ba
import ConfigConst as ConfConst
logger = logging.getLogger('TopKPathManager')
logger.handlers = []
hdlr = logging.handlers.RotatingFileHandler(ConfConst.CONTROLLER_LOG_FILE_PATH, maxBytes = ConfConst.MAX_LOG_FILE_SIZE , backupCount= ConfConst.MAX_LOG_FILE_BACKUP_COUNT)
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

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

class TopKPathManager:
    '''
    In out system 0 means empty. k=0 means this is not a valid path
    We do this to reduce an extra checking in data plane. Because in data plane if-else is costly then memory
    so we decided to start the start the index from 0.
    in the actual storage where paths are stored we use (K+1)^2
    '''

    def __init__(self, dev, k):
        self.p4dev = dev
        self.k = k
        self.portToRankMap = {}
        self.rankToCounterMap = {} #init needed
        self.rankToPortAtMaxIndexMap = {} #init needed
        self.portToIndexAtCurrentRankMap = {}
        self.bitamsk = ba.bitarray(self.k)
        self.rankToPort2dMap = {} # we technically do not need this in CP. But still keeping it
        for i in range(0, self.k+1):
            self.rankToCounterMap[i] = 0 #index k+1 because in our system 0'th rank is invalid for us. Our rank starts form 1. but we keep 0'th entry to maintain when there is no port ina group. and
            #go upto k+1. range (k+1) actualyy goes upto k
            self.rankToPortAtMaxIndexMap[i+1] = 0 #same as previous
            portList = []
            for j in range(0, self.k+1):
                portList.append(0)
            self.rankToPort2dMap[i] = portList
        pass

    def insertPort(self, port, k):
        '''
        This function inserts the port at K'th rank
        :param port:
        :param k:
        :return:
        '''
        oldRank = self.portToRankMap[port]
        if((oldRank != None) and (oldRank!=k)):
            logger.info("Old rank of port "+str(port)+" is: "+str(oldRank)+" and new rank is: "+str(k))
            logger.info("This can not happen. Please Debug. Exiting the thread!!!!")
            exit(1)
        self.portToRankMap[port] = k
        self.rankToCounterMap[k] = self.rankToCounterMap[k] + 1
        self.rankToPortAtMaxIndexMap[k] = port
        oldIndex = self.portToIndexAtCurrentRankMap[port]
        if((oldIndex != None) and (oldIndex!=self.rankToCounterMap[k])):
            logger.info("Old index of port "+str(port)+" is: "+str(oldIndex)+" and new index is: "+str(self.rankToCounterMap[k]))
            logger.info("This can not happen. Please Debug. Exiting the thread!!!!")
            exit(1)
        self.portToIndexAtCurrentRankMap[port] = self.rankToPortAtMaxIndexMap[k]
        self.rankToPort2dMap[k][self.rankToCounterMap[k]] = port
        #next we need to build the control message
        pass

    def deletePort(self, port):
        '''
        This function deletes port from the CP data strucutre and  builds a control message to delete the port from data plane
        At any point of execution if it finds any inconsistency, it exits the thread at control plnae to keep consistency intact
        :param port:
        :return:
        '''

        oldRank = self.portToRankMap[port]
        if(oldRank == None):
            logger.info("Old rank of port to be deleted("+str(port)+") is None. If you are deleting a port before inserting it then you are ok. otherwise There is some bug.")
            logger.info("To ensure sonsistency we are exiting.")
            exit(1)
        self.portToRankMap[port] = 0
        self.rankToCounterMap[oldRank] = self.rankToCounterMap[oldRank] - 1
        portAtMaxIndex = self.rankToPortAtMaxIndexMap[oldRank]
        oldIndex = self.portToIndexAtCurrentRankMap[port]
        if((oldIndex == None) ):
            logger.info("Old index of port "+str(port)+" to be deleted is None. This means the port is already not existing ")
            logger.info("This can not happen. Please Debug. Exiting the thread!!!!")
            exit(1)
        self.portToIndexAtCurrentRankMap[port] = 0
        self.rankToPort2dMap[oldRank][oldIndex] = portAtMaxIndex
        self.portToIndexAtCurrentRankMap[portAtMaxIndex] = oldIndex  #This is necessary because we are shifting it's location
        #next we need to build the control message
        pass

