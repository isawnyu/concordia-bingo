# -*- coding: utf-8 -*-

import sys

import BTrees
from persistent import Persistent
from persistent.mapping import PersistentMapping
from zope.interface import Attribute, Interface, implements
from zope.intid import IntIds
import repoze.catalog.catalog
from repoze.catalog.indexes.text import CatalogTextIndex
from repoze.folder import Folder
import zc.relation.catalog

from repoze.bfg.log import make_stream_logger

logger = make_stream_logger('ZODB.FileStorage', sys.stderr)


class IModel(Interface):
    pass


class BingoModel(PersistentMapping):
    implements(IModel)
    __parent__ = __name__ = None
    

class IMetadataCatalog(Interface):
    pass
    

class MetadataCatalog(repoze.catalog.catalog.Catalog):
    implements(IMetadataCatalog)
    

class IBingoContainer(Interface):
    pass


class IBingoItem(Interface):
    pass


class IResource(IBingoItem):
    pass

class BingoContainer(Folder):
    implements(IBingoContainer)
    
    def __init__(self, title):
        super(BingoContainer, self).__init__()
        self.title = title
        
    @property
    def intids(self):
        return self.get('_intids')
    
    @property
    def relation_catalog(self):
        return self.get('_relation_catalog')
    
    @property
    def metadata_catalog(self):
        return self.get('_metadata_catalog')
    
    def add(self, name, obj):
        # Registers and catalogs
        import transaction
        self[name] = obj
        transaction.commit()
        i = self.intids.register(obj)
        self.relation_catalog.index_doc(i, obj)
        if IResource.providedBy(obj):
            self.metadata_catalog.index_doc(i, obj)
        transaction.commit()


class IRelationCatalog(Interface):
    pass
    

class RelationCatalog(zc.relation.catalog.Catalog):
    implements(IRelationCatalog)


class Resource(Persistent):
    implements(IResource)
    def __init__(self, title):
        self.title = title
    def __str__(self):
        return u'<%s>' % self.title
    @property
    def searchable_text(self):
        return self.title
        
class IRelation(IBingoItem):
    subjects = Attribute('subjects')
    predicate = Attribute('predicate')
    objects = Attribute('objects')


class Relation(Persistent):
    implements(IRelation)
    def __init__(self, subjects, predicate, objects):
        self.subjects = subjects
        self.predicate = predicate
        self.objects = objects
    def __str__(self):
        return u'<(%s) : %s : (%s)>' % (u', '.join([unicode(r) for r in self.subjects]), self.predicate, ', '.join([unicode(r) for r in self.objects]))

def dumpPersistent(obj, catalog, cache):
    intids = catalog.__parent__['_intids']
    return intids.queryId(obj)

def loadPersistent(token, catalog, cache):
    intids = catalog.__parent__['_intids']
    return intids.getObject(token)
    

# Relation vocabulary
ATTESTATION = 'gawd:attestsTo'

# Ἀφροδισιάς

def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        import transaction
        app_root = BingoModel()
        zodb_root['app_root'] = app_root
        concordia = app_root['concordia'] = BingoContainer('Concordia')
        concordia['_intids'] = IntIds()
        catalog = concordia['_metadata_catalog'] = MetadataCatalog()
        catalog['text'] = CatalogTextIndex('searchable_text')
        catalog = concordia['_relation_catalog'] = RelationCatalog(dumpPersistent, loadPersistent, BTrees.family32.IO)
        catalog.addValueIndex(
            IRelation['subjects'], dumpPersistent, loadPersistent,
            multiple=True, name='subject'
            )
        catalog.addValueIndex(
            IRelation['objects'], dumpPersistent, loadPersistent,
            multiple=True, name='object'
            )
        catalog.addValueIndex(
            IRelation['predicate'], btree=BTrees.family32.OO
            )
        transaction.commit()
        a = Resource('A Resource')
        concordia.add('a', a)
        b = Resource(u'\u1f08\u03c6\u03c1\u03bf\u03b4\u03b9\u03c3\u03b9\u1f71\u03c2')
        concordia.add('b', b)
        r1 = Relation((a,), ATTESTATION, (b,))
        concordia.add('r1', r1)
        
    return zodb_root['app_root']
