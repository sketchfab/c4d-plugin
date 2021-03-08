# Copyright(c) 2017-2019 Sketchfab Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import tempfile
import c4d
from c4d import storage

class Config:

    PLUGIN_VERSION = "1.4.0"
    PLUGIN_TITLE   = "Sketchfab Plugin"
    PLUGIN_AUTHOR  = "Sketchfab"
    PLUGIN_TWITTER = "@sketchfab"
    PLUGIN_EMAIL   = "support@sketchfab.com"
    IMPORTER_ID    = 1052778
    IMPORTER_TITLE = "Sketchfab Importer"
    IMPORTER_HELP  = "Import a model from Sketchfab"
    EXPORTER_ID    = 1029390
    EXPORTER_TITLE = "Sketchfab Exporter"
    EXPORTER_HELP  = "Export a model to Sketchfab"

    PLUGIN_DIRECTORY = os.path.dirname(os.path.dirname(__file__))
    MODEL_PLACEHOLDER_PATH = os.path.join(PLUGIN_DIRECTORY, 'res', 'modelPlaceholder.png')

    MAX_THUMBNAIL_HEIGHT = 512
    UI_PREVIEW_RESOLUTION = (512, 288)
    UI_THUMBNAIL_RESOLUTION = 128

    # sometimes the path in preferences is empty
    def get_temp_path():
        return c4d.storage.GeGetStartupWritePath()

    GITHUB_REPOSITORY_URL = 'https://github.com/sketchfab/c4d-plugin'
    PLUGIN_LATEST_RELEASE = GITHUB_REPOSITORY_URL + '/releases/latest'

    GITHUB_REPOSITORY_API_URL = 'https://api.github.com/repos/sketchfab/c4d-plugin'

    SKETCHFAB_URL = 'https://sketchfab.com'
    DUMMY_CLIENTID = 'ns2PeO9blbAPsJIsowUZRV8PvxCvGhBtaPjSZckv'
    SKETCHFAB_OAUTH = SKETCHFAB_URL + '/oauth2/token/?grant_type=password&client_id=' + DUMMY_CLIENTID
    SKETCHFAB_API = 'https://api.sketchfab.com'
    SKETCHFAB_SEARCH = SKETCHFAB_API + '/v3/search?type=models&downloadable=true'
    SKETCHFAB_MODEL = SKETCHFAB_API + '/v3/models'
    SKETCHFAB_ORGS = SKETCHFAB_API + '/v3/orgs'
    SKETCHFAB_OWN_MODELS_SEARCH = SKETCHFAB_API + '/v3/me/search?type=models&downloadable=true'
    SKETCHFAB_PLANS = 'https://sketchfab.com/plans?utm_source=c4d-plugin&utm_medium=plugin&utm_campaign=download-api-pro-cta'
    SKETCHFAB_STORE = 'https://sketchfab.com/store?utm_source=c4d-plugin&utm_medium=plugin&utm_campaign=store-cta'
    SKETCHFAB_REPORT_URL = 'https://help.sketchfab.com/hc/en-us/requests/new?type=exporters&subject=Cinema4D+Plugin'
    SKETCHFAB_SIGNUP = 'https://sketchfab.com/signup'

    DEFAULT_FLAGS = '&staffpicked=true&sort_by=-publishedAt&min_face_count=1'
    DEFAULT_SEARCH = SKETCHFAB_SEARCH + \
                     '?type=models&downloadable=true' + DEFAULT_FLAGS

    SKETCHFAB_ME = '{}/v3/me'.format(SKETCHFAB_URL)
    SKETCHFAB_PLUGIN_VERSION = '{}/releases'.format(GITHUB_REPOSITORY_API_URL)

    # PATH management
    SKETCHFAB_TEMP_DIR = os.path.join(get_temp_path(), 'sketchfab_cache')
    SKETCHFAB_THUMB_DIR = os.path.join(SKETCHFAB_TEMP_DIR, 'thumbnails')
    SKETCHFAB_MODEL_DIR = os.path.join(SKETCHFAB_TEMP_DIR, 'imports')
    SKETCHFAB_CACHE_FILE = os.path.join(SKETCHFAB_TEMP_DIR, '.sketchfab')

    SKETCHFAB_SEARCH_DOMAINS = (('/search?type=models&downloadable=true', 'All site', 'All site'),
                                ('/me/search?type=models&downloadable=true', 'My models (PRO)', 'My models (PRO)'),
                                ('/me/models/purchases?', 'Store purchases', 'Store purchases'))

    SKETCHFAB_CATEGORIES = (('ALL', 'All categories', 'All categories'),
                            ('animals-pets', 'Animals & Pets', 'Animals and Pets'),
                            ('architecture', 'Architecture', 'Architecture'),
                            ('art-abstract', 'Art & Abstract', 'Art & Abstract'),
                            ('cars-vehicles', 'Cars & vehicles', 'Cars & vehicles'),
                            ('characters-creatures', 'Characters & Creatures', 'Characters & Creatures'),
                            ('cultural-heritage-history', 'Cultural Heritage & History', 'Cultural Heritage & History'),
                            ('electronics-gadgets', 'Electronics & Gadgets', 'Electronics & Gadgets'),
                            ('fashion-style', 'Fashion & Style', 'Fashion & Style'),
                            ('food-drink', 'Food & Drink', 'Food & Drink'),
                            ('furniture-home', 'Furniture & Home', 'Furniture & Home'),
                            ('music', 'Music', 'Music'),
                            ('nature-plants', 'Nature & Plants', 'Nature & Plants'),
                            ('news-politics', 'News & Politics', 'News & Politics'),
                            ('people', 'People', 'People'),
                            ('places-travel', 'Places & Travel', 'Places & Travel'),
                            ('science-technology', 'Science & Technology', 'Science & Technology'),
                            ('sports-fitness', 'Sports & Fitness', 'Sports & Fitness'),
                            ('weapons-military', 'Weapons & Military', 'Weapons & Military'))

    SKETCHFAB_FACECOUNT = (('ANY', "All", ""),
                           ('10K', "Up to 10k", ""),
                           ('50K', "10k to 50k", ""),
                           ('100K', "50k to 100k", ""),
                           ('250K', "100k to 250k", ""),
                           ('250KP', "250k +", ""))

    SKETCHFAB_SORT_BY = (('RELEVANCE', "Relevance", ""),
                         ('LIKES', "Likes", ""),
                         ('VIEWS', "Views", ""),
                         ('RECENT', "Recent", ""))


