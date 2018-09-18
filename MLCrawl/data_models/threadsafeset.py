'''Folgender Code stammt aus: https://stackoverflow.com/questions/13610654/how-to-make-built-in-containers-sets-dicts-lists-thread-safe
und wurde dort am 29.11.2012 vom User: Francis Avila (https://stackoverflow.com/users/1002469/francis-avila) veröffentlicht.
Er wurde meinerseits nur leicht für Python3 modifiziert.'''
from threading import Lock

def lock_class(methodnames, lockfactory):
    return lambda cls: make_threadsafe(cls, methodnames, lockfactory)

def lock_method(method):
    if getattr(method, '__is_locked', False):
        raise TypeError("Method %r is already locked!" % method)
    def locked_method(self, *arg, **kwarg):
        with self._lock:
            return method(self, *arg, **kwarg)
    locked_method.__name__ = '%s(%s)' % ('lock_method', method.__name__)
    locked_method.__is_locked = True
    return locked_method


def make_threadsafe(cls, methodnames, lockfactory):
    init = cls.__init__
    def newinit(self, *arg, **kwarg):
        init(self, *arg, **kwarg)
        self._lock = lockfactory()
    cls.__init__ = newinit

    for methodname in methodnames:
        oldmethod = getattr(cls, methodname)
        newmethod = lock_method(oldmethod)
        setattr(cls, methodname, newmethod)
    return cls

@lock_class(['add','remove','__contains__','pop','copy'], Lock)
class ThreadSafeSet(set):
    @lock_method # if you double-lock a method, a TypeError is raised
    def frobnify(self):
        pass
