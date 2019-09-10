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
import datetime


import c4d
from c4d import gui, plugins, bitmaps

#Exporter imports
from c4d import documents, storage
from c4d.threading import C4DThread


__author__         = "Sketchfab"
__website__        = "sketchfab.com"
__email__          = "support@sketchfab.com"
__twitter__        = "@sketchfab"
__copyright_year__ = datetime.datetime.now().year
__version__        = "1.2.0"

__importer_id__    = 1052778
__importer_title__ = "Sketchfab Importer"
__exporter_id__    = 1029390
__exporter_title__ = "Sketchfab Exporter"

HELP_TEXT = "Sketchfab importer/exporter for C4D R.20 - v" + __version__

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

from sketchfab.ui_importer import *
from sketchfab.ui_exporter import *

class SketchfabImporter(plugins.CommandData):
    dialog = None

    def Execute(self, doc):
        from sketchfab import ui_importer

        # Check C4D version
        if c4d.GetC4DVersion() < 20000 and c4d.GeGetCurrentOS() == c4d.OPERATINGSYSTEM_WIN:
            c4d.gui.MessageDialog("Sorry, but the plugin is incompatible with the version of Cinema 4D you are currently running.\n\nThe Sketchfab plugin for Windows requires\nCinema 4D R20 or greater.", c4d.GEMB_OK)
            return False

        if self.dialog is None:
            self.dialog = SkfbPluginDialog()

        return self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC,
                                pluginid=__importer_id__,
                                defaultw=600,
                                defaulth=450)

    def RestoreLayout(self, sec_ref):
        if self.dialog is None:
            self.dialog = SkfbPluginDialog()

        return self.dialog.Restore(pluginid=__importer_id__, secret=sec_ref)


class SketchfabExporter(plugins.CommandData):
    dialog = None

    def Execute(self, doc):
        from sketchfab import ui_exporter

        # Check C4D version
        if c4d.GetC4DVersion() < 20000 and c4d.GeGetCurrentOS() == c4d.OPERATINGSYSTEM_WIN:
            c4d.gui.MessageDialog("Sorry, but the plugin is incompatible with the version of Cinema 4D you are currently running.\n\nThe Sketchfab plugin for Windows requires\nCinema 4D R20 or greater.", c4d.GEMB_OK)
            return False

        if self.dialog is None:
            self.dialog = MainDialog()

        return self.dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC,
                                pluginid=__exporter_id__,
                                defaultw=600,
                                defaulth=450)

    def RestoreLayout(self, sec_ref):
        if self.dialog is None:
            self.dialog = MainDialog()

        return self.dialog.Restore(pluginid=__exporter_id__, secret=sec_ref)

if __name__ == "__main__":
    icon = bitmaps.BaseBitmap()
    dir, file = os.path.split(__file__)
    iconPath = os.path.join(dir, "res", "icon.png")
    icon.InitWith(iconPath)
    plugins.RegisterCommandPlugin(id=__importer_id__,
                                  str=__importer_title__,
                                  info=0,
                                  help=HELP_TEXT,
                                  dat=SketchfabImporter(),
                                  icon=icon)

    plugins.RegisterCommandPlugin(id=__exporter_id__,
                                  str=__exporter_title__,
                                  info=0,
                                  help=HELP_TEXT,
                                  dat=SketchfabExporter(),
                                  icon=icon)