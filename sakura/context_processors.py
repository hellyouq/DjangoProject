"""Template context available to every page."""


def sakura_flags(request):
    """`static_mode` is on while `manage.py export_site` renders the Pages build.

    Templates use it to swap server-only links (auth, admin) and dynamic art
    endpoints for their static equivalents.
    """
    from django.conf import settings

    return {"static_mode": bool(getattr(settings, "SAKURA_STATIC_EXPORT", False))}
