#
# Queues and stuff
#

from Queue import PriorityQueue


mutationQueue = PriorityQueue()
processedQueue = PriorityQueue()


class FileToMutate(object):
    """
    This is a convenient object.
    Example:
    q = Queue.PriorityQueue()
    q.put(FileToMutate(1, 'c:\\tests\\file.123.txt'))
    """
    def __init__(self, priority, filename, id, bitmap):
        self.priority = priority
        self.filename = filename
        self.id = id
        self.bitmap = bitmap

    def __cmp__(self, other):
        return cmp(self.priority, other.priority)


def get_queue_element_by_id(id, q):
    """
    The function name is its own documentation :)
    """
    for e in q.queue:
        if e.id == id:
            return e

    return None
