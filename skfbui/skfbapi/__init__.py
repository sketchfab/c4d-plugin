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

# from gltfio.imp.gltf2_io_gltf import glTFImporter
# from gltfio.imp.gltf2_io_binary import BinaryData
from start import ImportGLTF

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
    GITHUB_REPOSITORY_URL = 'https://github.com/sketchfab/c4d-plugin'
    PLUGIN_LATEST_RELEASE = 'https://github.com/sketchfab/c4d-plugin/releases/latest'
    GITHUB_REPOSITORY_API_URL = 'https://api.github.com/repos/sketchfab/c4d-plugin'
    SKETCHFAB_REPORT_URL = 'https://help.sketchfab.com/hc/en-us/requests/new?type=exporters&subject=Cinema4D+Plugin'

    SKETCHFAB_URL = 'https://sketchfab.com'
    DUMMY_CLIENTID = 'ns2PeO9blbAPsJIsowUZRV8PvxCvGhBtaPjSZckv'
    SKETCHFAB_OAUTH = SKETCHFAB_URL + '/oauth2/token/?grant_type=password&client_id=' + DUMMY_CLIENTID
    SKETCHFAB_API = 'https://api.sketchfab.com'
    SKETCHFAB_SEARCH = SKETCHFAB_API + '/v3/search?type=models&downloadable=true'
    SKETCHFAB_MODEL = SKETCHFAB_API + '/v3/models'
    SKETCHFAB_OWN_MODELS_SEARCH = SKETCHFAB_API + '/v3/me/search?type=models&downloadable=true'
    SKETCHFAB_SIGNUP = 'https://sketchfab.com/signup'
    SKETCHFAB_PLANS = 'https://sketchfab.com/plans?utm_source=c4d-plugin&utm_medium=plugin&utm_campaign=download-api-pro-cta'

    DEFAULT_FLAGS = '&staffpicked=true&sort_by=-publishedAt'
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
    UI_PREVIEW_RESOLUTION = (512, 288)
    UI_THUMBNAIL_RESOLUTION = 128
    MODEL_PLACEHOLDER_PATH = 'D:\\Softwares\\MAXON\\Cinema4DR20\\plugins\\ImportGLTF\\res\\modelPlaceholder.png'

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
        path = Utils.build_thumbnail_path(uid)
        return os.path.exists(path)

    @staticmethod
    def build_thumbnail_path(uid, is_thumbnail=False):
        if is_thumbnail:
            uid = uid + '_thumb'

        return os.path.join(Config.SKETCHFAB_THUMB_DIR, '{}.jpeg'.format(uid))

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
    @staticmethod
    def read():
        if not os.path.exists(Cache.SKETCHFAB_CACHE_FILE):
            return {}

        with open(Cache.SKETCHFAB_CACHE_FILE, 'rb') as f:
            data = f.read().decode('utf-8')
            return json.loads(data)

    @staticmethod
    def get_key(key):
        cache_data = Cache.read()
        if key in cache_data:
            return cache_data[key]

        return ''

    @staticmethod
    def save_key(key, value):
        cache_data = Cache.read()
        cache_data[key] = value
        with open(Cache.SKETCHFAB_CACHE_FILE, 'wb+') as f:
            f.write(json.dumps(cache_data).encode('utf-8'))

    @staticmethod
    def delete_key(key):
        cache_data = Cache.read()
        if key in cache_data:
            del cache_data[key]

        with open(Cache.SKETCHFAB_CACHE_FILE, 'wb+') as f:
            f.write(json.dumps(cache_data).encode('utf-8'))


class ThreadedRequest(C4DThread):
    def __init__(self, url, headers, callback=None):
        C4DThread.__init__(self)
        self.url = url
        self.headers = headers if headers else {}
        self.callback = callback

    def Main(self):
        requests.get(self.url, headers=self.headers, hooks={'response': self.callback})


class SketchfabApi:
    def __init__(self):
        self.email = ''
        self.access_token = ''
        self.headers = {}
        self.display_name = ''
        self.plan_type = ''
        self.is_user_pro = False
        self.next_results_url = None
        self.prev_results_url = None

        self.latest_release_version = None
        self.search_results = {}
        self.threads = []

        self.version_callback = None
        self.login_callback = None
        self.import_callback = None
        self.request_callback = None
        self.msgbox_callback = None

    def parse_plugin_version(self, request, *args, **kwargs):
        response = request.json()
        if response and len(response):
            if 'tag_name' in response:
                latest_release_version = response['tag_name']
                current_version = str(bl_info['version']).replace(',', '').replace('(', '').replace(')', '').replace(' ', '')

                if latest_release_version == current_version:
                    print('You are using the latest version({})'.format(response[0]['tag_name']))
                else:
                    print('A new version is available: {}'.format(response[0]['tag_name']))

                return

        print('Failed to retrieve plugin version')
        self.latest_release_version = -1

        if self.version_callback:
            self.version_callback()

    def connect_to_sketchfab(self):
        self.check_plugin_version()
        self.check_user_logged()
        self.request_user_info()

    def check_plugin_version(self):
        requests.get(Config.SKETCHFAB_PLUGIN_VERSION, hooks={'response': self.parse_plugin_version})

    def request_user_info(self):
        requests.get(Config.SKETCHFAB_ME, headers=self.headers, hooks={'response': self.parse_user_info})

    def get_sketchfab_model(self, uid):
        if 'current' in self.search_results and uid in self.search_results['current']:
            return self.search_results['current'][uid]

        return None

    def handle_login(self, r, *args, **kwargs):
        if r.status_code == 200 and 'access_token' in r.json():
            self.access_token = r.json()['access_token']
            Cache.save_key('username', self.email)
            Cache.save_key('access_token', self.access_token)

            self.build_headers()
            self.request_user_info()

        else:
            print('Cannot login.\n{}'.format(r.json()))
            self.msgbox_callback('Cannot login: {}'.format(r.json()['error_description']))

        self.is_logging = False
        self.request_callback()

    def check_user_logged(self):
        access_token = Cache.get_key('access_token')
        self.access_token = access_token
        self.build_headers()
        self.request_user_info()

    def login(self, email, password):
        self.email = email
        url = '{}&username={}&password={}'.format(Config.SKETCHFAB_OAUTH, urllib.quote(email), urllib.quote(password))
        requests.post(url, hooks={'response': self.handle_login})

    def build_headers(self):
        self.headers = {'Authorization': 'Bearer ' + self.access_token}

    def is_user_logged(self):
        if self.access_token and self.headers:
            return True

        return False

    def clear_threads(self):
        terminathread = []
        for i in range(len(self.threads) - 1):
            if not self.threads[i].IsRunning():
                terminathread.append(self.threads[i])

        for thread in terminathread:
            self.threads.remove(thread)

    def download_model(self, uid):
        downloader = ThreadedModelDownload(self, uid, self.import_model)
        downloader.Start()

        self.threads.append(downloader)
        self.clear_threads()

    # Import should not be threadd
    # see https://developers.maxon.net/docs/Cinema4DPythonSDK/html/modules/c4d.threading/index.html#threading-information
    def import_model(self, filepath, uid):
        importer = ImportGLTF(self.import_callback)
        importer.run(filepath, uid)

    def logout(self):
        self.access_token = ''
        self.headers = {}
        self.is_user_pro = False
        self.display_name = ''
        self.plan_type = ''
        Cache.delete_key('access_token')
        Cache.delete_key('key')

    def get_user_info(self):
        if self.display_name and self.plan_type:
            return 'as {} ({})'.format(self.display_name, self.plan_type)
        else:
            return ''

    def parse_user_info(self, r, *args, **kargs):
        if r.status_code == 200:
            user_data = r.json()
            self.display_name = user_data['displayName']
            self.plan_type = user_data['account']
            self.is_user_pro = self.plan_type != 'basic'
            self.login_callback()
        else:
            self.access_token = ''
            self.headers = {}

    def request_thumbnail(self, thumbnails_json, thumbnail_cb):
        url = Utils.get_thumbnail_url(thumbnails_json)
        requests.get(url, stream=True, hooks={'response': thumbnail_cb})

    def request_model_info(self, uid):
        url = Config.SKETCHFAB_MODEL + '/' + uid
        requests.get(url, hooks={'response': self.handle_model_info})

    def handle_model_info(self, r, *args, **kwargs):
        uid = Utils.get_uid_from_model_url(r.url)

        # Dirty fix to avoid processing obsolete result data
        if 'current' not in self.search_results or uid not in self.search_results['current']:
            return

        model = self.search_results['current'][uid]
        json_data = r.json()
        model.license = json_data['license']['fullName']
        anim_count = int(json_data['animationCount'])
        model.animated = 'Yes ({} animation(s))'.format(anim_count) if anim_count > 0 else 'No'
        self.search_results['current'][uid] = model

    def search(self, url):
        threaded = ThreadedSearch(self, url)
        threaded.Start()
        self.threads.append(threaded)
        self.clear_threads()

    def has_next(self):
        return self.next_results_url is not None

    def has_prev(self):
        return self.prev_results_url is not None

    def search_next(self):
        self.search(self.next_results_url)

    def search_prev(self):
        self.search(self.prev_results_url)


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


class ThreadedImporter(C4DThread):
    def __init__(self, filepath, uid, progress_callback=None):
        C4DThread.__init__(self)
        self.filepath = filepath
        self.uid = uid
        self.importer = ImportGLTF(progress_callback)

    def Main(self):
        self.importer.run(self.filepath, self.uid)


class ThreadedModelDownload(C4DThread):
    def __init__(self, api, uid, import_callback):
        C4DThread.__init__(self)
        self.skfb_api = api
        self.uid = uid
        self.import_callback = import_callback
        self.importer = ImportGLTF(self.import_callback)

    def Main(self):
        self.download_model(self.uid)

    def download_model(self, uid):
        skfb_model = self.skfb_api.get_sketchfab_model(uid)
        if skfb_model.download_url:
            # Check url sanity
            if time.time() - skfb_model.time_url_requested < skfb_model.url_expires:
                self.get_archive(skfb_model.download_url)
            else:
                print("Download url is outdated, requesting a new one")
                skfb_model.download_url = None
                skfb_model.url_expires = None
                skfb_model.time_url_requested = None
                requests.get(Utils.build_download_url(uid), headers=self.skfb_api.headers, hooks={'response': self.handle_download})
        else:
            requests.get(Utils.build_download_url(uid), headers=self.skfb_api.headers, hooks={'response': self.handle_download})

    def handle_download(self, r, *args, **kwargs):
        if r.status_code != 200 or 'gltf' not in r.json():
            self.msgbox_callback('Download not available for this model')
            return

        uid = Utils.get_uid_from_model_url(r.url)

        gltf = r.json()['gltf']
        skfb_model = self.skfb_api.get_sketchfab_model(uid)
        skfb_model.download_url = gltf['url']
        skfb_model.time_url_requested = time.time()
        skfb_model.url_expires = gltf['expires']

        self.get_archive(gltf['url'])

    def get_archive(self, url):
        def unzip_archive(archive_path):
            if os.path.exists(archive_path):
                import zipfile
                try:
                    zip_ref = zipfile.ZipFile(archive_path, 'r')
                    extract_dir = os.path.dirname(archive_path)
                    zip_ref.extractall(extract_dir)
                    zip_ref.close()
                except zipfile.BadZipFile:
                    self.msgbox_callback('Error when dezipping file')
                    os.remove(archive_path)
                    self.msgbox_callback('Invaild zip. Try again')
                    return None, None

                gltf_file = os.path.join(extract_dir, 'scene.gltf')
                return gltf_file, archive_path

            else:
                print('ERROR: archive doesn\'t exist')

        if url is None:
            return

        r = requests.get(url, stream=True)
        uid = Utils.get_uid_from_download_url(url)
        temp_dir = os.path.join(Config.SKETCHFAB_MODEL_DIR, uid)

        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        archive_path = os.path.join(temp_dir, '{}.zip'.format(uid))
        if not os.path.exists(archive_path):
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
        else:
            print('Model already downloaded')

        gltf_path, gltf_zip = unzip_archive(archive_path)
        if gltf_path:
            try:
                self.import_callback(gltf_path, self.uid)
            except Exception as e:
                import traceback
                print(traceback.format_exc())
        else:
            model = self.get_sketchfab_model(uid)


class ThreadedSearch(C4DThread):
    def  __init__(self, api, url):
        C4DThread.__init__(self)
        self.skfb_api = api
        self.url = url

    def Main(self):
        requests.get(self.url, headers=self.skfb_api.headers, hooks={'response': self.parse_results})

    def parse_results(self, r, *args, **kwargs):
        json_data = r.json()

        if 'current' in self.skfb_api.search_results:
            self.skfb_api.search_results['current'].clear()
            del self.skfb_api.search_results['current']

        self.skfb_api.search_results['current'] = OrderedDict()

        for result in list(json_data['results']):
            model = SketchfabModel(result)
            self.skfb_api.search_results['current'][model.uid] = model

        if json_data['next']:
            self.skfb_api.next_results_url = json_data['next']
        else:
            self.skfb_api.next_results_url = None

        if json_data['previous']:
            self.skfb_api.prev_results_url = json_data['previous']
        else:
            self.skfb_api.prev_results_url = None

        # Request models thumbnails
        for result in list(json_data['results']):
            if not result['uid'] in self.skfb_api.search_results['current']:
                continue

            model = self.skfb_api.search_results['current'][result['uid']]
            if not Utils.thumbnail_file_exists(model.uid):
                self.skfb_api.request_thumbnail(result['thumbnails'], self.handle_thumbnail)
            else:
                model.preview_path =  Utils.build_thumbnail_path(model.uid)
                model.thumbnail_path = Utils.build_thumbnail_path(model.uid, is_thumbnail=True)

        if self.skfb_api.request_callback:
            self.skfb_api.request_callback()


    def handle_thumbnail(self, r, *args, **kwargs):
        def get_resize_resolution(im):
            size = Config.UI_THUMBNAIL_RESOLUTION
            width, height = im.size
            factor = size / height

            width *= factor
            height *= factor

            return (int(width), int(height))

        def get_square_crop_resolution(im):
            width, height = im.size
            size = Config.UI_THUMBNAIL_RESOLUTION

            left = (width - size)/2
            top = (height - size)/2
            right = (width + size)/2
            bottom = (height + size)/2

            return (left, top, right, bottom)

        uid = Utils.get_uid_from_thumbnail_url(r.url)
        if not uid in self.skfb_api.search_results['current']:
            return

        if not os.path.exists(Config.SKETCHFAB_THUMB_DIR):
            os.makedirs(Config.SKETCHFAB_THUMB_DIR)

        preview_path = Utils.build_thumbnail_path(uid)

        if os.path.exists(preview_path):
            return

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
            return

        try:
            im = Image.open(preview_path)
        except IOError:
            return

        # Resize for preview (model page)
        resize_res = get_resize_resolution(im)
        im = im.resize(resize_res, resample=Image.BILINEAR)

        # Crop to square for results (should be replaced by code using preview image)
        crop_res = get_square_crop_resolution(im)
        im = im.crop(crop_res)

        thumbnail_path = Utils.build_thumbnail_path(uid, is_thumbnail=True)
        im.save(thumbnail_path, "JPEG")

        if not uid in self.skfb_api.search_results['current']:
            return

        self.skfb_api.search_results['current'][uid].preview_path = preview_path
        self.skfb_api.search_results['current'][uid].thumbnail_path = thumbnail_path
        self.skfb_api.request_callback()