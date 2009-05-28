# -*- coding: utf-8 -*-

import sys

import BTrees
from persistent import Persistent
from persistent.mapping import PersistentMapping
from repoze.bfg.log import make_stream_logger
import repoze.catalog.catalog
from repoze.catalog.indexes.text import CatalogTextIndex
from repoze.folder import Folder
import transaction
import zc.relation.catalog
from ZODB.interfaces import IConnection
from zope.interface import Attribute, Interface, implements
from zope.intid import IntIds
from zope.keyreference.interfaces import IKeyReference
from zope.keyreference.persistent import connectionOfPersistent


logger = make_stream_logger('ZODB.FileStorage', sys.stderr)


class Error(Exception):
    pass
    

class BingoError(Error):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg
    

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
    
    def addRelation(self, name, subj, predicate, obj):
        # Add relation between already added resources
        if name in self:
            raise BingoError, "Can not replace existing Bingo relation"
        if self.intids.queryId(subj) is None:
            raise BingoError, "Relation subject has no uid"
        if self.intids.queryId(obj) is None:
            raise BingoError, "Relation object has no uid"
        savepoint = transaction.savepoint()
        try:
            relation = Relation((subj,), predicate, (obj,))
            self[name] = relation
            savepoint = transaction.savepoint()
            uid = self.intids.register(relation)
            self.relation_catalog.index_doc(uid, relation)
        except:
            savepoint.rollback()
            raise
        transaction.commit()
        return (name, uid)
        
    def addResource(self, name, resource):
        # Safely overwrites placeholders, registers, and catalogs
        if name in self:
            current = self[name]
            if IResource.providedBy(current):
                raise BingoError, "Can not replace existing Bingo item"
            else:
                # Step in for placeholder, keeping existing intid
                savepoint = transaction.savepoint()
                try:
                    uid = self.intids.getId(current)
                    del self[name]
                    self[name] = resource
                    key = IKeyReference(resource)
                    self.intids.refs[uid] = key
                    self.intids.ids[key] = uid
                    if IResource.providedBy(resource):
                        self.metadata_catalog.index_doc(uid, resource)
                except:
                    savepoint.rollback()
                    raise
                transaction.commit()
                return (name, uid)
        else:
            savepoint = transaction.savepoint()
            try:
                self[name] = resource
                uid = self.intids.register(resource)
                if IResource.providedBy(resource):
                    self.metadata_catalog.index_doc(uid, resource)
            except:
                savepoint.rollback()
                raise
            transaction.commit()
            return (name, uid)


def dumpPersistent(obj, catalog, cache):
    intids = catalog.__parent__['_intids']
    return intids.queryId(obj)

def loadPersistent(token, catalog, cache):
    intids = catalog.__parent__['_intids']
    return intids.getObject(token)


class IRelationCatalog(Interface):
    pass


class RelationCatalog(zc.relation.catalog.Catalog):
    implements(IRelationCatalog)


class Connected(Persistent):
    # Allowing key references to be had for unsaved objects
    def __conform__(self, iface):
        if iface is IConnection:
            return connectionOfPersistent(self.__parent__)
    

class Resource(Connected):
    implements(IResource)
    def __init__(self, title, summary=None, url=None, where=None):
        self.title = title
        self.summary = summary or ''
        self.url = url
        self.where = where
    def __str__(self):
        return u'<%s>' % self.title
    @property
    def searchable_text(self):
        return self.title + ' ' + self.summary


class IRelation(IBingoItem):
    subjects = Attribute('subjects')
    predicate = Attribute('predicate')
    objects = Attribute('objects')


class Relation(Connected):
    implements(IRelation)
    def __init__(self, subjects, predicate, objects):
        self.subjects = subjects
        self.predicate = predicate
        self.objects = objects
    def __str__(self):
        return u'<(%s) : %s : (%s)>' % (u', '.join([unicode(r) for r in self.subjects]), self.predicate, ', '.join([unicode(r) for r in self.objects]))


class IPlaceholder(IBingoItem):
    pass
    
    
class Placeholder(Connected):
    implements(IPlaceholder)
    title = u'Untitled placeholder'
    summary = u'Unsummarized placeholder'
    where = None
    def __init__(self, url=None):
        self.url = url
    def __str__(self):
        return u'<%s>' % self.title


# Relation vocabulary
ATTESTATION = 'gawd:attestsTo'
REFERENCE = 'dcterms:references'

# Ἀφροδισίαδος

def appmaker(zodb_root):
    if not 'app_root' in zodb_root:
        import transaction
        app_root = BingoModel()
        zodb_root['app_root'] = app_root
        concordia = app_root[u'concordia'] = BingoContainer('Concordia')
        concordia.__name__ = u'concordia'
        concordia['_intids'] = IntIds()
        catalog = concordia[u'_metadata_catalog'] = MetadataCatalog()
        catalog['text'] = CatalogTextIndex(u'searchable_text')
        catalog = concordia[u'_relation_catalog'] = RelationCatalog(dumpPersistent, loadPersistent, BTrees.family32.IO)
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

        # Add a placeholder to be clobbered
        x = Placeholder(
                url=u'http://insaph.kcl.ac.uk/iaph2007/iAph040202.html'
                )
        concordia.addResource(u'insaph.kcl.ac.uk/iaph2007/iAph040202.html', x)
        
        # Clobber preceeding placeholder
        a = Resource(
                u"4.202. Verse honours: i. for Ampelios, father of the city; ii. and iii. for Doulkitios, governor, on the Agora Gate",
                summary=u"i., ii. and iii are all cut, clearly set out as a group, on the façade, on the highest remaining course of blocks, which was capped above by a moulded course. i. is cut on the northernmost of a series of projecting bastions; ii. is on the next bastion to the south, whose surface is largely lost; three loose fragments were found in 1983. The third bastion shows no sign of any inscription; iii. is cut on the fourth. i. and ii. are on a smooth face, but iii. is cut partly on a rough surface.",
                url=u"http://insaph.kcl.ac.uk/iaph2007/iAph040202.html"
                )
        concordia.addResource(u'insaph.kcl.ac.uk/iaph2007/iAph040202.html', a)
        
        b = Resource(
                u"Aphrodisias",
                summary=u"Attested as \u1f08\u03c6\u03c1\u03bf\u03b4\u03b9\u03c3\u03af\u03b1\u03b4\u03bf\u03c2 during Roman, early Empire (30 BC-AD 300) (confident) and Late Antique (AD 300-AD 640) (confident) periods",
                url=u"http://bacchus.atlantides.org/places/638753/aphrodisias"
                )
        concordia.addResource(
            u'bacchus.atlantides.org/places/638753/aphrodisias', 
            b
            )

        # Relate A and B
        concordia.addRelation(
        u'insaph.kcl.ac.uk/iaph2007/iAph040202.html--%s--bacchus.atlantides.org/places/638753/aphrodisias' % ATTESTATION, 
            a, 
            ATTESTATION, 
            b
            )
        concordia.addRelation(
        u'bacchus.atlantides.org/places/638753/aphrodisias--%s--insaph.kcl.ac.uk/iaph2007/iAph040202.html' % REFERENCE,
            b,
            REFERENCE,
            a
            )
            
        # Relate B to a placeholder
        c = Placeholder(url=u'http://en.wikipedia.org/wiki/Aphrodisias')
        concordia.addResource(u'en.wikipedia.org/wiki/Aphrodisias', c)
        concordia.addRelation(
        'bacchus.atlantides.org/places/638753/aphrodisias--%s--en.wikipedia.org/wiki/Aphrodisias' % 'related',
            b,
            'related',
            c
            )
            
    return zodb_root['app_root']
