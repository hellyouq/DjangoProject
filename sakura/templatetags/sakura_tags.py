"""Template helpers that resolve to real URLs in both Django mode and the static build.

In static mode the procedural art is pre-rendered into files by `manage.py export_site`,
so the same template produces working <img src> on GitHub Pages.
"""

from django import template
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def art_avatar(context, girl):
    """URL of the girl's procedural portrait."""
    if context.get("static_mode"):
        return static(f"art/avatar/{girl.image_seed}.svg")
    return (
        f"{reverse('art_avatar', args=[girl.image_seed])}"
        f"?accent={escape(girl.accent)}"
    )


@register.simple_tag(takes_context=True)
def art_case(context, case):
    """URL of the case banner."""
    if context.get("static_mode"):
        return static(f"art/case/{case.slug}.svg")
    return (
        f"{reverse('art_case', args=[case.art_key])}"
        f"?a={escape(case.accent)}&b={escape(case.accent2)}&s=21"
    )


@register.simple_tag(takes_context=True)
def art_logo(context):
    if context.get("static_mode"):
        return static("art/logo.svg")
    return reverse("art_logo")


@register.simple_tag
def rarity_color(rarity):
    from sakura.models import RARITY_META

    return mark_safe(RARITY_META[rarity]["color"])
