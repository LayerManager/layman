from oauth2_provider.decorators import protected_resource
from django.http import HttpResponse
import json


@protected_resource(scopes=['read'])
def profile(request):
    return HttpResponse(json.dumps({
        "userId": request.resource_owner.id,
        "screenName": request.resource_owner.username,
        "emailAddress": request.resource_owner.email,
        "firstName": request.resource_owner.first_name,
        "lastName": request.resource_owner.last_name
    }), content_type="application/json")
