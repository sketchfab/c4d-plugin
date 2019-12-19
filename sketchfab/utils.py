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

import sys
import os
import shutil

from config import Config

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
        if not os.path.exists(Config.SKETCHFAB_TEMP_DIR):
            os.makedirs(Config.SKETCHFAB_TEMP_DIR)
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

    @staticmethod
    def open_directory(path):
        if sys.platform == "win32":
            os.startfile(path)
        else:
            opener ="open" if sys.platform == "darwin" else "xdg-open"
            subprocess.call([opener, path])

    @staticmethod
    def remove_url(value):
        start = value.find('(')
        cleaned = value[0:start] if start != -1 else value

        return cleaned.strip()

    @staticmethod
    def zip_c4d_directory(path, zipObject, title):
        """Adds files to zip object.

        :param string path: path of root directory
        :param object zipObject: the zip object
        :param string title: the name of the .fbx file with extension
        """

        include = ['tex']
        for root, dirs, files, in os.walk(path):
            dirs[:] = [i for i in dirs if i in include]
            for file in files:
                if file.startswith('.'):
                    continue
                if file.endswith('.fbx'.lower()) and file == title:
                    zipObject.write(os.path.join(root, file))

        # zip textures in tex directory
        texDir = os.path.join(path, 'tex')
        if os.path.exists(texDir):
            for f in os.listdir(texDir):
                zipObject.write(os.path.join(path, 'tex', f))
