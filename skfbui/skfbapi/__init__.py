"""
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 *
 * ***** END GPL LICENSE BLOCK *****
 """
from __future__ import division
import os
import json
import shutil
import tempfile
import requests
import urllib
from collections import OrderedDict
from PIL import Image
import time

from c4d.threading import C4DThread

class Config:
    # Plugin Specific
    __author__ = "Sketchfab"
    __website__ = "sketchfab.com"
    __sketchfab__ = "http://sketchfab.com"
    __email__ = "support@sketchfab.com"
    __plugin_title__ = "Sketchfab Plugin"

    PLUGIN_VERSION = "0.0.1"
    PLUGIN_ID = 1025251

    # sometimes the path in preferences is empty
    def get_temp_path():
        return tempfile.mkdtemp()

    ADDON_NAME = 'io_sketchfab'
    GITHUB_REPOSITORY_URL = 'https://github.com/sketchfab/glTF-Blender-IO'
    GITHUB_REPOSITORY_API_URL = 'https://api.github.com/repos/sketchfab/glTF-Blender-IO'
    SKETCHFAB_REPORT_URL = 'https://help.sketchfab.com/hc/en-us/requests/new?type=exporters&subject=Blender+Plugin'

    SKETCHFAB_URL = 'https://sketchfab.com'
    DUMMY_CLIENTID = 'ns2PeO9blbAPsJIsowUZRV8PvxCvGhBtaPjSZckv'
    SKETCHFAB_OAUTH = SKETCHFAB_URL + '/oauth2/token/?grant_type=password&client_id=' + DUMMY_CLIENTID
    SKETCHFAB_API = 'https://api.sketchfab.com'
    SKETCHFAB_SEARCH = SKETCHFAB_API + '/v3/search'
    SKETCHFAB_MODEL = SKETCHFAB_API + '/v3/models'
    SKETCHFAB_SIGNUP = 'https://sketchfab.com/signup'

    BASE_SEARCH = SKETCHFAB_SEARCH + '?type=models&downloadable=true'
    DEFAULT_FLAGS = '&staffpicked=true&sort_by=-staffpickedAt'
    DEFAULT_SEARCH = SKETCHFAB_SEARCH + \
                     '?type=models&downloadable=true' + DEFAULT_FLAGS

    SKETCHFAB_ME = '{}/v3/me'.format(SKETCHFAB_URL)

    SKETCHFAB_PLUGIN_VERSION = '{}/releases'.format(GITHUB_REPOSITORY_API_URL)
    # PATH management
    SKETCHFAB_TEMP_DIR = os.path.join(get_temp_path(), 'sketchfab_downloads')
    SKETCHFAB_THUMB_DIR = os.path.join(SKETCHFAB_TEMP_DIR, 'thumbnails')
    SKETCHFAB_MODEL_DIR = os.path.join(SKETCHFAB_TEMP_DIR, 'imports')

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

    MAX_THUMBNAIL_HEIGHT = 512
    UI_THUMBNAIL_RESOLUTION = 128
    MODEL_PLACEHOLDER_PATH = 'D:\\Softwares\\MAXON\\plugins\\ImportGLTF\\res\\model_placeholder.png'

class Utils:

    @staticmethod
    def humanify_size(size):
        suffix = 'B'
        readable = size

        # Megabyte
        if size > 1048576:
            suffix = 'MB'
            readable = size / 1048576.0
        # Kilobyte
        elif size > 1024:
            suffix = 'KB'
            readable = size / 1024.0

        readable = round(readable, 2)
        return '{}{}'.format(readable, suffix)
    @staticmethod
    def humanify_number(number):
        suffix = ''
        readable = number

        if number > 1000000:
            suffix = 'M'
            readable = number / 1000000.0

        elif number > 1000:
            suffix = 'K'
            readable = number / 1000.0

        readable = round(readable, 2)
        return '{}{}'.format(readable, suffix)

    @staticmethod
    def build_download_url(uid):
        return '{}/{}/download'.format(Config.SKETCHFAB_MODEL, uid)

    @staticmethod
    def thumbnail_file_exists(uid):
        return os.path.exists(os.path.join(Config.SKETCHFAB_THUMB_DIR, '{}.jpeg'.format(uid)))

    @staticmethod
    def clean_thumbnail_directory():
        if not os.path.exists(Config.SKETCHFAB_THUMB_DIR):
            return

        from os import listdir
        for file in listdir(Config.SKETCHFAB_THUMB_DIR):
            os.remove(os.path.join(Config.SKETCHFAB_THUMB_DIR, file))

    @staticmethod
    def clean_downloaded_model_dir(uid):
        shutil.rmtree(os.path.join(Config.SKETCHFAB_MODEL_DIR, uid))

    @staticmethod
    def get_thumbnail_url(thumbnails_json):
        best_height = 0
        best_thumbnail = None
        for image in thumbnails_json['images']:
            if image['height'] <= Config.MAX_THUMBNAIL_HEIGHT and image['height'] > best_height:
                best_height = image['height']
                best_thumbnail = image['url']

        return best_thumbnail

    @staticmethod
    def make_model_name(gltf_data):
        if 'title' in gltf_data.asset.extras:
            return gltf_data.asset.extras['title']

        return 'GLTFModel'
    @staticmethod
    def setup_plugin():
        if not os.path.exists(Config.SKETCHFAB_THUMB_DIR):
            os.makedirs(Config.SKETCHFAB_THUMB_DIR)
    @staticmethod
    def get_uid_from_thumbnail_url(thumbnail_url):
        return thumbnail_url.split('/')[4]

    @staticmethod
    def get_uid_from_model_url(model_url):
        return model_url.split('/')[5]
    @staticmethod
    def get_uid_from_download_url(model_url):
        return model_url.split('/')[6]


class Cache:
    SKETCHFAB_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".cache")

    def read():
        if not os.path.exists(Cache.SKETCHFAB_CACHE_FILE):
            return {}

        with open(Cache.SKETCHFAB_CACHE_FILE, 'rb') as f:
            data = f.read().decode('utf-8')
            return json.loads(data)

    def get_key(key):
        cache_data = Cache.read()
        if key in cache_data:
            return cache_data[key]

    def save_key(key, value):
        cache_data = Cache.read()
        cache_data[key] = value
        with open(Cache.SKETCHFAB_CACHE_FILE, 'wb+') as f:
            f.write(json.dumps(cache_data).encode('utf-8'))

    def delete_key(key):
        cache_data = Cache.read()
        if key in cache_data:
            del cache_data[key]

        with open(Cache.SKETCHFAB_CACHE_FILE, 'wb+') as f:
            f.write(json.dumps(cache_data).encode('utf-8'))

class SketchfabApi:
    def __init__(self):
        self.access_token = ''
        self.headers = {}
        self.display_name = ''
        self.plan_type = ''
        self.next_results_url = None
        self.prev_results_url = None
        self.import_callback = None
        self.request_callback = None
        self.search_results = {}

    def get_sketchfab_model(self, uid):
        if 'current' in self.search_results and uid in self.search_results['current']:
            return self.search_results['current'][uid]

        return None

    def parse_results(self, r, *args, **kwargs):
        json_data = r.json()

        if 'current' in self.search_results:
            self.search_results['current'].clear()
            del self.search_results['current']

        self.search_results['current'] = OrderedDict()

        for result in list(json_data['results']):

            # Dirty fix to avoid parsing obsolete data
            if 'current' not in self.search_results:
                return

            uid = result['uid']
            self.search_results['current'][result['uid']] = SketchfabModel(result)

            if not os.path.exists(os.path.join(Config.SKETCHFAB_THUMB_DIR, uid) + '.jpeg'):
                self.request_thumbnail(result['thumbnails'], self.handle_thumbnail)
            # elif uid not in skfb.custom_icons:
            #     self.custom_icons.load(uid, os.path.join(Config.SKETCHFAB_THUMB_DIR, "{}.jpeg".format(uid)), 'IMAGE')

        if json_data['next']:
            self.next_results_url = json_data['next']
        else:
            self.next_results_url = None

        if json_data['previous']:
            self.prev_results_url = json_data['previous']
        else:
            self.prev_results_url = None

        print("PARSED")
        if self.request_callback:
            self.request_callback()

    def handle_login(self, r, *args, **kwargs):
        if r.status_code == 200 and 'access_token' in r.json():
            self.access_token = r.json()['access_token']
            # Cache.save_key('username', login_props.email)
            # Cache.save_key('access_token', browser_props.skfb_api.access_token)

            self.build_headers()
            self.request_user_info()
            print("LOGGED")

        else:
            print('Cannot login.\n {}'.format(r.json()))

        self.is_logging = False
        self.request_callback()

    def login(self, email, password):
        url = '{}&username={}&password={}'.format(Config.SKETCHFAB_OAUTH, urllib.quote(email), urllib.quote(password))
        requests.post(url, hooks={'response': self.handle_login})

    def build_headers(self):
        self.headers = {'Authorization': 'Bearer ' + self.access_token}

    def is_user_logged(self):
        if self.access_token and self.headers:
            return True

        return False

    def logout(self):
        self.access_token = ''
        self.headers = {}
        Cache.delete_key('username')
        Cache.delete_key('access_token')
        Cache.delete_key('key')

    def request_user_info(self):
        requests.get(Config.SKETCHFAB_ME, headers=self.headers, hooks={'response': self.parse_user_info})

    def get_user_info(self):
        if self.display_name and self.plan_type:
            return 'as {} ({})'.format(self.display_name, self.plan_type)
        else:
            return ('', '')

    def parse_user_info(self, r, *args, **kargs):
        if r.status_code == 200:
            user_data = r.json()
            self.display_name = user_data['displayName']
            self.plan_type = user_data['account']
        else:
            print('Invalid access token')
            self.access_token = ''
            self.headers = {}

    def parse_login(self, r, *args, **kwargs):
        if r.status_code == 200 and 'access_token' in r.json():
            self.access_token = r.json()['access_token']
            self.build_headers()
            self.request_user_info()
        else:
            if 'error_description' in r.json():
                print("Failed to login: {}".format(r.json()['error_description']))
            else:
                print('Login failed.\n {}'.format(r.json()))

    def request_thumbnail(self, thumbnails_json, thumbnail_cb):
        url = Utils.get_thumbnail_url(thumbnails_json)
        requests.get(url, stream=True, hooks={'response': thumbnail_cb})

    def request_model_info(self, uid):
        url = Config.SKETCHFAB_MODEL + '/' + uid
        requests.get(url, hooks={'response': self.handle_model_info})

    def handle_model_info(self, r, *args, **kwargs):
        uid = Utils.get_uid_from_model_url(r.url)

        # Dirty fix to avoid processing obsolete result data
        if 'current' not in skfb.search_results or uid not in skfb.search_results['current']:
            return

        model = skfb.search_results['current'][uid]
        json_data = r.json()
        model.license = json_data['license']['fullName']
        anim_count = int(json_data['animationCount'])
        model.animated = 'Yes ({} animation(s))'.format(anim_count) if anim_count > 0 else 'No'
        skfb.search_results['current'][uid] = model

    def search(self, query):
        search_query = '{}{}'.format(Config.BASE_SEARCH, query)
        requests.get(query, hooks={'response': self.parse_results})

    def search_cursor(self, url, search_cb):
        requests.get(url, hooks={'response': search_cb})

    def download_model(self, uid):
        skfb_model = self.get_sketchfab_model(uid)
        if skfb_model.download_url:
            # Check url sanity
            if time.time() - skfb_model.time_url_requested < skfb_model.url_expires:
                self.get_archive(skfb_model.download_url)
            else:
                print("Download url is outdated, requesting a new one")
                skfb_model.download_url = None
                skfb_model.url_expires = None
                skfb_model.time_url_requested = None
                requests.get(Utils.build_download_url(uid), headers=self.headers, hooks={'response': self.handle_download})
        else:
            requests.get(Utils.build_download_url(uid), headers=self.headers, hooks={'response': self.handle_download})

    def handle_download(self, r, *args, **kwargs):
        if r.status_code != 200 or 'gltf' not in r.json():
            print('Download not available for this model')
            print(r)
            return

        uid = Utils.get_uid_from_model_url(r.url)

        gltf = r.json()['gltf']
        skfb_model = self.get_sketchfab_model(uid)
        skfb_model.download_url = gltf['url']
        skfb_model.time_url_requested = time.time()
        skfb_model.url_expires = gltf['expires']

        self.get_archive(gltf['url'])

    def handle_thumbnail(self, r, *args, **kwargs):
        return

        uid = r.url.split('/')[4]
        if uid not in self.search_results['current']:
            print("Thumbnail not found")
            return

        if not os.path.exists(Config.SKETCHFAB_THUMB_DIR):
            os.makedirs(Config.SKETCHFAB_THUMB_DIR)
        preview_path = os.path.join(Config.SKETCHFAB_THUMB_DIR, uid) + '.jpeg'

        with open(preview_path, "wb") as f:
            total_length = r.headers.get('content-length')

            if total_length is None and r.content:
                f.write(r.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in r.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)

        if not os.path.exists(preview_path):
            print("Thumbnail not found")
            return

        try:
            im = Image.open(preview_path)
        except IOError:
            print("FAILED to import thumbnail")
            return

        # Resize to UI_THUMBNAIL_RESOLUTION height and then crop UI_THUMBNAIL_RESOLUTION * UI_THUMBNAIL_RESOLUTION
        size = Config.UI_THUMBNAIL_RESOLUTION

        width, height = im.size
        factor = size / height

        width *= factor
        height *= factor
        im = im.resize((int(width), int(height)))

        left = (width - size)/2
        top = (height - size)/2
        right = (width + size)/2
        bottom = (height + size)/2

        im = im.crop((left, top, right, bottom))

        thumbnail_path = os.path.join(Config.SKETCHFAB_THUMB_DIR, uid) + '_thumb.jpeg'
        im.save(thumbnail_path, "JPEG")

        self.search_results['current'][uid].preview_path = preview_path
        self.search_results['current'][uid].thumbnail_path = thumbnail_path

    def get_archive(self, url):
        def unzip_archive(archive_path):
            if os.path.exists(archive_path):
                # set_import_status('Unzipping model')
                import zipfile
                try:
                    zip_ref = zipfile.ZipFile(archive_path, 'r')
                    extract_dir = os.path.dirname(archive_path)
                    zip_ref.extractall(extract_dir)
                    zip_ref.close()
                except zipfile.BadZipFile:
                    print('Error when dezipping file')
                    os.remove(archive_path)
                    print('Invaild zip. Try again')
                    return None, None

                gltf_file = os.path.join(extract_dir, 'scene.gltf')
                return gltf_file, archive_path

            else:
                print('ERROR: archive doesn\'t exist')

        if url is None:
            print('Url is None')
            return

        r = requests.get(url, stream=True)
        uid = Utils.get_uid_from_download_url(url)
        temp_dir = os.path.join(Config.SKETCHFAB_MODEL_DIR, uid)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        archive_path = os.path.join(temp_dir, '{}.zip'.format(uid))
        if not os.path.exists(archive_path):
            # wm = bpy.context.window_manager
            # wm.progress_begin(0, 100)
            # set_log("Downloading model..")
            with open(archive_path, "wb") as f:
                total_length = r.headers.get('content-length')
                if total_length is None:  # no content length header
                    f.write(r.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in r.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(100 * dl / total_length)
                        # wm.progress_update(done)
                        # set_log("Downloading model..{}%".format(done))

            # wm.progress_end()
        else:
            print('Model already downloaded')

        gltf_path, gltf_zip = unzip_archive(archive_path)
        print(gltf_path)
        if gltf_path:
            try:
                self.import_callback(gltf_path, uid)
            except Exception as e:
                import traceback
                print(traceback.format_exc())
        else:
            print("Failed to download model (url might be invalid)")
            model = self.get_sketchfab_model(uid)
            # set_import_status("Import model ({})".format(model.download_size if model.download_size else 'fetching data'))

class SketchfabModel:
    def __init__(self, json_data):
        self.title = json_data['name']
        self.author = json_data['user']['displayName']
        self.uid = json_data['uid']
        self.vertex_count = json_data['vertexCount']
        self.face_count = json_data['faceCount']
        self.thumbnail_path = Config.MODEL_PLACEHOLDER_PATH
        self.preview_path = Config.MODEL_PLACEHOLDER_PATH

        if 'archives' in json_data and  'gltf' in json_data['archives']:
            self.download_size = Utils.humanify_size(json_data['archives']['gltf']['size'])
        else:
            self.download_size = None

        self.thumbnail_url = os.path.join(Config.SKETCHFAB_THUMB_DIR, '{}.jpeg'.format(self.uid))


        # Model info request
        self.info_requested = False
        self.license = None
        self.animated = False

        # Download url data
        self.download_url = None
        self.time_url_requested = None
        self.url_expires = None

    def print_model(self):
        print(self.title)