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
        self.maxRank = k
        self.portToRankMap = {}
        self.rankToCounterMap = {} #init needed
        self.rankToPortAtMaxIndexMap = {} #init needed
        self.portToIndexAtCurrentRankMap = {}
        self.bitamsk = ba.bitarray(self.maxRank)
        self.rankToPort2dMap = {}
        for i in range(0, self.maxRank):
            self.rankToCounterMap[i] = ConfConst.INVALID
            self.rankToPortAtMaxIndexMap[i] = ConfConst.INVALID
            portList = []
            for j in range(0, self.maxRank):
                portList.append(0)
            self.rankToPort2dMap[i] = portList
        pass

    def printDS(self):
        print("portToRankMap is :",self.portToRankMap)
        print("rankToCounterMap is ", self.rankToCounterMap)
        print("rankToPortAtMaxIndexMap is :",self.rankToPortAtMaxIndexMap)
        print("portToIndexAtCurrentRankMap is ",self.portToIndexAtCurrentRankMap)
        print("rankToPort2dMap is ")
        for i in range (0, self.maxRank):
            print(self.rankToPort2dMap[i])
        pass

    def insertPort(self, port, k):
        '''
        This function inserts the port at K'th rank
        :param port:
        :param k:
        :return:
        '''
        if(k>self.maxRank):
            logger.error("given  rank is more than the system's available rank. so can't insert the port")
            return False
        if(self.rankToCounterMap[k] >= self.maxRank):
            print("Already k memebers in the group. Yoo may enter the port into next group")
            return False
        oldRank = self.portToRankMap.get(port)
        if((oldRank != None) and (oldRank > ConfConst.INVALID) and  (oldRank != k)):
            logger.info("Old rank of port "+str(port)+" is: "+str(oldRank)+" and new rank is: "+str(k))
            logger.info("This can not happen. Please Debug. Exiting the thread!!!!")
            exit(1)
        if((oldRank != None) and (oldRank > ConfConst.INVALID) and  (oldRank==k)):
            logger.info("The port is already in rank-"+str(k))
            print("The port is already in rank-",k)
            return True
        self.portToRankMap[port] = k
        self.rankToCounterMap[k] = self.rankToCounterMap[k] + 1
        self.rankToPortAtMaxIndexMap[k] = port
        oldIndex = self.portToIndexAtCurrentRankMap.get(port)
        if((oldIndex != None) and (oldIndex >0) and (oldIndex!=self.rankToCounterMap[k])):
            logger.info("Old index of port "+str(port)+" is: "+str(oldIndex)+" and new index is: "+str(self.rankToCounterMap[k]))
            logger.info("This can not happen. Please Debug. Exiting the thread!!!!")
            exit(1)
        self.portToIndexAtCurrentRankMap[port] = self.rankToCounterMap[k]
        self.rankToPort2dMap[k][self.rankToCounterMap[k]] = port
        #next we need to build the control message
        return True

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
            logger.info("To ensure consistency we are exiting.")
            exit(1)
        oldIndex = self.portToIndexAtCurrentRankMap[port]
        if((oldIndex == None) ):
            logger.info("Old index of port "+str(port)+" to be deleted is None. This means the port is already not existing ")
            logger.info("This can not happen. Please Debug. Exiting the thread!!!!")
            exit(1)
        self.portToRankMap[port] = ConfConst.INVALID
        self.rankToCounterMap[oldRank] = self.rankToCounterMap[oldRank] - 1
        portAtMaxIndex = self.rankToPortAtMaxIndexMap.get(oldRank)
        newMaxIndexOfTheRank = self.portToIndexAtCurrentRankMap.get(portAtMaxIndex)-1
        self.portToIndexAtCurrentRankMap[port] = ConfConst.INVALID
        self.rankToPort2dMap[oldRank][oldIndex] = portAtMaxIndex
        #TODO special case when we delete a port from a group. the port itself was the last port in the group. Need s[ecial test for that
        if(port == self.rankToPortAtMaxIndexMap[oldRank]):
            self.portToRankMap[port] = ConfConst.INVALID
            self.portToIndexAtCurrentRankMap[portAtMaxIndex] = ConfConst.INVALID #this case means we are deleting the last port of the group
        else:
            self.portToIndexAtCurrentRankMap[portAtMaxIndex] = oldIndex  #This is necessary because we are shifting it's location
        self.rankToPortAtMaxIndexMap[oldRank] = self.rankToPort2dMap[oldRank][newMaxIndexOfTheRank]
        #next we need to build the control message

        pass


def testDriverFunction():
    mgr = TopKPathManager(dev = None, k=8)
    mgr.insertPort(port = 4, k =1)
    mgr.printDS()
    mgr.insertPort(port = 5, k =1)
    mgr.insertPort(port = 6, k =1)
    mgr.printDS()
    mgr.deletePort(port = 5)
    mgr.insertPort(port = 7, k =1)
    mgr.insertPort(port = 8, k =1)
    mgr.insertPort(port = 9, k =1)
    mgr.insertPort(port = 10, k =1)
    mgr.insertPort(port = 11, k =1)
    mgr.insertPort(port = 12, k =1)
    mgr.insertPort(port = 13, k =2)
    mgr.deletePort(port = 7)
    mgr.insertPort(port = 14, k =7)
    mgr.deletePort(port = 12)
    mgr.deletePort(port = 13)
    mgr.insertPort(port = 23, k =2)
    mgr.insertPort(port = 13, k =2)
    mgr.deletePort(port = 8)
    mgr.deletePort(port = 4)
    mgr.insertPort(port=4, k = 5)
    mgr.insertPort(port=4, k = 5)
    mgr.printDS()

testDriverFunction()