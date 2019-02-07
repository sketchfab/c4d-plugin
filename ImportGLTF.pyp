import os
import sys

import c4d
from c4d import documents, gui, plugins, bitmaps, storage

__author__ = "Sketchfab"
__website__ = "sketchfab.com"
__sketchfab__ = "http://sketchfab.com"
__email__ = "aurelien@sketchfab.com"
__plugin_title__ = "Sketchfab Plugin"
__version__ = "0.0.1"
__plugin_id__ = 1025251

HELP_TEXT = "TAMAMAN"
CURRENT_PATH = os.path.join(os.getcwd(), 'plugins\\ImportGLTF\\')
DEPTS_PATH = os.path.join(CURRENT_PATH, 'dependencies')
SAMPLE_PATH = CURRENT_PATH + '\\samples\\cube\\Box.gltf'
sys.path.insert(0, CURRENT_PATH)
sys.path.insert(0, DEPTS_PATH)

from gltfio.imp.gltf2_io_gltf import glTFImporter
from gltfio.imp.gltf2_io_binary import BinaryData

import skfbui
import imp

class SketchfabExporter(plugins.CommandData):
    dialog = None

    def Execute(self, doc):

        imp.reload(skfbui)

        from skfbui import *

        # Check C4D version
        if c4d.GetC4DVersion() < 15000 and c4d.GeGetCurrentOS() == c4d.OPERATINGSYSTEM_WIN:
            c4d.gui.MessageDialog("Sorry, but the plugin is incompatible with the version of Cinema 4D you are currently running.\n\n\
The Sketchfab plugin for Windows requires\nCinema 4D R15 or greater.", c4d.GEMB_OK)
            return False

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
    print("tamere")
    plugins.RegisterCommandPlugin(id=__plugin_id__,
                                  str=__plugin_title__,
                                  info=0,
                                  help=HELP_TEXT,
                                  dat=SketchfabExporter(),
                                  icon=icon)
