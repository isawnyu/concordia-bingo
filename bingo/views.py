from xml.etree import ElementTree

from repoze.bfg.interfaces import IRequest
from repoze.bfg.jinja2 import render_template_to_response
from repoze.bfg.url import model_url
from repoze.bfg.view import static
from webob import Response
from zc.relation import RELATION
import zc.relation.catalog


static_view = static('templates/static')
IGETRequest = IRequest({'request_method': 'GET'})
IPOSTRequest = IRequest({'request_method': 'POST'})


def my_view(context, request):
    return render_template_to_response('templates/mytemplate.pt',
                                       request = request,
                                       project = 'Bingo')
                                       
def search_view(context, request):
    results = []
    errormsg = None
    q = request.params.get('q')
    if q:
        md = context.metadata_catalog
        try:
            numdocs, tokens = md.search(text=q)
            resources = sorted((context.intids.getObject(t), t) for t in tokens)
            rc = context.relation_catalog
            for res, token in resources:
                subs = rc.findRelations(
                    dict(subject=token)
                    )
                objs = rc.findRelations(
                    dict(object=token)
                    )
                results.append(
                    dict(resource=res, subjects=subs, objects=objs)
                    )
        except Exception, e:
            errormsg = str(e)
        # endif
    return render_template_to_response('templates/search_form.pt',
                                       title=context.title,
                                       request=request,
                                       results=results or None,
                                       errormsg=errormsg
                                       )

ATOMNS = 'http://www.w3.org/2005/Atom'

def append_item(context, request):
    # Parse Atom entry in request body and add resource, placeholders, and 
    # relations.
    try:
        doc = ElementTree.fromstring(request.body)
        if doc.tag == '{%s}entry' % ATOMNS:
            entry = doc
        else:
            entry = doc.find('{%s}entry' % ATOMNS)
    except Exception, e:
        errormsg = str(e)
        raise
    
    # Required
    title = getattr(entry.find('{%s}title' % ATOMNS), 'text')
    summary = getattr(entry.find('{%s}summary' % ATOMNS), 'text')
    s_url = ([e.attrib['href'] for e in entry.findall('{%s}link' % ATOMNS) if e.attrib['rel'] == 'alternate'] or [None])[0]
    assert not 
    return Response("POST " + str(request.headers) + " " + str(request.body) + "\n")

def append_form(context, request):
    errormsg = None
    url = model_url(context, request)
    return render_template_to_response('templates/append_form.pt',
                                       context=context,
                                       request=request,
                                       context_url=url,
                                       errormsg=errormsg
                                       )
    
