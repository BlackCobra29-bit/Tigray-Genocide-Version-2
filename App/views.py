# import libraries to export SQL backup
import subprocess
import os
from django.conf import settings
from django.http import Http404, HttpResponse
from datetime import datetime
from django.db.models import Count, Sum
from django.core.cache import cache
from django.views.decorators.cache import cache_page
# end of block
from django.shortcuts import render, redirect
from .models import Civilian_victims
from .models import Analysis_articles
from .models import Article_comments
from .models import Webinar
from .models import Photo_archive
from .models import Video_archive
from .models import Administrator
from .models import Tigray_woreda
from .models import Hero_images
from .models import Webmail_password_manager
from .models import Unverified_civilian
from django.contrib import messages
from django.views.generic import DeleteView, UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from .forms import Civilian_Victim_Form
from .forms import AnalysisArticleForm
from .forms import Webinar_discussion_Form
from .forms import Photo_Archive_Form
from .forms import Video_Archive_Form
from .forms import Approve_Civilian_Victim_Form
from .forms import Approve_Analysis_Form
from .forms import Administrator_form
from .forms import Unverified_civilian_form
from .forms import LoginCaptchaForm
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.db.models import Q
from django.http import JsonResponse
from colorama import Fore
from django.core.mail import EmailMessage
from django.conf import settings
import folium
import random
import string
import plotly.graph_objs as go
from plotly.offline import plot
import urllib.parse
from django.utils.text import slugify
from django.utils.html import escape
# to purse video url id
from urllib.parse import urlparse, parse_qs

def custom_404_view(request, exception):
    
    return render(request, '404.html', status=404)

@cache_page(300)  # Cache for 5 minutes (300 seconds)
def index(request):

    # select select hero image
    random_hero_image = Hero_images.objects.filter().order_by('?')[:1].get()
    
    # counter data
    
    count_civilian = Civilian_victims.objects.filter(approval=True).count()
    count_articles = Analysis_articles.objects.filter(approval=True, draft=False).count()
    count_panel = Webinar.objects.all().count()
    count_photo = Photo_archive.objects.all().count()
    count_video = Video_archive.objects.all().count()

    # fetch models data
    civilian_victims = Civilian_victims.objects.filter(approval=True).exclude(Q(picture='civilian_victims_pic/default.png') | Q(picture='civilian_victims_pic/default_female.jpg'))[:30]
    analysis_articles = Analysis_articles.objects.filter(approval=True, draft=False)[:9]
    photo_archives = Photo_archive.objects.all()[:12]
    video_archives = Video_archive.objects.all()[:12]

    # Get total unverified civilians ONCE (used in multiple places)
    total_unverified = Unverified_civilian.objects.aggregate(
        total=Sum('number_of_civilian', default=0)
    )['total'] or 0
    total_civilians_sum = count_civilian + total_unverified

    # line chart - Get zone counts in batch instead of looping with individual queries
    zone_list = ['Western Tigray', 'Eastern Tigray', 'Central Tigray', 'North Western Tigray',
                 'Southern Tigray', 'South Eastern Tigray', 'Mekelle Special', 'Other']
    
    # Get all verified counts by zone in one query
    verified_by_zone = dict(
        Civilian_victims.objects
        .filter(approval=True)
        .values('zone')
        .annotate(cnt=Count('id'))
        .values_list('zone', 'cnt')
    )
    
    # Get all unverified counts by zone in one query
    unverified_by_zone = dict(
        Unverified_civilian.objects
        .values('zone')
        .annotate(total=Sum('number_of_civilian', default=0))
        .values_list('zone', 'total')
    )
    
    line_chart_data_points = []
    for zone in zone_list:
        verified = verified_by_zone.get(zone, 0)
        unverified = unverified_by_zone.get(zone, 0) or 0
        line_chart_data_points.append(verified + unverified)

    # line chart percentages - use pre-calculated total instead of recalculating in loop
    line_chart_items_percentage = []
    for item in line_chart_data_points:
        if total_civilians_sum != 0:
            percentage = round((item * 100) / total_civilians_sum, 2)
            line_chart_items_percentage.append(percentage)
        else:
            line_chart_items_percentage.append(0)


    # bar chart
    bar_chart_data_points = [
        Civilian_victims.objects.filter(
            approval=True, age__gt=int(0), age__lt=int(11)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(11), age__lt=int(18)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(18), age__lt=int(33)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(33), age__lt=int(49)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(49), age__lt=int(64)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(64), age__lt=int(80)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(80), age__lt=int(95)).count(),
        Civilian_victims.objects.filter(approval=True, age = None).count()
    ]

    # bar chart percentages - use pre-calculated count_civilian instead of recalculating in loop
    bar_chart_items_percentage = []
    for item in bar_chart_data_points:
        if count_civilian != 0:
            percentage = round((item * 100) / count_civilian, 2)
            bar_chart_items_percentage.append(percentage)
        else:
            bar_chart_items_percentage.append(0)


    # Pie Chart
    

    verified_list = []

    verified_list = []

    verified_legend = []

    pi_chart_data_points = []

    perpetrator_list = ['Died from lack of food', 'Killed by Eritrean forces', 'Died from lack of medicine',

                    'Killed by Ethiopian forces', 'Killed by Ethiopian and Eritrean forces', 'Killed by Amhara militia and Fano']

    

    total_count = Civilian_victims.objects.filter(approval=True).count()

    for item in perpetrator_list:
        
        total_civilian_count = Unverified_civilian.objects.filter(perpetrator=item).aggregate(total_civilian_count=Sum('number_of_civilian'))['total_civilian_count']
        
        
        if total_civilian_count is None:
            total_civilian_count = 0
        
        count_items = (Civilian_victims.objects.filter(approval=True, perpetrator=item).count() + total_civilian_count)

        if count_items > 0:

            total_civilian_count = Unverified_civilian.objects.filter(perpetrator=item).aggregate(total_civilian_count=Sum('number_of_civilian'))['total_civilian_count']
        
        
            if total_civilian_count is None:
                total_civilian_count = 0

            pi_chart_data_points.append(Civilian_victims.objects.filter(

                approval=True, perpetrator=item).count() + total_civilian_count)



            verified_list.append(item)

            verified_legend.append(f"{item} ({round((count_items/total_count)*100, 1)}%)")

    pie_chart = go.Figure(data=[go.Pie(labels=verified_legend, values=pi_chart_data_points,

                hoverinfo='label+value', textinfo='value+percent', textposition='inside')])

    # Update the layout to increase width and height
    pie_chart.update_layout(
    autosize=True,  # Enable autosizing to make the chart responsive
    margin=dict(l=0, r=0, t=30, b=0),  # Adjust margin as needed
    legend=dict(orientation="h", yanchor="top", y=1.5),  # Position legend at the top
)

    # end of to be updated

    pie_chart.update_traces(marker=dict(colors=['rgb(13, 93, 149)', 'rgb(36, 102, 71)', '#2ca02c', '#d62728', 'rgb(126, 34, 189)', 'rgb(121, 53, 40)']),

     textinfo='value+percent', textfont=dict(color='white', size=14))

    # Doughnut Chart

    verified_list = []

    verified_legend = []

    doughnut_chart_data_points = []

    gender_list = ['Male', 'Female', 'Unknown']



    total_count = Civilian_victims.objects.filter(approval=True).count()

    for item in gender_list:

        count_items = Civilian_victims.objects.filter(approval=True, gender=item).count()

        if count_items > 0:



            doughnut_chart_data_points.append(count_items)



            verified_list.append(item)

            verified_legend.append(f"{item} ({round((count_items/total_count)*100, 1)}%)")



    # Create the donut chart

    donut_chart = go.Figure(data=[go.Pie(labels=verified_legend, values=doughnut_chart_data_points, hole=0.5, 

            hoverinfo='label+value', textposition='inside', textinfo='value+percent')])

    # Update the layout to increase width and height
    donut_chart.update_layout(
    autosize=True,  # Enable autosizing to make the chart responsive
    margin=dict(l=0, r=0, t=30, b=0),  # Adjust margin as needed
    legend=dict(orientation="h", yanchor="top", y=1.5),  # Position legend at the top
)

    donut_chart.update_traces(marker=dict(colors=['rgb(102, 73, 36)', 'rgb(214, 39, 40)', 'rgb(36, 102, 71)']),

        textinfo='value+percent', textfont=dict(color='white', size=14))



    # Convert the chart to HTML

    doughnut_plot_div = plot(donut_chart, output_type='div')

    # get sum of unverified ciivilians
    if Unverified_civilian.objects.exists():
        total_civilians = Unverified_civilian.objects.aggregate(total_civilians=Sum('number_of_civilian'))['total_civilians']
    else:
        total_civilians = 0
    
    context = {
        # counter data
        'count_civilian': count_civilian,
        'count_articles': count_articles,
        'count_panel': count_panel,
        'count_photo': count_photo,
        'count_video': count_video,
        'count_unverified_civilian':total_civilians,
        # hero image object
        'hero_image': random_hero_image.hero_image.url,
        # section data
        'civilian_victims': civilian_victims,
        'analysis_articles': analysis_articles,
        # Chart data
        'line_data_points': line_chart_data_points,
        'bar_data_points': bar_chart_data_points,
        'bar_chart_items_percentage': bar_chart_items_percentage,
        'line_chart_items_percentage': line_chart_items_percentage,
        'photo_archives': photo_archives,
        'video_archives': video_archives,
        'pi_data_points': pie_chart.to_html(full_html=False),
        'doughnut_data_points': doughnut_plot_div
    }

    print(f'bar_chart_items_percentage {bar_chart_items_percentage}')

    return render(request, 'index.html', context)


def civilian_victims_by_name(request):
    filters = {
        'name': request.GET.get('name', '').strip(),
        'atrocity': request.GET.get('atrocity', '').strip(),
        'woreda': request.GET.get('woreda', '').strip(),
        'gender': request.GET.get('gender', '').strip(),
    }
    
    # Generate cache key based on filters and pagination
    cache_key = f'victims_by_name:{":".join(filters.values())}:page:{request.GET.get("page", 1)}'
    
    # Check if it's an HTMX partial request
    is_htmx_request = request.headers.get('HX-Request') == 'true' and request.headers.get('HX-Boosted') != 'true'
    
    # Try to get from cache for HTMX requests
    if is_htmx_request:
        cached_response = cache.get(cache_key)
        if cached_response:
            return render(request, 'public_partials/civilian_victim_results.html', cached_response)

    civilian_victims = (
        Civilian_victims.objects
        .filter(approval=True)
        .select_related('woreda')
        .only(
            'id', 'full_name', 'gender', 'age', 'perpetrator',
            'place_of_killing', 'woreda', 'source', 'source_link',
            'date_of_event', 'remark', 'date_created',
        )
    )

    if filters['name']:
        civilian_victims = civilian_victims.filter(full_name__icontains=filters['name'])
    if filters['atrocity']:
        civilian_victims = civilian_victims.filter(perpetrator=filters['atrocity'])
    if filters['woreda']:
        civilian_victims = civilian_victims.filter(woreda_id=filters['woreda'])
    if filters['gender']:
        civilian_victims = civilian_victims.filter(gender=filters['gender'])

    paginator = Paginator(civilian_victims, 10)
    page = paginator.get_page(request.GET.get('page'))
    has_filters = any(filters.values())
    total_count = (
        Civilian_victims.objects.filter(approval=True).count()
        if has_filters else paginator.count
    )

    pagination_params = request.GET.copy()
    pagination_params.pop('page', None)

    context = {
        'page': page,
        'page_offset': page.start_index() - 1 if paginator.count else 0,
        'total_count': total_count,
        'filtered_count': paginator.count,
        'filters': filters,
        'pagination_query': pagination_params.urlencode(),
        'atrocity_choices': Civilian_victims.Perpetrator_Choices,
        'gender_choices': Civilian_victims.Gender_Choices,
        'woreda_list': Tigray_woreda.objects.only('woreda_name'),
    }

    # Cache HTMX partial responses for 30 minutes
    if is_htmx_request:
        cache.set(cache_key, context, 1800)
        return render(request, 'public_partials/civilian_victim_results.html', context)
    
    template_name = 'civilian_victims_by_name.html'
    return render(request, template_name, context)

def Civilian_victim_photo_page(request):
    filters = {
        'name': request.GET.get('name', '').strip(),
        'atrocity': request.GET.get('atrocity', '').strip(),
        'woreda': request.GET.get('woreda', '').strip(),
    }
    
    # Generate cache key based on filters and pagination
    cache_key = f'victims_photo:{":".join(filters.values())}:page:{request.GET.get("page", 1)}'
    
    # Check if it's an HTMX partial request
    is_htmx_request = request.headers.get('HX-Request') == 'true' and request.headers.get('HX-Boosted') != 'true'
    
    # Try to get from cache for HTMX requests
    if is_htmx_request:
        cached_response = cache.get(cache_key)
        if cached_response:
            return render(request, 'public_partials/victim_photo_batch.html', cached_response)

    civilian_data = (
        Civilian_victims.objects
        .filter(approval=True)
        .select_related('woreda')
        .only(
            'id', 'full_name', 'gender', 'picture', 'zone', 'woreda',
            'perpetrator', 'place_of_killing', 'date_created',
        )
    )

    if filters['name']:
        civilian_data = civilian_data.filter(full_name__icontains=filters['name'])
    if filters['atrocity']:
        civilian_data = civilian_data.filter(perpetrator=filters['atrocity'])
    if filters['woreda']:
        civilian_data = civilian_data.filter(woreda_id=filters['woreda'])

    paginator = Paginator(civilian_data, 30)
    page = paginator.get_page(request.GET.get('page'))
    pagination_params = request.GET.copy()
    pagination_params.pop('page', None)

    context = {
        'page': page,
        'filtered_count': paginator.count,
        'filters': filters,
        'pagination_query': pagination_params.urlencode(),
        'atrocity_choices': Civilian_victims.Perpetrator_Choices,
        'woreda_list': Tigray_woreda.objects.only('woreda_name'),
    }

    # Cache HTMX partial responses for 30 minutes
    if is_htmx_request:
        cache.set(cache_key, context, 1800)
        return render(request, 'public_partials/victim_photo_batch.html', context)
    
    template_name = 'civilin_vicitm_photo_page.html'
    return render(request, template_name, context)
    
# a method view to search a specfic civilian victim
def Search_civilian(request):
    
    # define context variable with in scope of the function
    context = {}
    
    selected_atrocity = request.GET.get('atrocity')
    selected_woreda = request.GET.get('woreda')
    
    if selected_atrocity:
        get_search_result = Civilian_victims.objects.filter(perpetrator=selected_atrocity, approval=True)
        
        context = {
            'result': get_search_result
        }
        
    if selected_woreda:
        Woreda_obj = Tigray_woreda.objects.get(woreda_name = selected_woreda)
        get_search_result = Civilian_victims.objects.filter(woreda=Woreda_obj, approval=True)
        
        context = {
            'result': get_search_result
        }

    return render(request, 'search_civilian_victim.html', context)


def _woredas_with_victim_counts():
    return list(
        Tigray_woreda.objects
        .annotate(
            victim_count=Count(
                'civilian_victims',
                filter=Q(civilian_victims__approval=True),
            )
        )
        .only('woreda_name', 'latitude', 'longitude')
    )


def _render_victim_location_map(woreda_list, selected_woreda=None):
    selected_name = selected_woreda.woreda_name if selected_woreda else ''
    cache_key = f'victim-location-map-v2:{slugify(selected_name) or "all"}'
    cached_map = cache.get(cache_key)
    if cached_map is not None:
        return cached_map

    center = (
        [selected_woreda.latitude, selected_woreda.longitude]
        if selected_woreda else [13.881273, 39.127495]
    )
    location_map = folium.Map(
        location=center,
        zoom_start=10 if selected_woreda else 7,
        width='100%',
        height='100%',
        tiles='OpenStreetMap',
    )

    for woreda in woreda_list:
        if woreda.woreda_name == 'Other' or not woreda.victim_count:
            continue

        detail_url = reverse(
            'civilian-victim-map-info-page',
            args=[slugify(woreda.woreda_name)],
        )
        popup_content = (
            f'<b><a title="Get full information" href="{detail_url}" '
            f'target="_top">{escape(woreda.woreda_name)} Woreda</a></b>'
            f'<br>Civilian Victims: {woreda.victim_count}'
        )
        marker_options = {
            'location': (woreda.latitude, woreda.longitude),
            'popup': folium.Popup(popup_content, max_width=300),
        }
        if selected_name == woreda.woreda_name:
            marker_options['icon'] = folium.Icon(color='red', icon='star')
        folium.Marker(**marker_options).add_to(location_map)

    map_html = location_map._repr_html_()
    cache.set(cache_key, map_html, 300)
    return map_html


def Civilian_victim_by_map(request):
    # Cache for 10 minutes (600 seconds) - map data doesn't change frequently
    cache_key = 'civilian_victim_map_data'
    cached_data = cache.get(cache_key)
    if cached_data:
        return render(request, 'civilian_victims_map.html', cached_data)
    
    woreda_list = _woredas_with_victim_counts()
    context = {
        'geolocation': _render_victim_location_map(woreda_list),
        'woreda_list': woreda_list,
    }
    cache.set(cache_key, context, 600)
    return render(request, 'civilian_victims_map.html', context)


@cache_page(600)  # Cache for 10 minutes
def Civilian_victim_by_map_info(request, woreda_pr):
    woreda_list = _woredas_with_victim_counts()
    requested_slug = slugify(woreda_pr)
    selected_woreda = next(
        (woreda for woreda in woreda_list if slugify(woreda.woreda_name) == requested_slug),
        None,
    )
    if selected_woreda is None:
        raise Http404('Woreda not found')

    civilian_victims = (
        Civilian_victims.objects
        .filter(woreda=selected_woreda, approval=True)
        .select_related('woreda')
        .only(
            'id', 'full_name', 'gender', 'age', 'perpetrator',
            'place_of_killing', 'woreda', 'source', 'source_link',
            'date_of_event', 'remark', 'date_created',
        )
    )
    paginator = Paginator(civilian_victims, 25)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'geolocation': _render_victim_location_map(woreda_list, selected_woreda),
        'civilian_victims': page.object_list,
        'page': page,
        'page_offset': page.start_index() - 1 if paginator.count else 0,
        'selected_woreda': selected_woreda,
        'woreda_list': woreda_list,
    }
    return render(request, 'civilian_victims_map_info.html', context)

@cache_page(1800)  # Cache for 30 minutes
def view_victim_info(request, id):

    civilian_victim_item = Civilian_victims.objects.get(id=id, approval=True)

    context = {
        'item': civilian_victim_item
    }

    return render(request, 'view_victim_info.html', context)

def unverified_civilian_victims_by_name(request):
    filters = {
        'atrocity': request.GET.get('atrocity', '').strip(),
        'woreda': request.GET.get('woreda', '').strip(),
    }
    
    # Generate cache key based on filters and pagination
    cache_key = f'unverified_victims:{":".join(filters.values())}:page:{request.GET.get("page", 1)}'
    
    is_partial = request.headers.get('HX-Boosted') != 'true' and (
        request.headers.get('HX-Request') == 'true'
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    )
    
    # Try to get from cache for HTMX requests
    if is_partial:
        cached_response = cache.get(cache_key)
        if cached_response:
            return render(request, 'public_partials/unverified_results.html', cached_response)

    civilian_victims = (
        Unverified_civilian.objects
        .select_related('woreda')
        .only(
            'id', 'location', 'number_of_civilian', 'perpetrator',
            'woreda', 'source', 'source_link', 'remark', 'date_created',
        )
    )
    if filters['atrocity']:
        civilian_victims = civilian_victims.filter(perpetrator=filters['atrocity'])
    if filters['woreda']:
        civilian_victims = civilian_victims.filter(woreda_id=filters['woreda'])

    paginator = Paginator(civilian_victims, 10)
    page = paginator.get_page(request.GET.get('page'))
    pagination_params = request.GET.copy()
    pagination_params.pop('page', None)

    context = {
        'page': page,
        'page_offset': page.start_index() - 1 if paginator.count else 0,
        'filtered_count': paginator.count,
        'filters': filters,
        'pagination_query': pagination_params.urlencode(),
    }

    if is_partial:
        # Cache HTMX partial responses for 30 minutes
        cache.set(cache_key, context, 1800)
        return render(request, 'public_partials/unverified_results.html', context)

    context.update({
        'total_civilians': Unverified_civilian.objects.aggregate(
            total=Sum('number_of_civilian', default=0)
        )['total'],
        'atrocity_choices': Unverified_civilian.Perpetrator_Choices,
        'woreda_list': Tigray_woreda.objects.only('woreda_name'),
    })

    return render(request, 'unverified_civilian_victim.html', context)


@cache_page(1800)  # Cache for 30 minutes
def View_article(request, id):

    # get random articles
    random_analysis_articles = Analysis_articles.objects.exclude(
        id=id).exclude(approval=False).exclude(draft=True).order_by('?')[:10]

    # get number of articles under general categories
    general_articles = Analysis_articles.objects.filter(Q(approval = True)
    & Q(endf_related = False) & Q(personal_account = False) & Q(draft = False)).count()

    # get number of articles under tegaru Ex-ENDF categories
    endf_articles = Analysis_articles.objects.filter(Q(approval = True)
    & Q(endf_related = True) & Q(draft = False)).count()

    # get number of articles under personal accounts categories
    personal_acc = Analysis_articles.objects.filter(Q(approval = True)
     & Q(personal_account = True) & Q(draft = False)).count()

    analysis_article_item = Analysis_articles.objects.get(id=id, approval=True, draft=False)

    analysis_article_comments = Article_comments.objects.filter(
        article=analysis_article_item)

    context = {
        'random_articles': random_analysis_articles,
        'general_articles': general_articles,
        'endf_articles': endf_articles,
        'personal_acc': personal_acc,
        'item': analysis_article_item,
        'comments': analysis_article_comments
    }

    return render(request, 'view_article.html', context)


def Article_comment(request, article_id):

    if request.method == 'POST':

        article_object = Analysis_articles.objects.get(
            id=article_id, approval=True, draft=False)
        Article_comments.objects.create(article=article_object, name=request.POST.get('name'), email=request.POST.get('email'),
                                        content=request.POST.get('comment'))

        print('Comment added successfully')

        return redirect(f'/View-article/{article_id}')

    return None


def Articles_page(request):

    total_articles = Analysis_articles.objects.filter(approval=True, draft=False)

    paginator = Paginator(total_articles, 12)

    page_number = request.GET.get('page', 1)

    page = paginator.get_page(page_number)

    context = {
        'page': page
    }

    return render(request, 'analysis_articles_page.html', context)

@cache_page(1800)  # Cache for 30 minutes
def General_category_articles(request, category):

    from App.seo_config import ARTICLE_CATEGORY_SEO

    category_meta = ARTICLE_CATEGORY_SEO.get(category, ARTICLE_CATEGORY_SEO['general'])

    # if the selected category is "General"
    if category == 'general':
        general_articles = Analysis_articles.objects.filter(Q(approval = True)
                        & Q(endf_related = False) & Q(personal_account = False) & Q(draft = False))

        paginator = Paginator(general_articles, 12)

    # if the selected category is "Personal accounts"
    if category == 'personal':
        personal_articles =  Analysis_articles.objects.filter(Q(approval = True) 
                        & Q(personal_account = True) & Q(draft = False))

        paginator = Paginator(personal_articles, 12)
        
    # if the selected category is "ENDF related"
    if category == 'endf':
        endf_articles = Analysis_articles.objects.filter(Q(approval = True)
                        & Q(endf_related = True) & Q(draft = False))

        paginator = Paginator(endf_articles, 12)

    # create django pagination
    page_number = request.GET.get('page', 1)

    page = paginator.get_page(page_number)

    context = {
        'page': page,
        'category_meta': category_meta,
        'category_slug': category,
    }

    return render(request, 'articles_category.html', context)

def Search_article(request):

    context = {}

    if request.method == 'POST':
        searched_articles = Analysis_articles.objects.filter(Q(title__icontains = request.POST.get('search_query'))
                            & (Q(draft = False)))
        
        context = {
            'search_result': searched_articles,
            'search_query': request.POST.get('search_query')
        }

    return render(request, 'search_articles.html', context)

def Webinar_discussion_page(request):

    toatl_discussion = Webinar.objects.all()

    paginator = Paginator(toatl_discussion, 12)

    page_number = request.GET.get('page', 1)

    page = paginator.get_page(page_number)

    context = {
        'page': page
    }

    return render(request, 'webinar_discussion.html', context)


@cache_page(1800)  # Cache for 30 minutes
def View_webinar_discussion(request, id):

    webinar_discussion_item =Webinar.objects.get(id=id)

    context = {
        'item': webinar_discussion_item,
    }

    return render(request, 'view_panel_discussion.html', context)

def Archive_photo(request):
    selected_woreda = request.GET.get('woreda', '').strip()
    is_partial = (
        request.headers.get('HX-Request') == 'true'
        and request.headers.get('HX-Boosted') != 'true'
    )
    
    # Generate cache key based on selected woreda
    cache_key = f'archive_photo:{selected_woreda or "all"}:page:{request.GET.get("page", 1)}'
    
    # Try to get from cache
    if is_partial:
        cached_response = cache.get(cache_key)
        if cached_response:
            return render(request, 'public_partials/photo_archive_batch.html', cached_response)
    
    photo_archives = (
        Photo_archive.objects
        .select_related('woreda')
        .only(
            'id', 'location', 'woreda', 'date_of_event', 'description',
            'photo', 'graphic', 'date_created',
        )
    )
    if selected_woreda:
        photo_archives = photo_archives.filter(woreda_id=selected_woreda)

    paginator = Paginator(photo_archives, 6)
    page = paginator.get_page(request.GET.get('page'))
    pagination_params = request.GET.copy()
    pagination_params.pop('page', None)

    context = {
        'page': page,
        'filtered_count': paginator.count,
        'selected_woreda': selected_woreda,
        'pagination_query': pagination_params.urlencode(),
    }

    # Cache partial response for 30 minutes
    if is_partial:
        cache.set(cache_key, context, 1800)
        return render(request, 'public_partials/photo_archive_batch.html', context)

    context['woreda_list'] = Tigray_woreda.objects.only('woreda_name')

    return render(request, 'archive_by_photo.html', context)
    
# a method view to search a specfic photo archive by woreda
def Search_archive_photo(request):
    selected_woreda = request.GET.get('woreda')
    target = reverse('archive-photo')
    if selected_woreda:
        target = f'{target}?{urllib.parse.urlencode({"woreda": selected_woreda})}'
    return redirect(target)


@cache_page(1800)  # Cache for 30 minutes
def Archive_video(request):

    video_archives = Video_archive.objects.all()

    paginator = Paginator(video_archives, 30)

    page_number = request.GET.get('page', 1)

    page = paginator.get_page(page_number)

    context = {
        'page': page
    }

    return render(request, 'archive_by_video.html', context)

@cache_page(1800)  # Cache for 30 minutes
def Watch_video(request, id):

    get_obj = Video_archive.objects.get(id = id)

    random_video_archives = Video_archive.objects.exclude(
        id=id).order_by('?')[:10]

    context = {
        'current_video': get_obj,
        'random_video': random_video_archives
    }

    return render(request, 'watch_video.html', context)


def Send_us_information(request):
    if request.method == 'POST':
        gender = request.POST.get('gender')
        photo = request.FILES.get('photo')
        woreda = Tigray_woreda.objects.only('woreda_name', 'zone').get(
            pk=request.POST.get('woreda')
        )
        full_name = ' '.join(filter(None, (
            request.POST.get('first_name', '').strip(),
            request.POST.get('middle_name', '').strip(),
            request.POST.get('last_name', '').strip(),
        )))

        Civilian_victims.objects.create(
            sender_fullname=request.POST.get('sender_fullname'),
            sender_location=request.POST.get('sender_address'),
            sender_email=request.POST.get('sender_email'),
            sender_phone=request.POST.get('sender_phone'),
            full_name=full_name,
            gender=gender,
            age=request.POST.get('age') or None,
            picture=(
                photo
                or ('civilian_victims_pic/default.png' if gender == 'Male'
                    else 'civilian_victims_pic/default_female.jpg')
            ),
            perpetrator=request.POST.get('perpetrator'),
            woreda=woreda,
            zone=woreda.zone,
            place_of_killing=request.POST.get('place'),
            date_of_event=request.POST.get('date_of_event') or None,
            remark=request.POST.get('remark'),
        )

        return JsonResponse({'success': True})

    woreda_names = cache.get('submission-form-woreda-names')
    if woreda_names is None:
        woreda_names = list(
            Tigray_woreda.objects.order_by('woreda_name').values_list(
                'woreda_name', flat=True
            )
        )
        cache.set('submission-form-woreda-names', woreda_names, 900)

    context = {
        'woreda_names': woreda_names,
        'gender_choices': Civilian_victims.Gender_Choices,
        'atrocity_choices': Civilian_victims.Perpetrator_Choices,
    }

    return render(request, 'send_us_information.html', context)
    
def Send_archive(request):
    
    context = {
        'woreda_list': Tigray_woreda.objects.all(),
    }
    
    if request.method == 'POST':
        # email message setting
        archive_file = request.FILES['photo']
        email_subject = request.POST['sender_email']
        email_body = '''
                <!DOCTYPE html
                PUBLIC "-//W3C//DTD XHTML 1.0 Transitional //EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
            <html xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office"
                xmlns:v="urn:schemas-microsoft-com:vml" lang="en">
            
            <head>
                <link rel="stylesheet" type="text/css" hs-webfonts="true"
                    href="https://fonts.googleapis.com/css?family=Lato|Lato:i,b,bi">
                <title>Email template</title>
                <meta property="og:title" content="Email template">
            
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            
                <meta http-equiv="X-UA-Compatible" content="IE=edge">
            
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            
            
            </head>
            
            <body bgcolor="#F5F8FA"
                style="width: 100%; margin: auto 0; padding:0; font-family:Lato, sans-serif; font-size:18px; color:#33475B; word-break:break-word">
            
                <! View in Browser Link -->
            
                    <div id="email" style="margin: auto;
                    width: 600px;
                    background-color: white;">
                        <table align="right" role="presentation">
                            <tr>
                                <td style="vertical-align: top;">
                                    <a class="subtle-link" style="text-decoration: underline;
                    color: inherit;
                    font-weight: bold;
                    color: #253342; font-size: 9px; 
                    text-transform:uppercase; 
                    letter-spacing: 1px;
                    color: #CBD6E2;" href="#">View in Browser</a>
                                </td>
                            <tr>
                        </table>
            
            
                        <! Banner -->
                            <table role="presentation" width="100%">
                                <tr>
            
                                    <td bgcolor="black" align="center" style="color: white;vertical-align: top;">
            
                                        <h3><i>tigraygenocide.com</i> Archive Information </h3>
            
                                    </td>
                            </table>
            
                            <br><br>
            
                            <! First Row -->
            
                                <table role="presentation" border="0" cellpadding="0" cellspacing="10px"
                                    style="padding: 30px 30px 30px 60px;">
                                    <tr>
                                        <td style="vertical-align: top;">
                                            <ul>
                                                <li>
                                                    <p style="text-weight: normal; font-weight: 100;">Sender Fullname: <b
                                                            style="color: #73879C">{}</b></p>
                                                </li>
                                                <li>
                                                    <p style="text-weight: normal; font-weight: 100;">Sender Email: <b
                                                            style="color: #73879C">{}</b></p>
                                                </li>
                                                <li>
                                                    <p style="text-weight: normal; font-weight: 100;">Sender Address: <b
                                                            style="color: #73879C">{}</b></p>
                                                </li>
                                                <li>
                                                    <p style="text-weight: normal; font-weight: 100;">Sender Phone: <b
                                                            style="color: #73879C">{}</b></p>
                                                </li>
                                                <li>
                                                    <p style="text-weight: normal; font-weight: 100;">Location: <b
                                                            style="color: #73879C">{}</b></p>
                                                </li>
                                                <li>
                                                    <p style="text-weight: normal; font-weight: 100;">Woreda: <b
                                                            style="color: #73879C">{}</b></p>
                                                </li>
                                                <li>
                                                    <p style="text-weight: normal; font-weight: 100;">Date of event:: <b
                                                            style="color: #73879C">{}</b></p>
                                                </li>
                                                <li>
                                                    <p style="text-weight: normal; font-weight: 100;">Description:: <b
                                                            style="color: #73879C">{}</b></p>
                                                </li>
            
                                            </ul>
                                        </td>
                                    </tr>
                                </table>
            
                    </div>
            </body>
            
            </html>
            '''.format(request.POST.get('sender_fullname'), request.POST.get('sender_email'), request.POST.get('sender_address'), request.POST['sender_phone'], request.POST['location'], request.POST['woreda'], request.POST['date_of_event'], request.POST['description'])
    
        email_from = request.POST['sender_email']
        email_to = [settings.EMAIL_HOST_USER]

        msg = EmailMessage(email_subject, email_body, email_from, email_to)
        msg.attach(archive_file.name, archive_file.read(), archive_file.content_type)
        msg.content_subtype = "html"  # Set the content type to HTML
        # Send the email
        msg.send()
        
        return JsonResponse({'success': True})
    
    return render(request, 'send-archive.html', context)

@cache_page(3600)  # Cache for 60 minutes - static page
def About_us(request):

    return render(request, 'about_us.html')

def Contact_us(request):
    
    if request.method == 'POST':
        email_subject = request.POST['sender_subject']
        email_body = request.POST['sender_message']
        email_from = request.POST['sender_email']
        email_to = [settings.EMAIL_HOST_USER]

        msg = EmailMessage(email_subject, email_body, email_from, email_to)
        msg.content_subtype = "html"  # Set the content type to HTML

        # Send the email
        msg.send()
        
        return JsonResponse({'success': True})

    return render(request, 'contact-us.html')


""" 
Adminstrator Page View Methods
"""


def Admin_login(request):

    form = LoginCaptchaForm()

    if request.user.is_authenticated:

        return redirect('/Admin-dashboard')

    else:

        if request.method == 'POST':

            username = request.POST.get('login_username')
            password = request.POST.get('login_password')
            # authenticate user
            user_auth = authenticate(username=username, password=password)
            if user_auth is not None:
                form = LoginCaptchaForm(request.POST)
                if form.is_valid():
                    human = True
                    login(request, user_auth)
                    return redirect('/Admin-dashboard')
            else:
                messages.error(request, 'Incorrect login credenials')
                return redirect('/Adminstrator-login-page')

    return render(request, 'admin_templates/account_templates/login.html', {'captcha_form': form})

def Admin_logout(request):

    logout(request)

    return redirect('/Adminstrator-login-page')


@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def admin_dashboard(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    # Count available contents
    count_civilian = Civilian_victims.objects.filter(approval=True).count()
    count_articles = Analysis_articles.objects.filter(approval=True, draft=False).count()
    count_panel = Webinar.objects.all().count()
    count_photo = Photo_archive.objects.all().count()
    count_video = Video_archive.objects.all().count()
    count_pending = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    # line chart
    line_chart_data_points = []
    zone_list = ['Western Tigray', 'Eastern Tigray', 'Central Tigray', 'North Western Tigray',
                 'Southern Tigray', 'South Eastern Tigray', 'Mekelle Special', 'Other']
    
    for item in zone_list:
        total_civilian_count = Unverified_civilian.objects.filter(zone=item).aggregate(total_civilian_count=Sum('number_of_civilian'))['total_civilian_count']
        if total_civilian_count is None:
            total_civilian_count = 0
        line_chart_data_points.append(Civilian_victims.objects.filter(
            zone=item, approval=True).count() + total_civilian_count)

    line_chart_items_percentage = []
    for item in line_chart_data_points:
        try:
            total_civilians = Unverified_civilian.objects.aggregate(total_civilians=Sum('number_of_civilian'))['total_civilians']
            if total_civilian_count is None:
                total_civilian_count = 0
            count = Civilian_victims.objects.filter(approval=True).count() + total_civilians 
            if count != 0:
                percentage = round((item * 100) / count, 2)
                line_chart_items_percentage.append(percentage)
            else:
                # Handle the case where count is zero
                # For example, set percentage to 0 or some default value
                line_chart_items_percentage.append(0)
        except ZeroDivisionError:
            # Handle the ZeroDivisionError
            # For example, set percentage to 0 or some default value
            line_chart_items_percentage.append(0)


    # bar chart
    bar_chart_data_points = [
        Civilian_victims.objects.filter(
            approval=True, age__gt=int(0), age__lt=int(11)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(11), age__lt=int(18)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(18), age__lt=int(33)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(33), age__lt=int(49)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(49), age__lt=int(64)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(64), age__lt=int(80)).count(),
        Civilian_victims.objects.filter(
            approval=True, age__gte=int(80), age__lt=int(95)).count(),
        Civilian_victims.objects.filter(approval=True, age = None).count()
    ]

    bar_chart_items_percentage = []
    for item in bar_chart_data_points:
        try:
            count = Civilian_victims.objects.filter(approval=True).count()
            if count != 0:
                percentage = round((item * 100) / count, 2)
                bar_chart_items_percentage.append(percentage)
            else:
                # Handle the case where count is zero
                # For example, set percentage to 0 or some default value
                bar_chart_items_percentage.append(0)
        except ZeroDivisionError:
            # Handle the ZeroDivisionError
            # For example, set percentage to 0 or some default value
            bar_chart_items_percentage.append(0)


    # Pie Chart
    

    verified_list = []

    verified_list = []

    verified_legend = []

    pi_chart_data_points = []

    perpetrator_list = ['Died from lack of food', 'Killed by Eritrean forces', 'Died from lack of medicine',

                    'Killed by Ethiopian forces', 'Killed by Ethiopian and Eritrean forces', 'Killed by Amhara militia and Fano']

    

    total_count = Civilian_victims.objects.filter(approval=True).count()

    for item in perpetrator_list:
        
        total_civilian_count = Unverified_civilian.objects.filter(perpetrator=item).aggregate(total_civilian_count=Sum('number_of_civilian'))['total_civilian_count']
        
        
        if total_civilian_count is None:
            total_civilian_count = 0
        
        count_items = (Civilian_victims.objects.filter(approval=True, perpetrator=item).count() + total_civilian_count)

        if count_items > 0:

            total_civilian_count = Unverified_civilian.objects.filter(perpetrator=item).aggregate(total_civilian_count=Sum('number_of_civilian'))['total_civilian_count']
        
        
            if total_civilian_count is None:
                total_civilian_count = 0

            pi_chart_data_points.append(Civilian_victims.objects.filter(

                approval=True, perpetrator=item).count() + total_civilian_count)



            verified_list.append(item)

            verified_legend.append(f"{item} ({round((count_items/total_count)*100, 1)}%)")

    pie_chart = go.Figure(data=[go.Pie(labels=verified_legend, values=pi_chart_data_points,

                hoverinfo='label+value', textinfo='value+percent', textposition='inside')])

    # Update the layout to increase width and height
    pie_chart.update_layout(
    autosize=True,  # Enable autosizing to make the chart responsive
    margin=dict(l=0, r=0, t=30, b=0),  # Adjust margin as needed
    legend=dict(orientation="h", yanchor="top", y=1.5),  # Position legend at the top
)

    # end of to be updated



    pie_chart.update_traces(marker=dict(colors=['rgb(13, 93, 149)', 'rgb(36, 102, 71)', '#2ca02c', '#d62728', 'rgb(126, 34, 189)', 'rgb(121, 53, 40)']),

     textinfo='value+percent', textfont=dict(color='white', size=14))



    # Doughnut Chart

    verified_list = []

    verified_legend = []

    doughnut_chart_data_points = []

    gender_list = ['Male', 'Female', 'Unknown']



    total_count = Civilian_victims.objects.filter(approval=True).count()

    for item in gender_list:

        count_items = Civilian_victims.objects.filter(approval=True, gender=item).count()

        if count_items > 0:



            doughnut_chart_data_points.append(count_items)



            verified_list.append(item)

            verified_legend.append(f"{item} ({round((count_items/total_count)*100, 1)}%)")



    # Create the donut chart

    donut_chart = go.Figure(data=[go.Pie(labels=verified_legend, values=doughnut_chart_data_points, hole=0.5, 

            hoverinfo='label+value', textposition='inside', textinfo='value+percent')])



    donut_chart.update_traces(marker=dict(colors=['rgb(102, 73, 36)', 'rgb(214, 39, 40)', 'rgb(36, 102, 71)']),

        textinfo='value+percent', textfont=dict(color='white', size=14))



    # Convert the chart to HTML

    doughnut_plot_div = plot(donut_chart, output_type='div')

    context = {
        'pending_count': pending_count,
        'count_civilian': count_civilian,
        'count_articles': count_articles,
        'count_panel': count_panel,
        'count_photo': count_photo,
        'count_video': count_video,
        'count_pending': count_pending,
        'line_data_points': line_chart_data_points,
        'bar_data_points': bar_chart_data_points,
        'line_chart_items_percentage': line_chart_items_percentage,
        'bar_chart_items_percentage': bar_chart_items_percentage,
        'pi_data_points': pie_chart.to_html(full_html=False),
        'doughnut_data_points': doughnut_plot_div,
        'Administrator': Administrator.objects.get(user=request.user)
    }

    return render(request, 'admin_templates/index.html', context)


@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def admin_civilian_victims_page(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    civilian_victims_data = Civilian_victims.objects.filter(
        approval=True).count()

    civilian_victims = Civilian_victims.objects.filter(approval=True)

    context = {
        'pending_count': pending_count,
        'civilian_victims': civilian_victims,
        'civilian_victims_data': civilian_victims_data,
        'Administrator': Administrator.objects.get(user=request.user),
        'woreda_list': Tigray_woreda.objects.all(),
    }

    return render(request, 'admin_templates/civilian_victim/civilian_victims.html', context)

@login_required(login_url='/Administrator-login-page', redirect_field_name='authentication_required')
def add_civilian_victim(request):
    pending_count = Civilian_victims.objects.filter(approval=False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    context = {
        'pending_count': pending_count,
        'Administrator': Administrator.objects.get(user=request.user),
        'woreda_list': Tigray_woreda.objects.all(),
    }
    
    # Initialize success_message variable
    success_message = ""

    if request.method == 'POST':
        civilian_model = Civilian_victims()
        civilian_model.author = User.objects.get(username=request.user)
        civilian_model.full_name = request.POST.get('fullname')
        civilian_model.gender = request.POST.get('gender')
        civilian_model.age = request.POST.get('age') or None
        if request.FILES.get('photo'):
            civilian_model.picture = request.FILES.get('photo')
        else:
            if request.POST.get('gender') == 'Male':
                civilian_model.picture = "civilian_victims_pic/default.png"
            else:
                civilian_model.picture = "civilian_victims_pic/default_female.jpg"
        civilian_model.perpetrator = request.POST.get('perpetrator')
        woreda_obj = Tigray_woreda.objects.get(woreda_name=request.POST.get('woreda'))
        civilian_model.woreda = woreda_obj
        civilian_model.zone = woreda_obj.zone
        civilian_model.place_of_killing = request.POST.get('place')
        civilian_model.date_of_event = request.POST.get('date_of_event') or None
        civilian_model.source = request.POST.get('source')
        civilian_model.source_link = request.POST.get('source_link')
        civilian_model.remark = request.POST.get('remark')

        # Check if the fullname and woreda already exist
        if Civilian_victims.objects.filter(full_name=request.POST.get('fullname')).exists() and Civilian_victims.objects.filter(woreda=woreda_obj).exists():
            
            previous_existed_civilian_victim = Civilian_victims.objects.filter(full_name=request.POST.get('fullname'), woreda=woreda_obj).first()
            
            if User.objects.get(username=request.user).is_superuser:
                civilian_model.approval = True

            civilian_model.save()
            
            error_message = f'A civilian victim with the provided full name and Woreda already exists. <a href="https://tigraygenocide.com/View-victim-info/{previous_existed_civilian_victim.id}" target="_blank"><u>Click here to view the existing victim</u></a>.'
                    
            # Return error message and new_duplicate_id in JSON format
            return JsonResponse({'message': error_message, 'new_duplicate_id': civilian_model.id}, status=400)

        else:
            if User.objects.get(username=request.user).is_superuser:
                civilian_model.approval = True

            civilian_model.save()

            if User.objects.get(username=request.user).is_superuser:
                success_message = 'New civilian victim data added successfully.'
            else:
                success_message = 'New civilian victim data added successfully and is pending approval.'

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # If the request is AJAX, return JSON response with success message
                return JsonResponse({'message': 'Success!', 'success_message': success_message}, status=200)

    # Pass the success_message to the template context
    context['success_message'] = success_message

    # Return the same context if not AJAX request
    return render(request, 'admin_templates/civilian_victim/add_civilian_victim.html', context)

@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def civilian_data_management(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    civilian_victims = Civilian_victims.objects.filter(approval=True)
    specfic_admin_civilian_victims = Civilian_victims.objects.filter(
        author=request.user)

    context = {
        'pending_count':pending_count,
        'civilian_victims': civilian_victims,
        'specfic_data': specfic_admin_civilian_victims,
        'Administrator': Administrator.objects.get(user=request.user)
    }

    return render(request, 'admin_templates/civilian_victim/civilian_data_management.html', context)


class Update_Civilian_Victim(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/civilian_victim/update_civilian_victim.html'
    model = Civilian_victims
    form_class = Civilian_Victim_Form
    success_message = 'Civilian victim informatiom updated successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Civilian_victims, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('civilian-data-management')

@login_required
def delete_duplicate_civilian_victim_item(request, pk):
    civilian_victim = get_object_or_404(Civilian_victims, id=pk)

    civilian_victim.delete()

    return redirect('admin-add-civilian')

class delete_civilian_victim_item(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/civilian_victim//delete_civilian_victim.html'
    model = Civilian_victims
    success_message = 'Civilian victim informatiom deleted successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Civilian_victims, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('civilian-data-management')

@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Add_unverified_civilian(request):
    pending_count = Civilian_victims.objects.filter(approval=False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    context = {
        'pending_count': pending_count,
        'Administrator': Administrator.objects.get(user=request.user),
        'woreda_list': Tigray_woreda.objects.all(),
    }

    if request.method == 'POST':
        unverified_model = Unverified_civilian()
        unverified_model.location = request.POST.get('location')
        unverified_model.number_of_civilian = request.POST.get('number_of_civilian')
        unverified_model.perpetrator = request.POST.get('perpetrator')
        woreda_obj = Tigray_woreda.objects.get(woreda_name=request.POST.get('woreda'))
        unverified_model.woreda = woreda_obj
        unverified_model.zone = woreda_obj.zone
        unverified_model.source = request.POST.get('source')
        unverified_model.source_link = request.POST.get('source_link')
        unverified_model.remark = request.POST.get('remark')

        unverified_model.save()

        # Add success message to context
        success_message = 'New unidentified civilian victims data added successfully.'

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # If the request is AJAX, return JSON response with success message
            return JsonResponse({'message': 'Success!', 'success_message': success_message}, status=200)

    return render(request, 'admin_templates/civilian_victim/unverified_add_data.html', context)
    
@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Unverified_civilian_data_management(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    unverified_civilian_victims = Unverified_civilian.objects.all()

    context = {
        'pending_count':pending_count,
        'unverified_civilian_victims': unverified_civilian_victims,
        'Administrator': Administrator.objects.get(user=request.user)
    }

    return render(request, 'admin_templates/civilian_victim/unverified_civilian_data_management.html', context)

class Update_unverified_Civilian_Victim(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/civilian_victim/unverified_update_civilian_victim.html'
    model = Unverified_civilian
    form_class = Unverified_civilian_form
    success_message = 'Civilian victim informatiom updated successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Unverified_civilian, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('unverified-civilian-data-management')

@login_required
def delete_unverified_civilian_victim(request, pk):
    unverified_civilian_victim = get_object_or_404(Unverified_civilian, id=pk)

    unverified_civilian_victim.delete()

    # Add success message
    messages.success(request, 'Unverified civilian victim data has been successfully removed.')

    return redirect('unverified-civilian-data-management')


@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def export_unverified_data(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
    
    
    # get sum of unverified ciivilians
    if Unverified_civilian.objects.exists():
        total_civilians = Unverified_civilian.objects.aggregate(total_civilians=Sum('number_of_civilian'))['total_civilians']
    else:
        total_civilians = 0

    civilian_victims = Unverified_civilian.objects.all()

    context = {
        'pending_count': pending_count,
        'civilian_victims': civilian_victims,
        'civilian_victims_data': total_civilians,
        'Administrator': Administrator.objects.get(user=request.user),
        'woreda_list': Tigray_woreda.objects.all(),
    }

    return render(request, 'admin_templates/civilian_victim/unverified_export_data.html', context)

@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Write_article(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    form = AnalysisArticleForm()

    context = {
        'pending_count': pending_count,
        'analysis_form': form,
        'Administrator': Administrator.objects.get(user=request.user)
    }

    if request.method == 'POST':
        form = AnalysisArticleForm(request.POST, request.FILES)
        if form.is_valid():

            # check if the article is Ex-ENDF related
            if request.POST.get('endf_related'):
                endf_related = True
            else:
                endf_related = False
            
            # check if the article is Personal Accounts
            if request.POST.get('personal_account'):
                personal_account = True
            else:
                personal_account = False

            insert_article = Analysis_articles(author=User.objects.get(username=request.user), title=form.cleaned_data.get('title'),
                                               thumbnail=form.cleaned_data.get('thumbnail'), content=form.cleaned_data.get('content'),
                                               endf_related=endf_related, personal_account = personal_account, approval=User.objects.get(username=request.user).is_superuser)
            insert_article.save()

            if User.objects.get(username=request.user).is_superuser is True:

                messages.success(
                    request, 'New analysis article shared successfully...')

            else:
                messages.success(
                    request, 'New analysis article shared successfully and is pending for an approval ...')

        return render(request, 'admin_templates/analysis_article/write_article.html', context)

    else:
        return render(request, 'admin_templates/analysis_article/write_article.html', context)



@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Draft_article(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    form = AnalysisArticleForm()

    context = {
        'pending_count': pending_count,
        'analysis_form': form,
        'Administrator': Administrator.objects.get(user=request.user)
    }

    if request.method == 'POST':
        form = AnalysisArticleForm(request.POST, request.FILES)
        if form.is_valid():

            # check if the article is Ex-ENDF related
            if request.POST.get('endf_related'):
                endf_related = True
            else:
                endf_related = False
            
            # check if the article is Personal Accounts
            if request.POST.get('personal_account'):
                personal_account = True
            else:
                personal_account = False

            insert_article = Analysis_articles(author=User.objects.get(username=request.user), title=form.cleaned_data.get('title'),
                                               thumbnail=form.cleaned_data.get('thumbnail'), content=form.cleaned_data.get('content'),
                                               endf_related=endf_related, personal_account = personal_account, approval=User.objects.get(username=request.user).is_superuser,
                                               draft = True)
            insert_article.save()

            messages.success(
                request, 'New analysis article saved to draft...')

        return render(request, 'admin_templates/analysis_article/write_article.html', context)

    else:
        return render(request, 'admin_templates/analysis_article/write_article.html', context)


@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Analysis_articles_management(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    analysis_articles = Analysis_articles.objects.filter(approval=True, draft=False)
    specfic_analysis_articles = Analysis_articles.objects.filter(
        author=request.user, draft = False)

    context = {
        'pending_count': pending_count,
        'analysis_articles': analysis_articles,
        'Administrator': Administrator.objects.get(user=request.user),
        'specfic_data': specfic_analysis_articles
    }

    return render(request, 'admin_templates/analysis_article/article_data_management.html', context)



@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Draft_articles_management(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    analysis_articles = Analysis_articles.objects.filter(author = request.user, draft=True)

    context = {
        'pending_count': pending_count,
        'analysis_articles': analysis_articles,
    }

    return render(request, 'admin_templates/analysis_article/draft_article_management.html', context)


class Update_Article_Analysis(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/analysis_article/update_analysis_article.html'
    model = Analysis_articles
    form_class = AnalysisArticleForm
    success_message = 'Analysis Article updated successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Analysis_articles, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('analysis-article-management')


class Update_Draft_Analysis(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/analysis_article/update_draft_article.html'
    model = Analysis_articles
    form_class = AnalysisArticleForm
    success_message = 'Draft Article updated successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Analysis_articles, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('analysis-article-management')
        
    def form_valid(self, form):
        if 'publish' in self.request.POST:  # Check if the "Publish" button was clicked
            instance = form.save(commit=False)
            instance.draft = False  # Set draft to False
            instance.save()
            return super().form_valid(form)
        else:
            return super().form_valid(form)


class Delete_Article_Analysis(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/analysis_article/delete_analysis_article.html'
    model = Analysis_articles
    success_message = 'Analysis Article deleted successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Analysis_articles, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('analysis-article-management')

@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Add_webinar_discussion(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    form = Webinar_discussion_Form()

    context = {
        'pending_count': pending_count,
        'webinar_form': form
    }

    if request.method == 'POST':
        form = Webinar_discussion_Form(request.POST, request.FILES)
        if form.is_valid():
            insert_webinar = Webinar(author=User.objects.get(username=request.user), webinar_title=form.cleaned_data.get('webinar_title'),
                                            webinar_content=form.cleaned_data.get('webinar_content'),
                                            webinar_video_url=form.cleaned_data.get('webinar_video_url'))
            insert_webinar.save()

            messages.success(
                request, 'New webinar discussion shared successfully...')

        return render(request, 'admin_templates/analysis_article/add_webinar_discussion.html', context)

    else:
        return render(request, 'admin_templates/analysis_article/add_webinar_discussion.html', context)

@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Webinar_discussion_management(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    webinar_discussion = Webinar.objects.all()

    context = {
        'pending_count': pending_count,
        'webinar_discussion': webinar_discussion
    }

    return render(request, 'admin_templates/analysis_article/webinar_data_management.html', context)


class Update_webinar_discussion(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/analysis_article/update_webinar_discussion.html'
    model = Webinar
    form_class = Webinar_discussion_Form
    success_message = 'Panel discussion updated successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Webinar, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('webinar-discussion-management')


class Delete_Webinar_discussion(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/analysis_article/delete_webinar_discussion.html'
    model = Webinar_discussion_Form
    success_message = 'Panel discussion deleted successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Webinar, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context 

    def get_success_url(self):

        return reverse('webinar-discussion-management')

@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Archive_create_photo(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    context = {
        'pending_count': pending_count,
        'Administrator': Administrator.objects.get(user=request.user),
        'woreda_list': Tigray_woreda.objects.all(),
    }

    if request.method == 'POST':

        archive_model = Photo_archive()
        archive_model.author = User.objects.get(username=request.user)
        archive_model.location = request.POST.get('archive_location')
        woreda_obj = Tigray_woreda.objects.get(woreda_name = request.POST.get('archive_woreda'))
        archive_model.woreda = woreda_obj
        archive_model.date_of_event = request.POST.get('archive_date_of_event') or None
        archive_model.description = request.POST.get('archive_description')
        archive_model.photo = request.FILES.get('archive_photo')
        if request.POST.get('is_graphic'):
            archive_model.graphic = True

        archive_model.save()

        messages.success(
            request, 'New photo archive shared successfully...')

        return render(request, 'admin_templates/archive_templates/add_photo_archive.html', context)

    else:
        return render(request, 'admin_templates/archive_templates/add_photo_archive.html', context)

@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Archive_manage_photo(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    photo_archive = Photo_archive.objects.all()

    context = {
        'pending_count': pending_count,
        'photo_archive': photo_archive,
        'Administrator': Administrator.objects.get(user=request.user)
    }

    return render(request, 'admin_templates/archive_templates/photo_archive_management.html', context)


class Update_photo_archive(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/archive_templates/update_photo_archive.html'
    model = Photo_archive
    form_class = Photo_Archive_Form
    success_message = 'Photo Archive updated successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Photo_archive, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('manage-photo-archive')


class Delete_photo_archive(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/archive_templates/delete_photo_archive.html'
    model = Photo_archive
    success_message = 'Photo Archive deleted successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Photo_archive, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('manage-photo-archive')

@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Archive_create_video(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    context = {
        'pending_count': pending_count,
        'Administrator': Administrator.objects.get(user=request.user),
        'woreda_list': Tigray_woreda.objects.all(),
    }

    if request.method == 'POST':

        archive_model = Video_archive()
        archive_model.author = User.objects.get(username=request.user)
        archive_model.location = request.POST.get('archive_location')
        woreda_obj = Tigray_woreda.objects.get(woreda_name = request.POST.get('archive_woreda'))
        archive_model.woreda = woreda_obj
        archive_model.date_of_event = request.POST.get('archive_date_of_event') or None
        archive_model.description = request.POST.get('archive_description')
        archive_model.online_link = request.POST.get('online_link')

        archive_model.save()

        messages.success(
            request, 'New Video archive shared successfully...')

        return render(request, 'admin_templates/archive_templates/add_video_archive.html', context)

    else:
        return render(request, 'admin_templates/archive_templates/add_video_archive.html', context)


@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Archive_manage_video(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    video_archive = Video_archive.objects.all()

    context = {
        'pending_count': pending_count,
        'video_archive': video_archive,
        'Administrator': Administrator.objects.get(user=request.user)
    }

    return render(request, 'admin_templates/archive_templates/video_archive_management.html', context)


class Update_video_archive(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/archive_templates/update_video_archive.html'
    model = Photo_archive
    form_class = Video_Archive_Form
    success_message = 'Video archive updated successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Video_archive, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('manage-video-archive')


class Delete_video_archive(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/archive_templates/delete_video_archive.html'
    model = Video_archive
    success_message = 'Video archive deleted successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Video_archive, id=id_)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('manage-video-archive')

@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Create_admin_account(request):

    # get available pending posts
    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    # generate random password for administrator
    ascii_alphabets = string.printable[:67]

    context = {
        'pending_count': pending_count,
        'Administrator': Administrator.objects.get(user=request.user)
    }

    administrator_model = Administrator()

    if request.method == 'POST':

        check_username = User.objects.filter(
            username=request.POST.get('admin_username'))

        if not check_username:

            
            random_andom_password = ''
            for i in range(0, 8):
                random_andom_password += random.choice(ascii_alphabets)

            first_name = request.POST.get('admin_first_name')
            last_name = request.POST.get('admin_last_name')
            email = request.POST.get('admin_email')
            username = request.POST.get('admin_username')
            password = make_password(random_andom_password)

            if request.POST.get('super_admin'):
                is_superuser = True
            else:
                is_superuser = False

            email_subject = "Your System Administration Account Created Successfully"
            email_body = '''
                <!DOCTYPE html
    PUBLIC "-//W3C//DTD XHTML 1.0 Transitional //EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office"
    xmlns:v="urn:schemas-microsoft-com:vml" lang="en">

<head>
    <link rel="stylesheet" type="text/css" hs-webfonts="true"
        href="https://fonts.googleapis.com/css?family=Lato|Lato:i,b,bi">
    <title>Email template</title>
    <meta property="og:title" content="Email template">

    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">

    <meta http-equiv="X-UA-Compatible" content="IE=edge">

    <meta name="viewport" content="width=device-width, initial-scale=1.0">


</head>

<body bgcolor="#F5F8FA"
    style="width: 100%; margin: auto 0; padding:0; font-family:Lato, sans-serif; font-size:18px; color:#33475B; word-break:break-word">

    <! View in Browser Link -->

        <div id="email" style="margin: auto;
        width: 600px;
        background-color: white;">
            <table align="right" role="presentation">
                <tr>
                    <td style="vertical-align: top;">
                        <a class="subtle-link" style="text-decoration: underline;
        color: inherit;
        font-weight: bold;
        color: #253342; font-size: 9px; 
        text-transform:uppercase; 
        letter-spacing: 1px;
        color: #CBD6E2;" href="#">View in Browser</a>
                    </td>
                <tr>
            </table>


            <! Banner -->
                <table role="presentation" width="100%">
                    <tr>

                        <td bgcolor="black" align="center" style="color: white;vertical-align: top;">

                            <h3><i>System Admin Account </h3>

                        </td>
                </table>




                <! First Row -->

                    <table role="presentation" border="0" cellpadding="0" cellspacing="10px"
                        style="padding: 30px 30px 30px 60px;">
                        <tr>
                            <td style="vertical-align: top;">
                                <p style="font-weight: 100;">
                                    Your system administration account has been created successfully.
                                </p>
                                <ul>
                                    <li>
                                        <p style="text-weight: normal; font-weight: 100;">🔐 Username: <b
                                                style="color: blue">{}</b></p>
                                    </li>
                                    <li>
                                        <p style="text-weight: normal; font-weight: 100;">🔐 Password: <b
                                                style="color: blue">{}</b></p>
                                    </li>

                                </ul>
                                <p>👉 You can change your username and password once you log in with this one.</p>
                                <br>
                                <div style="text-align: center">
                                    <a href="www.tigraygenocide.com/Adminstrator-login-page/">
                                        <button style="font: inherit;
        background-color: #FF7A59;
        border: none;
        padding: 10px;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 900; 
        color: white;
        border-radius: 5px; 
        box-shadow: 3px 3px #d94c53;">
                                        Sign in to your account.
                                    </button>
                                    </a>
                                </div>
                            </td>
                        </tr>
                    </table>

                    <! Banner Row -->
                        <table role="presentation" bgcolor="#EAF0F6" width="100%" style="margin-top: 50px;">
                            <tr>
                                <td align="center" style="padding: 30px 30px;">

                                    <h2 style="font-size: 28px;
        font-weight: 900; "> Tigray Genocide </h2>
                                    <p style="font-weight: 100; text-decoration: none">
                                        www.tigraygenocide.com

                                    </p>
                                </td>
                            </tr>
                        </table>

        </div>
</body>

</html>
            '''.format(username, random_andom_password)
            
            email_from = settings.EMAIL_HOST_USER
            email_to = [email]

            msg = EmailMessage(email_subject, email_body, email_from, email_to)
            msg.content_subtype = "html"  # Set the content type to HTML

            # Send the email
            msg.send()

            admin = User.objects.create(first_name=first_name, last_name=last_name,
                                        email=email, username=username, password=password, is_staff=is_superuser, is_superuser=is_superuser)

            admin.save()

            get_admin_obj = User.objects.get(username=username)

            # send account email to the user
            # get_admin_obj.email_user(
            #         'Your System Administration Account Created Successfully',
            #         f'<h5>Username: <span style="colore:red">{username}</span></h5><p>This is a paragraph.</p>',
            #         'eminemmerne@gmail.com'
            #     )
                
            # save admin permission

            administrator_model.user = get_admin_obj

            if request.POST.get('civilian_victim_role'):
                administrator_model.civilian_role = True
            if request.POST.get('analysis_article_role'):
                administrator_model.analysis_role = True

            administrator_model.save()

            messages.success(
                request, 'New admin account created successfully...')

        else:

            messages.error(
                request, 'Username available...')

        return render(request, 'admin_templates/account_templates/create_account.html', context)

    else:

        return render(request, 'admin_templates/account_templates/create_account.html', context)


@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Manage_admin_account(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    context = {
        'pending_count': pending_count,
        'is_notsuperuser': User.objects.filter(is_superuser=False, is_active=True)
    }

    return render(request, 'admin_templates/account_templates/account_management.html', context)

class Update_admin_permissions(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/account_templates/update_admin_permission.html'
    model = Administrator
    form_class = Administrator_form
    success_message = 'Account permission successfully changed'

    def get_object(self, *args, **kwargs):
        get_id = self.kwargs.get('admin_id')
        return get_object_or_404(Administrator, user=User.objects.get(id = get_id))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('manage-admin-account')
        
@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Deactivate_admin_account(request, admin_id):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    context = {
        'pending_count': pending_count,
    }

    user_model = User.objects.get(id = admin_id)

    if request.method == 'POST':
        user_model.is_active = False
        user_model.save()

        messages.success(request, 'Admin account removed successfully')

        return redirect('/Manage-admin-account/')

    return render(request, 'admin_templates/account_templates/deactivate_admin_account.html', context)

        
@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Pending_posts_management(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    pending_civilian_victims = Civilian_victims.objects.filter(approval=False)
    pending_analysis_articles = Analysis_articles.objects.filter(
        approval=False, draft=False)

    context = {
        'pending_count': pending_count,
        'pending_civilian_victims': pending_civilian_victims,
        'pending_analysis_articles': pending_analysis_articles
    }

    return render(request, 'admin_templates/pending_templates/pending.html', context)


class Approve_Civilian_Victim(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/pending_templates/approve_civilian_victim.html'
    model = Civilian_victims
    form_class = Approve_Civilian_Victim_Form
    success_message = 'Civilian victim informatiom approved successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Civilian_victims, id=id_, approval=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('pending-posts-management')


class Approve_Article_Analysis(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    redirect_field_name = '/authentication_required/'
    template_name = 'admin_templates/pending_templates/approve_analysis_articles.html'
    model = Analysis_articles
    form_class = Approve_Analysis_Form
    success_message = 'Analysis article approved successfully'

    def get_object(self, *args, **kwargs):
        id_ = self.kwargs.get('pk')
        return get_object_or_404(Analysis_articles, id=id_, approval=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['Administrator'] = Administrator.objects.get(
            user=self.request.user)
        context['pending_count'] = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()
        return context

    def get_success_url(self):

        return reverse('pending-posts-management')


@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Account_settings(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    current_user = User.objects.get(username = request.user.username)

    context = {
        'pending_count': pending_count,
        'Administrator': Administrator.objects.get(user=request.user),
        'webinar_password': Webmail_password_manager.objects.all().count()
    }

    if request.method == 'POST':
        current_user.first_name = request.POST['new_first_name']
        current_user.last_name = request.POST['new_last_name']
        current_user.username = request.POST['new_username']
        current_user.save()
        messages.success(request, 'Account Updated Successfully')

        return redirect('/Account-settings/')

    return render(request, 'admin_templates/admin_settings/settings.html', context)


@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Password_settings(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    current_user = User.objects.get(username = request.user.username)

    context = {
        'pending_count': pending_count,
        'Administrator': Administrator.objects.get(user=request.user)
    }

    if request.method == 'POST':
        is_valid_password = current_user.check_password(request.POST['old_password'])
        if is_valid_password:
            if request.POST['new_password'] == request.POST['confirm_new_password']:
                # Update the user's password
                current_user.set_password(request.POST['new_password'])
                current_user.save()
                messages.success(request, 'Password has been successfully changed')
            else:
                messages.error(request, 'New password and confirm password does not match')
        else:
            messages.error(request, 'Old password is not correct')

        return redirect('/Account-settings/')

    return render(request, 'admin_templates/admin_settings/settings.html', context)



@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Profile_picture_settings(request):

    pending_count = Civilian_victims.objects.filter(approval = False).count() + Analysis_articles.objects.filter(approval=False, draft=False).count()

    current_user = User.objects.get(username = request.user.username)
    current_admin_profile = Administrator.objects.get(user = current_user)

    context = {
        'pending_count': pending_count,
        'Administrator': Administrator.objects.get(user=request.user)
    }

    if request.method == 'POST':
        current_admin_profile.admin_photo = request.FILES.get('new_profile_picture')
        current_admin_profile.save()

        messages.success(request, 'Profile picture has been successfully changed')

        return redirect('/Account-settings/')

    return render(request, 'admin_templates/admin_settings/settings.html', context)



@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def Webmail_password_setting(request):

    if request.method == 'POST':
        
        if Webmail_password_manager.objects.all().count() > 0:
            get_first_row = Webmail_password_manager.objects.first()
            if get_first_row.password == request.POST.get("old_webmail_password"):
                if request.POST.get("new_webmail_password") == request.POST.get("confirm_webmail_password"):
                    get_first_row.password = request.POST.get("new_webmail_password")
                    get_first_row.save()
                    messages.success(request, 'Webmail password updated successfully!')
            
                    return redirect('/Account-settings/')
                else:
                    messages.error(request, 'New password doesn\'t match!')
            
                    return redirect('/Account-settings/')
                    
            else:
                messages.error(request, 'Old webinar password is not correct!')
        
                return redirect('/Account-settings/')
        else:
            Webmail_password_manager.objects.create(password = request.POST.get("new_webmail_password"))

            messages.success(request, 'Webmail password saved successfully!')
    
            return redirect('/Account-settings/')

    return render(request, 'admin_templates/admin_settings/settings.html', context)
    
# export database SQL backup
@login_required(login_url='/Adminstrator-login-page', redirect_field_name='authentication_required')
def export_database(request):
    # Database credentials
    db_name = settings.DATABASES['default']['NAME']
    db_user = settings.DATABASES['default']['USER']
    db_password = settings.DATABASES['default']['PASSWORD']

    # Get current date
    current_date = datetime.now().strftime('%m-%d-%Y')

    # Specify the file path where you want to save the SQL dump
    filename = f'database-Backup-{current_date}.sql'
    filepath = os.path.join(settings.BASE_DIR, filename)

    # Command to export MySQL database using mysqldump
    command = f"mysqldump -u {db_user} -p{db_password} {db_name} > {filepath}"

    try:
        # Execute the command
        subprocess.run(command, shell=True, check=True)
        with open(filepath, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/sql')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except subprocess.CalledProcessError as e:
        return HttpResponse(f"Error exporting database: {e}", status=500)
