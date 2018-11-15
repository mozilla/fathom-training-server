from django.http import FileResponse
from django.shortcuts import get_object_or_404

from fathom_server.training.models import Webpage


def view_frozen_webpage(request, webpage_id):
    webpage = get_object_or_404(Webpage, id=webpage_id)
    return FileResponse(webpage.frozen_html)
