from repoze.bfg.interfaces import IRequest
from repoze.bfg.jinja2 import render_template_to_response
from repoze.bfg.url import model_url
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

def append_item(context, request):
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
    
