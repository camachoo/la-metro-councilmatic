import re
from itertools import groupby
from operator import attrgetter
import itertools
import urllib
import json
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
import requests

from haystack.query import SearchQuerySet
from django.db import transaction, connection, connections
from django.conf import settings
from django.shortcuts import render
from django.db import connection
from django.db.models.functions import Lower
from django.db.models import Max, Min
from django.utils import timezone
from django.utils.text import slugify
from collections import namedtuple
from councilmatic_core.views import IndexView, BillDetailView, CouncilMembersView, AboutView, CommitteeDetailView, CommitteesView, PersonDetailView, EventDetailView, EventsView, CouncilmaticFacetedSearchView
from councilmatic_core.models import *
from lametro.models import LAMetroBill, LAMetroPost, LAMetroPerson, LAMetroEvent

from councilmatic.settings_jurisdiction import MEMBER_BIOS
from councilmatic.settings import MERGER_BASE_URL

class LAMetroIndexView(IndexView):
    template_name = 'lametro/index.html'

    event_model = LAMetroEvent

    def extra_context(self):
        extra = {}
        extra['upcoming_board_meeting'] = self.event_model.upcoming_board_meeting()
        extra['current_meeting'] = self.event_model.current_meeting()
        print(extra['current_meeting'])

        return extra

class LABillDetail(BillDetailView):
    model = LAMetroBill
    template_name = 'lametro/legislation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actions'] = self.get_object().actions.all().order_by('-order')
        context['attachments'] = self.get_object().attachments.all().order_by(Lower('note')).exclude(note="Board Report")

        context['board_report'] = self.get_object().attachments.get(note="Board Report")
        item = context['legislation']
        actions = Action.objects.filter(_bill_id=item.ocd_id)
        organization_lst = [action.organization for action in actions]
        context['sponsorships'] = set(organization_lst)

        # Create URL for packet download.
        packet_slug = item.ocd_id.replace('/', '-')
        try:
            r = requests.head(MERGER_BASE_URL + '/document/' + packet_slug)
            if r.status_code == 200:
                context['packet_url'] = MERGER_BASE_URL + '/document/' + packet_slug
        except:
            context['packet_url'] = None

        print(item.ocd_id)

        return context

class LAMetroEventDetail(EventDetailView):
    template_name = 'lametro/event.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Create URL for packet download.
        event = context['event']

        packet_slug = event.ocd_id.replace('/', '-')
        try:
            r = requests.head(MERGER_BASE_URL + '/document/' + packet_slug)
            if r.status_code == 200:
                context['packet_url'] = MERGER_BASE_URL + '/document/' + packet_slug
        except:
            context['packet_url'] = None

        return context

class LAMetroEventsView(EventsView):
    template_name = 'lametro/events.html'

    def get_context_data(self, **kwargs):
        context = super(LAMetroEventsView, self).get_context_data(**kwargs)


        # Did the user set date boundaries?
        start_date_str = self.request.GET.get('from')
        end_date_str   = self.request.GET.get('to')
        day_grouper    = lambda x: (x.start_time.year, x.start_time.month, x.start_time.day)

        # If yes...
        if start_date_str and end_date_str:
            context['start_date'] = start_date_str
            context['end_date']   = end_date_str
            start_date_time       = parser.parse(start_date_str)
            end_date_time         = parser.parse(end_date_str)

            select_events = Event.objects.filter(start_time__gt=start_date_time)\
                          .filter(start_time__lt=end_date_time)\
                          .order_by('start_time')

            org_select_events = []

            for event_date, events in itertools.groupby(select_events, key=day_grouper):
                events = sorted(events, key=attrgetter('start_time'))
                org_select_events.append([date(*event_date), events])

            context['select_events'] = org_select_events

        # Did the user set date boundaries?
        # date_str               = self.request.GET.get('form_datetime')
        # day_grouper            = lambda x: (x.start_time.year, x.start_time.month, x.start_time.day)
        # context['select_date'] = ''

        # # If yes: dates...
        # if date_str:
        #     context['date'] = date_str
        #     date_time       = parser.parse(date_str)

        #     select_events = Event.objects.filter(start_time__gt=date_time)\
        #                   .filter(start_time__lt=(date_time + relativedelta(months=1)))\
        #                   .order_by('start_time')

        #     org_select_events = []

        #     for event_date, events in itertools.groupby(select_events, key=day_grouper):
        #         events = sorted(events, key=attrgetter('start_time'))
        #         org_select_events.append([date(*event_date), events])

        #     context['select_events'] = org_select_events
        #     context['select_date']   = date_time.strftime("%B") + " " + date_time.strftime("%Y")

        # If all meetings
        elif self.request.GET.get('show'):
            all_events = Event.objects.all().order_by('-start_time')

            org_all_events = []

            for event_date, events in itertools.groupby(all_events, key=day_grouper):
                events = sorted(events, key=attrgetter('start_time'))
                org_all_events.append([date(*event_date), events])

            context['all_events'] = org_all_events
        # If no...
        else:
            # Upcoming events for the current month.
            future_events = Event.objects.filter(start_time__gt=timezone.now())\
                  .filter(start_time__lt=datetime(timezone.now().year, timezone.now().month+1, 1))\
                  .order_by('start_time')

            if not future_events:
                # Upcoming events for the next month.
                future_events = Event.objects.filter(start_time__gt=timezone.now())\
                      .filter(start_time__lt=datetime(timezone.now().year, timezone.now().month+2, 1))\
                      .order_by('start_time')

            org_future_events = []

            for event_date, events in itertools.groupby(future_events, key=day_grouper):
                events = sorted(events, key=attrgetter('start_time'))
                org_future_events.append([date(*event_date), events])

            context['future_events'] = org_future_events

            # Past events
            past_events = Event.objects.filter(start_time__lt=datetime.now(app_timezone))\
                          .order_by('-start_time')

            org_past_events = []

            for event_date, events in itertools.groupby(past_events, key=day_grouper):
                events = sorted(events, key=attrgetter('start_time'))
                org_past_events.append([date(*event_date), events])

            org_past_events

            context['past_events'] = org_past_events

        context['user_subscribed'] = False
        if self.request.user.is_authenticated():
            user = self.request.user
            context['user'] = user

            if settings.USING_NOTIFICATIONS:
                if (len(user.eventssubscriptions.all()) > 0):
                    context['user_subscribed'] = True

        return context

class LABoardMembersView(CouncilMembersView):
    template_name = 'lametro/board_members.html'

    model = LAMetroPost

    def get_queryset(self):
        posts = LAMetroPost.objects.filter(_organization__ocd_id=settings.OCD_CITY_COUNCIL_ID)

        return posts

    def get_context_data(self, *args, **kwargs):
        context = super(LABoardMembersView, self).get_context_data(**kwargs)
        context['seo'] = self.get_seo_blob()

        context['map_geojson'] = None

        if settings.MAP_CONFIG:

            map_geojson = {
                            'type': 'FeatureCollection',
                            'features': []
                          }

            map_geojson_sectors = {
                                    'type': 'FeatureCollection',
                                    'features': []
                                  }

            map_geojson_city = {
                                 'type': 'FeatureCollection',
                                 'features': []
                               }

            for post in self.object_list:
                if post.shape:
                    council_member = "Vacant"
                    detail_link = ""
                    if post.current_members:
                        for membership in post.current_members:
                            council_member = membership.person.name
                            detail_link = membership.person.slug

                    feature = {
                        'type': 'Feature',
                        'geometry': json.loads(post.shape),
                        'properties': {
                            'district': post.label,
                            'council_member': council_member,
                            'detail_link': '/person/' + detail_link,
                            'select_id': 'polygon-{}'.format(slugify(post.label)),
                        },
                    }

                    if 'council_district' in post.division_ocd_id:
                        map_geojson['features'].append(feature)

                    if 'la_metro_sector' in post.division_ocd_id:
                        map_geojson_sectors['features'].append(feature)

                    if post.division_ocd_id == 'ocd-division/country:us/state:ca/place:los_angeles':
                        map_geojson_city['features'].append(feature)

            context['map_geojson'] = json.dumps(map_geojson)
            context['map_geojson_sectors'] = json.dumps(map_geojson_sectors)
            context['map_geojson_city'] = json.dumps(map_geojson_city)


        with connection.cursor() as cursor:
            today = timezone.now().date()

            sql = '''
            SELECT p.ocd_id, p.name, array_agg(pt.label) as label,
                array_agg(m.role) as role,
                split_part(p.name, ' ', 2) AS last_name
            FROM councilmatic_core_membership as m
            INNER JOIN councilmatic_core_post as pt
            ON pt.ocd_id=m.post_id
            INNER JOIN councilmatic_core_person as p
            ON m.person_id=p.ocd_id
            WHERE m.organization_id='ocd-organization/42e23f04-de78-436a-bec5-ab240c1b977c'
            AND m.end_date >= '{0}'
            GROUP BY p.ocd_id, p.name
            ORDER BY last_name
            '''.format(today)

            cursor.execute(sql)

            columns = [c[0] for c in cursor.description]
            columns.append('index')
            cursor_copy = []

            # from operator import itemgetter
            for obj in cursor:
                if '1st Vice Chair' in obj[3]:
                    obj = obj + ("2",)
                elif '2nd Vice Chair' in obj[3]:
                    obj = obj + ("3",)
                elif 'Chair' in obj[3]:
                    obj = obj + ("1",)
                elif 'Nonvoting Board Member' in obj[3]:
                    obj = obj + ("5",)
                else:
                    obj = obj + ("4",)
                cursor_copy.append(obj)

            # Create tuple-like object...iterable and accessible by field names.
            membership_tuple = namedtuple('Membership', columns)
            membership_objects = [membership_tuple(*r) for r in cursor_copy]

            membership_objects = sorted(membership_objects, key=lambda x: x[5])

            context['membership_objects'] = membership_objects

            board = Organization.objects.get(ocd_id='ocd-organization/42e23f04-de78-436a-bec5-ab240c1b977c')
            context['recent_activity'] = board.actions.order_by('-date', '-_bill__identifier', '-order')
            context['recent_events'] = board.recent_events

        return context


class LAMetroAboutView(AboutView):
    template_name = 'lametro/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['timestamp'] = datetime.now(app_timezone).strftime('%m%d%Y%s')

        return context


class LACommitteesView(CommitteesView):
    template_name = 'lametro/committees.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        with connection.cursor() as cursor:

            sql = ('''
              SELECT DISTINCT on (o.ocd_id, m.person_id) o.*, m.person_id, m.role, p.name
              FROM councilmatic_core_organization AS o
              JOIN councilmatic_core_membership AS m
              ON o.ocd_id=m.organization_id
              JOIN councilmatic_core_person as p
              ON p.ocd_id=m.person_id
              WHERE o.classification='committee'
              AND m.end_date::date > NOW()::date
              ORDER BY o.ocd_id, m.person_id, m.end_date;
                ''')

            cursor.execute(sql)

            columns           = [c[0] for c in cursor.description]
            committees_tuple  = namedtuple('Committee', columns, rename=True)
            data              = [committees_tuple(*r) for r in cursor]
            groups            = []

            for key, group in groupby(data, lambda x: x[1]):
                groups.append(list(group))

            committees_list = groups
            context["committees_list"] = committees_list

        return context

class LACommitteeDetailView(CommitteeDetailView):

    template_name = 'lametro/committee.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        committee = context['committee']

        if getattr(settings, 'COMMITTEE_DESCRIPTIONS', None):
            description = settings.COMMITTEE_DESCRIPTIONS.get(committee.slug)
            context['committee_description'] = description

        with connection.cursor() as cursor:
            sql = ('''
              SELECT
                p.name, p.slug, p.ocd_id,
                array_agg(m.role) as committee_role,
                array_agg(mm.label::VARCHAR)
                FILTER (WHERE mm.label is not Null) as label,
                split_part(p.name, ' ', 2) AS last_name
              FROM councilmatic_core_membership AS m
              LEFT JOIN (
                SELECT
                  person_id,
                  array_agg(DISTINCT pt.label) as label
                FROM councilmatic_core_membership AS m
                JOIN councilmatic_core_post AS pt
                  ON m.post_id=pt.ocd_id
                WHERE m.organization_id = %s
                GROUP BY person_id
              ) AS mm
                USING(person_id)
              JOIN councilmatic_core_person AS p
                ON m.person_id = p.ocd_id
              WHERE m.organization_id = %s
              AND m.end_date::date > NOW()::date
              GROUP BY
                p.name, p.slug, p.ocd_id
              ORDER BY last_name
            ''')

            cursor.execute(sql, [settings.OCD_CITY_COUNCIL_ID, committee.ocd_id])

            columns = [c[0] for c in cursor.description]
            columns.append('index')
            cursor_copy = []

            for obj in cursor:
                if 'Chair' in obj[3]:
                    obj = obj + ("1",)
                elif '1st Vice Chair' in obj[3] or 'Vice Chair' in obj[3]:
                    obj = obj + ("2",)
                elif '2nd Vice Chair' in obj[3]:
                    obj = obj + ("3",)
                elif 'Nonvoting Member' in obj[3]:
                    obj = obj + ("5",)
                else:
                    obj = obj + ("4",)
                cursor_copy.append(obj)

            results_tuple      = namedtuple('Member', columns)
            objects_list       = [results_tuple(*r) for r in cursor_copy]
            membership_objects = sorted(objects_list, key=lambda x: x[5])

            context['membership_objects'] = objects_list

            sql = ('''
              SELECT
                p.name, p.slug, p.ocd_id,
                array_agg(m.role) as committee_role,
                array_agg(mm.label::VARCHAR)
                FILTER (WHERE mm.label is not Null) as label,
                split_part(p.name, ' ', 2) AS last_name
              FROM councilmatic_core_membership AS m
              LEFT JOIN (
                SELECT
                  person_id,
                  array_agg(DISTINCT pt.label) as label
                FROM councilmatic_core_membership AS m
                JOIN councilmatic_core_post AS pt
                  ON m.post_id=pt.ocd_id
                WHERE m.organization_id = %s
                GROUP BY person_id
              ) AS mm
                USING(person_id)
              JOIN councilmatic_core_person AS p
                ON m.person_id = p.ocd_id
              WHERE m.organization_id = %s
              AND m.end_date::date > NOW()::date
              GROUP BY
                p.name, p.slug, p.ocd_id
              ORDER BY last_name
            ''')

            cursor.execute(sql, [settings.OCD_CITY_COUNCIL_ID, committee.ocd_id])

            columns = [c[0] for c in cursor.description]
            columns.append('index')
            cursor_copy = []

            for obj in cursor:
                if 'Chair' in obj[3]:
                    obj = obj + ("1",)
                elif '1st Vice Chair' in obj[3] or 'Vice Chair' in obj[3]:
                    obj = obj + ("2",)
                elif '2nd Vice Chair' in obj[3]:
                    obj = obj + ("3",)
                else:
                    obj = obj + ("4",)
                cursor_copy.append(obj)

            results_tuple      = namedtuple('Member', columns)
            objects_list       = [results_tuple(*r) for r in cursor_copy]
            membership_objects = sorted(objects_list, key=lambda x: x[5])

            context['ad_hoc_list'] = objects_list

        return context

class LAPersonDetailView(PersonDetailView):

    template_name = 'lametro/person.html'
    model = LAMetroPerson

    def get_context_data(self, **kwargs):
        post_model = LAMetroPost

        context = super().get_context_data(**kwargs)
        person = context['person']

        title = ''
        qualifying_post = '' # board membership criteria met by person in question
        m = person.latest_council_membership
        if person.current_council_seat:
            title = m.role
            if m.post:
                qualifying_post = m.post.label

        else:
            title = 'Former %s' % m.role
        context['title'] = title
        context['qualifying_post'] = qualifying_post

        if person.committee_sponsorships:
            context['sponsored_legislation'] = [
                s.bill for s in sorted(person.committee_sponsorships, key=lambda obj: obj.date, reverse=True)[:10]
            ]
        else:
            context['sponsored_legislation'] = []

        committees_lst = [action._organization.name for action in person.committee_sponsorships]
        context['committees_lst'] = list(set(committees_lst))

        if person.slug in MEMBER_BIOS:
            context['member_bio'] = MEMBER_BIOS[person.slug]

        return context


class LAMetroCouncilmaticFacetedSearchView(CouncilmaticFacetedSearchView):

    def build_form(self, form_kwargs=None):
        form = super(CouncilmaticFacetedSearchView, self).build_form(form_kwargs=form_kwargs)

        # For faceted search functionality.
        if form_kwargs is None:
            form_kwargs = {}

        form_kwargs['selected_facets'] = self.request.GET.getlist("selected_facets")

        # For remaining search functionality.
        data = None
        kwargs = {
            'load_all': self.load_all,
        }

        sqs = SearchQuerySet().facet('bill_type', sort='index')\
                      .facet('sponsorships', sort='index')\
                      .facet('inferred_status')\
                      .facet('topics')\
                      .facet('legislative_session', sort='index')\
                      .highlight()\

        if form_kwargs:
            kwargs.update(form_kwargs)

        if len(self.request.GET):
            data = self.request.GET
            dataDict = dict(data)

        if self.searchqueryset is not None:
            kwargs['searchqueryset'] = sqs

            try:
                for el in dataDict['sort_by']:
                    # Do this, because sometimes the 'el' may include a '?' from the URL
                    if 'date' in el:
                        try:
                            dataDict['ascending']
                            kwargs['searchqueryset'] = sqs.order_by('last_action_date')
                        except:
                            kwargs['searchqueryset'] = sqs.order_by('-last_action_date')
                    if 'title' in el:
                        try:
                            dataDict['descending']
                            # kwargs['searchqueryset'] = sqs.order_by('-identifier')
                            kwargs['searchqueryset'] = sqs.order_by('-sort_name')
                        except:
                            # kwargs['searchqueryset'] = sqs.order_by('identifier')
                            kwargs['searchqueryset'] = sqs.order_by('sort_name')
                    if 'relevance' in el:
                        kwargs['searchqueryset'] = sqs

            except:
                kwargs['searchqueryset'] = sqs.order_by('-last_action_date')

        return self.form_class(data, **kwargs)


class GoogleView(IndexView):
    template_name = 'lametro/google66b34bb6957ad66c.html'
