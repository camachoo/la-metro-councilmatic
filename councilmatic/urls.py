from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.conf import settings

from haystack.query import SearchQuerySet

from councilmatic_core.views import CouncilmaticSearchForm, CouncilmaticFacetedSearchView, EventDetailView

from lametro.views import LABillDetail, LABoardMembersView, LAMetroAboutView, LACommitteeDetailView, LAPersonDetailView

sqs = SearchQuerySet().facet('bill_type')\
                      .facet('sponsorships', sort='index')\
                      .facet('controlling_body')\
                      .facet('inferred_status')\
                      .facet('topics')\
                      .facet('legislative_session')\
                      .highlight()

patterns = ([
    url(r'^admin/', include(admin.site.urls)),
    url(r'^search/', CouncilmaticFacetedSearchView(searchqueryset=sqs,
                                       form_class=CouncilmaticSearchForm), name='search'),
    url(r'^about/$', LAMetroAboutView.as_view(), name='about'),
    url(r'^legislation/(?P<slug>[^/]+)/$', LABillDetail.as_view(), name='bill_detail'),
    url(r'^committee/(?P<slug>[^/]+)/$', LACommitteeDetailView.as_view(), name='committee'),
    url(r'^board-members/$', LABoardMembersView.as_view(), name='council_members'),
    url(r'^person/(?P<slug>[^/]+)/$', LAPersonDetailView.as_view(), name='person'),
    url(r'^event/(?P<slug>[^/]+)/$', EventDetailView.as_view(), name='event'),
], settings.APP_NAME)

urlpatterns = [
    url(r'', include(patterns)),
    url(r'', include('councilmatic_core.urls')),
]
