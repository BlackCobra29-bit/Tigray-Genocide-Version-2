import json
import re
from urllib.parse import urlencode, urlparse, urlunparse

from django import template
from django.templatetags.static import static
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

from App import seo_config

register = template.Library()

DEFAULT_IMAGE_SUFFIXES = ('default.png', 'default_female.jpg')


def _clean_text(value, max_length=None):
    text = strip_tags(str(value or ''))
    text = re.sub(r'\s+', ' ', text).strip()
    if max_length and len(text) > max_length:
        trimmed = text[:max_length].rsplit(' ', 1)[0]
        text = f'{trimmed.rstrip(".,;:")}…'
    return text


def _build_document_title(page_title):
    page_title = (page_title or '').strip()
    if not page_title or page_title == seo_config.SITE_NAME:
        return seo_config.SITE_NAME
    return f'{page_title} | {seo_config.SITE_NAME}'


def _absolute_uri(request, url):
    if not url:
        return ''
    if url.startswith(('http://', 'https://')):
        return url
    return request.build_absolute_uri(url)


def _absolute_static(request, static_path):
    return _absolute_uri(request, static(static_path))


def _absolute_media(request, file_field):
    if not file_field:
        return ''
    try:
        return _absolute_uri(request, file_field.url)
    except (ValueError, AttributeError):
        return ''


def _is_default_media(file_field):
    if not file_field:
        return True
    try:
        name = file_field.name or ''
    except (ValueError, AttributeError):
        return True
    return any(name.endswith(suffix) for suffix in DEFAULT_IMAGE_SUFFIXES)


def _canonical_url(request, canonical_url=None, keep_page=False):
    if canonical_url:
        return _absolute_uri(request, canonical_url)

    parsed = urlparse(request.build_absolute_uri())
    query = {}
    if keep_page:
        page = request.GET.get('page')
        if page and page != '1':
            query['page'] = page
    return urlunparse(parsed._replace(query=urlencode(query), fragment=''))


def _render_json_ld(data):
    if not data:
        return ''
    payload = json.dumps(data, ensure_ascii=False)
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')


def _organization_schema(request):
    return {
        '@type': 'Organization',
        'name': seo_config.SITE_NAME,
        'url': _absolute_uri(request, '/'),
        'logo': _absolute_static(request, seo_config.SITE_LOGO_STATIC),
    }


def _build_json_ld(request, schema_type=None, item=None, page_title=None, description=None):
    if schema_type == 'website':
        return {
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            'name': seo_config.SITE_NAME,
            'url': _absolute_uri(request, '/'),
            'description': description or seo_config.SITE_DEFAULT_DESCRIPTION,
            'publisher': _organization_schema(request),
        }

    if schema_type == 'webpage':
        data = {
            '@context': 'https://schema.org',
            '@type': 'WebPage',
            'name': page_title or seo_config.SITE_NAME,
            'url': _canonical_url(request),
            'description': description or seo_config.SITE_DEFAULT_DESCRIPTION,
            'isPartOf': {
                '@type': 'WebSite',
                'name': seo_config.SITE_NAME,
                'url': _absolute_uri(request, '/'),
            },
        }
        return data

    if schema_type == 'article' and item is not None:
        data = {
            '@context': 'https://schema.org',
            '@type': 'Article',
            'headline': _clean_text(item.title),
            'url': _canonical_url(request),
            'datePublished': item.date_created.isoformat(),
            'publisher': _organization_schema(request),
        }
        description_text = _clean_text(getattr(item, 'content', ''), max_length=300)
        if description_text:
            data['description'] = description_text
        image_url = _absolute_media(request, getattr(item, 'thumbnail', None))
        if image_url:
            data['image'] = [image_url]
        author = getattr(item, 'author', None)
        if author:
            author_name = f'{author.first_name} {author.last_name}'.strip()
            if author_name:
                data['author'] = {'@type': 'Person', 'name': author_name}
        return data

    if schema_type == 'person' and item is not None:
        data = {
            '@context': 'https://schema.org',
            '@type': 'Person',
            'name': item.full_name,
            'url': _canonical_url(request),
        }
        if getattr(item, 'gender', None):
            data['gender'] = item.gender
        image_url = _absolute_media(request, getattr(item, 'picture', None))
        if image_url and not _is_default_media(item.picture):
            data['image'] = image_url
        return data

    if schema_type == 'video' and item is not None:
        data = {
            '@context': 'https://schema.org',
            '@type': 'VideoObject',
            'name': _clean_text(getattr(item, 'description', '') or page_title),
            'url': _canonical_url(request),
            'uploadDate': item.date_created.isoformat(),
        }
        if getattr(item, 'online_link', None):
            data['contentUrl'] = item.online_link
        if description:
            data['description'] = description
        return data

    if schema_type == 'discussion' and item is not None:
        data = {
            '@context': 'https://schema.org',
            '@type': 'Article',
            'headline': _clean_text(item.webinar_title),
            'url': _canonical_url(request),
            'datePublished': item.date_created.isoformat(),
            'publisher': _organization_schema(request),
        }
        description_text = _clean_text(getattr(item, 'webinar_content', ''), max_length=300)
        if description_text:
            data['description'] = description_text
        author = getattr(item, 'author', None)
        if author:
            author_name = f'{author.first_name} {author.last_name}'.strip()
            if author_name:
                data['author'] = {'@type': 'Person', 'name': author_name}
        if getattr(item, 'webinar_video_url', None):
            data['video'] = {
                '@type': 'VideoObject',
                'contentUrl': item.webinar_video_url,
            }
        return data

    return None


@register.filter
def seo_plaintext(value, max_length=160):
    return _clean_text(value, max_length=int(max_length) if max_length else None)


@register.simple_tag
def seo_document_title(page_title=''):
    return _build_document_title(page_title)


@register.inclusion_tag('public_partials/seo_meta.html', takes_context=True)
def seo_meta(
    context,
    page_title=None,
    description=None,
    canonical_url=None,
    image=None,
    og_type='website',
    robots='index, follow',
    keywords=None,
    author=None,
    published=None,
    modified=None,
    schema_type=None,
    item=None,
    keep_page=False,
):
    request = context['request']
    document_title = _build_document_title(page_title)
    meta_description = _clean_text(
        description or context.get('SITE_DEFAULT_DESCRIPTION', seo_config.SITE_DEFAULT_DESCRIPTION),
        max_length=160,
    )
    meta_keywords = keywords or context.get(
        'SITE_DEFAULT_KEYWORDS',
        seo_config.SITE_DEFAULT_KEYWORDS,
    )
    og_image = _absolute_uri(
        request,
        image or _absolute_static(
            request,
            context.get('SITE_OG_IMAGE_STATIC', seo_config.SITE_OG_IMAGE_STATIC),
        ),
    )
    canonical = _canonical_url(request, canonical_url=canonical_url, keep_page=keep_page)
    json_ld = _render_json_ld(
        _build_json_ld(
            request,
            schema_type=schema_type,
            item=item,
            page_title=page_title or seo_config.SITE_NAME,
            description=meta_description,
        )
    )

    return {
        'document_title': document_title,
        'meta_description': meta_description,
        'meta_keywords': meta_keywords,
        'canonical_url': canonical,
        'og_title': document_title,
        'og_description': meta_description,
        'og_image': og_image,
        'og_type': og_type,
        'og_url': canonical,
        'robots': robots,
        'author': author,
        'published': published,
        'modified': modified,
        'json_ld': json_ld,
    }
