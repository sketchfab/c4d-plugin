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
import json

from config import Config

# Should use c4d cache instead
class Cache:
    @staticmethod
    def read():
        if not os.path.exists(Config.SKETCHFAB_CACHE_FILE):
            return {}

        with open(Config.SKETCHFAB_CACHE_FILE, 'rb') as f:
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
        with open(Config.SKETCHFAB_CACHE_FILE, 'wb+') as f:
            f.write(json.dumps(cache_data).encode('utf-8'))

    @staticmethod
    def delete_key(key):
        cache_data = Cache.read()
        if key in cache_data:
            del cache_data[key]

        with open(Config.SKETCHFAB_CACHE_FILE, 'wb+') as f:
            f.write(json.dumps(cache_data).encode('utf-8'))
