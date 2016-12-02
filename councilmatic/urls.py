from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.conf import settings

from haystack.query import SearchQuerySet, EmptySearchQuerySet

from councilmatic_core.views import CouncilmaticSearchForm, CouncilmaticFacetedSearchView, EventDetailView
from councilmatic_core.feeds import CouncilmaticFacetedSearchFeed
from lametro.views import LAMetroIndexView, LABillDetail, LABoardMembersView, \
    LAMetroAboutView, LACommitteeDetailView, LACommitteesView, LAPersonDetailView, LAMetroCouncilmaticFacetedSearchView
from lametro.feeds import *

patterns = ([
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/rss/',
        CouncilmaticFacetedSearchFeed(), name='councilmatic_search_feed'),
    url(r'^search/', LAMetroCouncilmaticFacetedSearchView(searchqueryset=EmptySearchQuerySet,
                                       form_class=CouncilmaticSearchForm), name='search'),
    url(r'^$', LAMetroIndexView.as_view(), name='index'),
    url(r'^about/$', LAMetroAboutView.as_view(), name='about'),
    url(r'^board-report/(?P<slug>[^/]+)/$', LABillDetail.as_view(), name='bill_detail'),
    url(r'^committees/$', LACommitteesView.as_view(), name='committees'),
    url(r'^committee/(?P<slug>[^/]+)/$', LACommitteeDetailView.as_view(), name='committee'),
    url(r'^board-members/$', LABoardMembersView.as_view(), name='council_members'),
    url(r'^person/(?P<slug>[^/]+)/$', LAPersonDetailView.as_view(), name='person'),
    url(r'^event/(?P<slug>[^/]+)/$', EventDetailView.as_view(), name='event'),
    url(r'^person/(?P<slug>[^/]+)/rss/$', LAMetroPersonDetailFeed(), name='person_feed'),
], settings.APP_NAME)

urlpatterns = [
    url(r'', include(patterns)),
    url(r'', include('councilmatic_core.urls')),
]
