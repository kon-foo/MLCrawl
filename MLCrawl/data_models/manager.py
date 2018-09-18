from multiprocessing.managers import BaseManager

from .threadsafeset import ThreadSafeSet
from .uniquepriorityqueue import UniquePriorityQueue


class OwnManager(BaseManager):
    pass
OwnManager.register('PriorityQueue', UniquePriorityQueue)
OwnManager.register('ThreadSafeSet', ThreadSafeSet, exposed = {'__contains__', 'add', '__len__', '__iter__'})
# DataManager.start()
DataManager = OwnManager()
