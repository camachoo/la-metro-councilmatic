import os


SECRET_KEY = 'sweet bird most musical most melancholy'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'haystack',
    'lametro',
    'councilmatic_core',
    'adv_cache_tag',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lametro',
        'USER': 'postgres',
        'PASSWORD': '',
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': 5432,
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.solr_backend.SolrEngine',
        'URL': 'http://127.0.0.1:8983/solr',
    },
}

OCD_CITY_COUNCIL_ID = 'ocd-organization/42e23f04-de78-436a-bec5-ab240c1b977c'

CITY_COUNCIL_NAME = 'Metro'

APP_NAME = 'lametro'

ROOT_URLCONF = 'councilmatic.urls'
STATIC_URL = '/static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'councilmatic_core.views.city_context',
            ],
        },
    },
]

SITE_META = {
    'site_name' : 'Metro Board',
    'site_desc' : '', 
    'site_author' : '', 
    'site_url' : '',
    'twitter_site': '',    
    'twitter_creator': '', 
}

USING_NOTIFICATIONS = False

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

TIME_ZONE = 'America/Los_Angeles'

MAP_CONFIG = False

CITY_VOCAB = {
    'MUNICIPAL_DISTRICT': 'District',       # e.g. 'District'
    'SOURCE': 'Metro',
    'COUNCIL_MEMBER': 'Board Member',       # e.g. 'Council Member'
    'COUNCIL_MEMBERS': 'Board of Directors',      # e.g. 'Council Members'
    'EVENTS': 'Meetings',               # label for the events listing, e.g. 'Events'
}

SHOW_TEST_EVENTS = True
