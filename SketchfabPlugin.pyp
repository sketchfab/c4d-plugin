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
from c4d import documents, storage
from c4d.threading import C4DThread

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

from sketchfab.config import Config
from sketchfab.utils import Utils
from sketchfab.ui_importer import *
from sketchfab.ui_exporter import *

__author__         = Config.PLUGIN_AUTHOR
__website__        = Config.SKETCHFAB_URL
__email__          = Config.PLUGIN_EMAIL
__twitter__        = Config.PLUGIN_TWITTER
__copyright_year__ = datetime.datetime.now().year
__version__        = Config.PLUGIN_VERSION

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
                                pluginid=Config.IMPORTER_ID,
                                defaultw=600,
                                defaulth=450)

    def RestoreLayout(self, sec_ref):
        if self.dialog is None:
            self.dialog = SkfbPluginDialog()

        return self.dialog.Restore(pluginid=Config.IMPORTER_ID, secret=sec_ref)


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
                                pluginid=Config.EXPORTER_ID,
                                defaultw=600,
                                defaulth=450)

    def RestoreLayout(self, sec_ref):
        if self.dialog is None:
            self.dialog = MainDialog()

        return self.dialog.Restore(pluginid=Config.EXPORTER_ID, secret=sec_ref)


if __name__ == "__main__":

    # Get the Sketchfab icon
    icon = bitmaps.BaseBitmap()
    iconPath = os.path.join(os.path.split(__file__)[0], "res", "icon.png")
    icon.InitWith(iconPath)

    # Create the necessary directories
    Utils.setup_plugin()

    # Register the importer
    plugins.RegisterCommandPlugin(id=Config.IMPORTER_ID,
                                  str=Config.IMPORTER_TITLE,
                                  info=0,
                                  help=Config.IMPORTER_HELP,
                                  dat=SketchfabImporter(),
                                  icon=icon)

    # Register the exporter
    plugins.RegisterCommandPlugin(id=Config.EXPORTER_ID,
                                  str=Config.EXPORTER_TITLE,
                                  info=0,
                                  help=Config.EXPORTER_HELP,
                                  dat=SketchfabExporter(),
                                  icon=icon)