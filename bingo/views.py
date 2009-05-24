#from repoze.bfg.chameleon_zpt import render_template_to_response
from repoze.bfg.jinja2 import render_template_to_response
from repoze.bfg.view import static
import zc.relation.catalog

from bingo.models import ATTESTATION

static_view = static('templates/static')

def my_view(context, request):
    return render_template_to_response('templates/mytemplate.pt',
                                       request = request,
                                       project = 'Bingo')
                                       
def search_view(context, request):
    if 'q' in request.params and 'search' in request.params:
        md = context.metadata_catalog
        numdocs, results = md.search(text=request.params['q'])
        resources = sorted(context.intids.getObject(r) for r in results)
        rc = context.relation_catalog
        query = rc.tokenizeQuery
        subjects = rc.findRelations(dict(predicate=ATTESTATION, subject=zc.relation.catalog.any(*results)))
        objects = rc.findRelations(dict(predicate=ATTESTATION, object=zc.relation.catalog.any(*results)))
    else:
        resources = None
        relations = None
    return render_template_to_response('templates/search_view.pt',
                                       title=context.title,
                                       request=request,
                                       resources=resources,
                                       subjects=subjects,
                                       objects=objects
                                       )

