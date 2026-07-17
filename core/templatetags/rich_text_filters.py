"""Filtros de template para sanitizar HTML salvo via rich text editor.

Conteudo colado de PDF/Word frequentemente vem dentro de <pre> com <br>
forcado em cada quebra de linha do original — o que destroi o reflow do
texto no site. O filtro abaixo normaliza esse HTML preservando as marcas
estruturais (h1-h6, strong, em, ul, ol, a, etc).
"""
import html as _html
import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def unescape_entities(value):
    """Decodifica entidades HTML (&Ccedil; &ouml; &amp; …) para o caractere real.

    Útil quando o conteúdo salvo veio entity-encoded e é exibido via
    ``textContent``/autoescape (cards, atributos data-*), onde as entidades
    apareceriam literalmente em vez de acentos. NÃO marca como safe — o
    resultado ainda passa pelo autoescape do template.
    """
    if not value:
        return ""
    return _html.unescape(str(value))


@register.filter
def clean_rich_text(value):
    if not value:
        return ""
    html = str(value)
    # Remove <pre> e </pre> (mantem o conteudo) — evita whitespace pre-formatado
    html = re.sub(r"</?pre[^>]*>", "", html, flags=re.IGNORECASE)
    # 2+ <br> consecutivos viram quebra de paragrafo real
    html = re.sub(
        r"(?:<br\s*/?>\s*){2,}", "</p><p>", html, flags=re.IGNORECASE
    )
    # <br> isolado vira espaco (line wrap herdado do source nao deve quebrar)
    html = re.sub(r"<br\s*/?>", " ", html, flags=re.IGNORECASE)
    # &nbsp; vira espaco simples para evitar runs longos sem quebra
    html = html.replace("&nbsp;", " ")
    # Colapsa whitespace multiplo entre tags
    html = re.sub(r"\s{2,}", " ", html)
    # <p> vazio pode aparecer apos as substituicoes
    html = re.sub(r"<p[^>]*>\s*</p>", "", html, flags=re.IGNORECASE)
    return mark_safe(html)
