"""Helpers para preservar parametros de query string em links de filtro."""
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Retorna a query string atual com os pares chave=valor sobrescritos.

    Use: {% url_replace category='egipto' %} -> "?q=...&category=egipto&..."
    Passar valor vazio remove a chave.
    """
    request = context.get('request')
    if request is None:
        return ''
    params = request.GET.copy()
    for key, value in kwargs.items():
        if value == '' or value is None:
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f'?{encoded}' if encoded else ''
