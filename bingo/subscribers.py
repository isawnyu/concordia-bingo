import sys

from repoze.bfg.log import make_stream_logger

logger = make_stream_logger('bingo.debug', sys.stderr)


class BingoSubscriber(object):
    intids = None
    catalog = None
    def _update(self, event):
        self.intids = event.parent['_intids']
        self.catalog = event.parent['_catalog']

class ResourceAdded(BingoSubscriber):
    def __call__(self, ob, event):
        self._update(event)
        logger.debug("added resource (%s, %s)", ob, event)

class ResourceRemoved(BingoSubscriber):
    def __call__(self, ob, event):
        self._update(event)
        logger.debug("removed resource (%s, %s)", ob, event)

class RelationAdded(BingoSubscriber):
    def __call__(self, ob, event):
        import pdb; pdb.set_trace()
        self._update(event)
        i = self.intids.register(ob)
        self.catalog.index(i)
        logger.debug("registered resource (%s, %s)", ob, event)
        
class RelationRemoved(BingoSubscriber):
    def __call__(self, ob, event):
        self._update(event)
        logger.debug("removed resource (%s, %s)", ob, event)
        
resource_added = ResourceAdded()
resource_removed = ResourceRemoved()
    
relation_added = RelationAdded()
relation_removed = RelationRemoved()
