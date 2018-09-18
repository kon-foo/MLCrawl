from queue import PriorityQueue
import heapq

class UniquePriorityQueue(PriorityQueue):

    def _init(self, maxsize):
        PriorityQueue._init(self, maxsize)
        self.values = dict()
        self.size_diff = 0

    def _put(self, item):
        heappush=heapq.heappush
        if item[1] not in self.values:
            self.values[item[1]] = [1,1,True]
            PriorityQueue._put(self, (item,1))
        else:
            validity = self.values[item[1]]
            validity[0] += 1   #Number of the valid entry
            validity[1] += 1   #Total number of entries
            if validity[2]:    #Is this a replace move?
                self.size_diff += 1
            validity[2] = True
            PriorityQueue._put(self, (item,validity[0]))

    def _get(self):
        heappop=heapq.heappop
        while True:
            item,i = PriorityQueue._get(self)
            validity = self.values[item[1]]
            if validity[1] <= 1:
                del self.values[item[1]]
            else:
                validity[1] -= 1    #Reduce the count
            if i == validity[0]:
                validity[2]=False
                return item
            else:
                self.size_diff -= 1

    def _qsize(self,len=len):
        return len(self.queue)-self.size_diff
