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
import sys

import c4d
from c4d import gui, plugins, bitmaps

__author__ = "Sketchfab"
__website__ = "sketchfab.com"
__sketchfab__ = "http://sketchfab.com"
__email__ = "support@sketchfab.com"
__plugin_title__ = "Sketchfab Plugin (BETA)"
__version__ = "0.0.85"
__plugin_id__ = 1052778

HELP_TEXT = "Sketchfab asset importer for C4D"

# Add paths for plugin
SKETCHFAB_PLUGIN_DIRECTORY = os.path.dirname(__file__)
SKETCHFAB_CODE_DIRECTORY = os.path.join(SKETCHFAB_PLUGIN_DIRECTORY, 'sketchfab')
SKFB_DEPENDENCIES_PATH = os.path.join(SKETCHFAB_PLUGIN_DIRECTORY, 'dependencies')
if not SKETCHFAB_PLUGIN_DIRECTORY in sys.path:
    sys.path.insert(0, SKETCHFAB_PLUGIN_DIRECTORY)

if not SKETCHFAB_CODE_DIRECTORY in sys.path:
    sys.path.insert(0, SKETCHFAB_CODE_DIRECTORY)

if not SKFB_DEPENDENCIES_PATH in sys.path:
    sys.path.insert(0, SKFB_DEPENDENCIES_PATH)

from sketchfab.ui import *

class SketchfabPlugin(plugins.CommandData):
    dialog = None

    def Execute(self, doc):
        from sketchfab import ui

        if self.dialog is None:
            self.dialog = SkfbPluginDialog()

        return self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC,
                                pluginid=__plugin_id__,
                                defaultw=600,
                                defaulth=450)

    def RestoreLayout(self, sec_ref):
        if self.dialog is None:
            self.dialog = SkfbPluginDialog()

        return self.dialog.Restore(pluginid=__plugin_id__, secret=sec_ref)

if __name__ == "__main__":
    icon = bitmaps.BaseBitmap()
    dir, file = os.path.split(__file__)
    iconPath = os.path.join(dir, "res", "icon.png")
    icon.InitWith(iconPath)
    plugins.RegisterCommandPlugin(id=__plugin_id__,
                                  str=__plugin_title__,
                                  info=0,
                                  help=HELP_TEXT,
                                  dat=SketchfabPlugin(),
                                  icon=icon)
