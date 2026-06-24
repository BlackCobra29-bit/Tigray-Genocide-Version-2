from . import seo_config


def seo_defaults(request):
    return {
        'SITE_NAME': seo_config.SITE_NAME,
        'SITE_DEFAULT_DESCRIPTION': seo_config.SITE_DEFAULT_DESCRIPTION,
        'SITE_DEFAULT_KEYWORDS': seo_config.SITE_DEFAULT_KEYWORDS,
        'SITE_LOGO_STATIC': seo_config.SITE_LOGO_STATIC,
        'SITE_OG_IMAGE_STATIC': seo_config.SITE_OG_IMAGE_STATIC,
    }
