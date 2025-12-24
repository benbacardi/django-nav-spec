from django.template.response import TemplateResponse


def test_view(request):
    return TemplateResponse(request, "test.html", {})
