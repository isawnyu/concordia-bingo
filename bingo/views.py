#from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.interfaces import IRequest
from repoze.bfg.jinja2 import render_template_to_response
from repoze.bfg.view import static
import zc.relation.catalog
from zc.relation import RELATION
from webob import Response

from bingo.models import ATTESTATION

static_view = static('templates/static')

IGETRequest = IRequest({'request_method': 'GET'})
IPOSTRequest = IRequest({'request_method': 'POST'})
    
def my_view(context, request):
    return render_template_to_response('templates/mytemplate.pt',
                                       request = request,
                                       project = 'Bingo')
                                       
def search_view(context, request):
    results = None
    errormsg = None
    if 'q' in request.params:
        md = context.metadata_catalog
        try:
            numdocs, results = md.search(text=request.params['q'])
            resources = sorted(context.intids.getObject(r) for r in results)
            rc = context.relation_catalog
            query = rc.tokenizeQuery
            subjects = rc.findRelations(
                dict(subject=zc.relation.catalog.any(*results))
                )
            objects = rc.findRelations(
                dict(object=zc.relation.catalog.any(*results))
                )
            results = dict(
                        resources=resources, 
                        subjects=subjects, 
                        objects=objects
                        )
        except Exception, e:
            errormsg = str(e)
        # endif
    return render_template_to_response('templates/search_view.pt',
                                       title=context.title,
                                       request=request,
                                       results=results,
                                       errormsg=errormsg
                                       )

def append_view(context, request):
    return Response("POST "+request.body+"\n")

