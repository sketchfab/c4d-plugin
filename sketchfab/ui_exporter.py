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

from __future__ import division

import textwrap
import webbrowser
import os

# C4D modules
import c4d
from c4d import gui

# Plugins modules
from api import SketchfabApi
from import_gltf import ImportGLTF
from config import Config
from cache import Cache
from utils import Utils


# Modules from the legacy exporter code
import datetime
import os
import json
import shelve
import webbrowser
import zipfile
import threading



"""
Sketchfab Exporter v1.3.5

Copyright: Erwin Santacruz 2012 (www.990adjustments.com)
Written for CINEMA 4D R13 - R15

Name-US: Sketchfab Exporter v1.3.5

Description-US: Model exporter for Sketchfab.com

Creation Date: 09/06/12
Modified Date: 03/16/13
"""


BTN_ABOUT = 100001
BTN_WEB = 100002
TXT_MODEL_NAME = 100003
EDITXT_MODEL_TITLE = 100004
TXT_DESCRIPTION = 100005
EDITXT_DESCRIPTION = 100006
TXT_TAGS = 100007
EDITXT_TAGS = 100008
TXT_API_TOKEN = 100009
EDITXT_API_TOKEN = 100010
BTN_PUBLISH = 100011
MENU_SAVE_API_TOKEN = 100012
BTN_WEB_990 = 100013
CHK_PRIVATE = 100014
BTN_THUMB_SRC_PATH = 100015
EDITXT_THUMB_SRC_PATH = 100015
EDITXT_PASSWORD = 100016
CHK_ANIMATION = 100017
CHK_PUBLISHDRAFT = 100018
BTN_SKFB_SIGNUP = 100019
BTN_SKFB_TOKEN = 100020

GROUP_WRAPPER = 20000
GROUP_ONE = 20001
GROUP_TWO = 20002
GROUP_THREE = 20003
GROUP_FOUR = 20004
GROUP_FIVE = 20005
GROUP_SIX = 20006

UA_HEADER = 30000
UA_ICON = 30001







__author__ = "Erwin Santacruz"
__website__ = "http://990adjustments.com"
__sketchfab__ = "http://sketchfab.com"
__twitter__ = "@990adjustments"
__email__ = "hi@990adjustments.com"
__plugin_title__ = "Sketchfab Exporter"
__version__ = "1.3.5"
__copyright_year__ = datetime.datetime.now().year
__exporter_id__ = 1029390







# Constants
SETTINGS = "com.990adjustments.SketchfabExport"
SKETCHFAB_URL = "https://api.sketchfab.com/v1/models"
FBX20142 = 1026370

export_options = {c4d.FBXEXPORT_LIGHTS: 1,
                  c4d.FBXEXPORT_CAMERAS: 0,
                  c4d.FBXEXPORT_SPLINES: 1,
                  # Geometry and Materials
                  c4d.FBXEXPORT_SAVE_NORMALS: 1,
                  c4d.FBXEXPORT_TEXTURES: 1,
                  c4d.FBXEXPORT_EMBED_TEXTURES: 1,
                  c4d.FBXEXPORT_FBX_VERSION: c4d.FBX_EXPORTVERSION_NATIVE,
                  # cancel all these one
                  c4d.FBXEXPORT_PLA_TO_VERTEXCACHE: 0,
                  c4d.FBXEXPORT_SAVE_VERTEX_MAPS_AS_COLORS: 0,
                  c4d.FBXEXPORT_TRIANGULATE: 0,
                  c4d.FBXEXPORT_SDS_SUBDIVISION: 1,
                  c4d.FBXEXPORT_ASCII: 0}

WRITEPATH = os.path.join(c4d.storage.GeGetStartupWritePath(), 'Sketchfab')
FILEPATH = os.path.join(WRITEPATH, SETTINGS)

if not os.path.exists(WRITEPATH):
    os.mkdir(WRITEPATH)

# Globals
g_uploaded = False
g_error = ""
g_lastUpdated = ""











class Utilities(object):
    """Several helper methods."""

    def __init__(self, arg):
        super(Utilities, self).__init__()

    @staticmethod
    def ESOpen_website(site):
        """Opens Website.

        :param string site: website url
        """

        webbrowser.open(site)

    @staticmethod
    def ESOpen_about():
        """Show About information dialog box."""

        """
        gui.MessageDialog("{0} v{1}\nCopyright (C) {2} {3}\nAll rights reserved.\n\nWeb:      {4}\nTwitter:  {5}\nEmail:    {6}\n\nThis program comes with ABSOLUTELY NO WARRANTY. For details, please visit\nhttp://www.gnu.org/licenses/gpl.html"
                          .format(__plugin_title__,
                                  __version__,
                                  __copyright_year__,
                                  __author__,
                                  __website__,
                                  __twitter__,
                                  __email__), c4d.GEMB_OK)
        """

    @staticmethod
    def ESZipdir(path, zipObject, title):
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


class PublishModelThread(c4d.threading.C4DThread):
    """Class that publishes 3D model to Sketchfab.com."""

    def __init__(self, data, title, activeDoc, activeDocPath, enable_animation):
        c4d.threading.C4DThread.__init__(self)
        self.data = data
        self.title = title
        self.activeDoc = activeDoc
        self.activeDocPath = activeDocPath
        self.enable_animation = enable_animation

    def Main(self):
        global g_uploaded
        global g_error

        # Need to work on this some more
        time_start = datetime.datetime.now()
        # t = time_start.strftime("%a %b %d %I:%M %p")
        t = time_start.strftime("%c")

        print("\nUpload started on {0}".format(t))
        print("Exporting...\n")

        exportFile = os.path.join(self.activeDocPath, self.title + '.fbx')

        options = self.get_fbxexport_options()
        backup_options = {}

        export_options[c4d.FBXEXPORT_TRACKS] = self.enable_animation
        export_options[c4d.FBXEXPORT_BAKE_ALL_FRAMES] = self.enable_animation

        for key in export_options:
            if options[key] != export_options[key]:
                backup_options[key] = options[key]

            options[key] = export_options[key]

        # FBX Export
        c4d.documents.SaveDocument(self.activeDoc, exportFile,
                               c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST, FBX20142)

        # restore options
        for key in backup_options:
            options[key] = backup_options[key]

        if not os.path.exists(exportFile):
            g_uploaded = False
            g_error = "Export failed."
            c4d.SpecialEventAdd(__exporter_id__)
            return False

        print("Export successful.")

        basepath, dirname = os.path.split(self.activeDocPath)
        archiveName = self.title + '.zip'
        os.chdir(basepath)

        zip = zipfile.ZipFile(archiveName, 'w')
        Utilities.ESZipdir(dirname, zip, self.title+'.fbx')
        zip.close()

        # Connection code
        # Begin upload
        print("Uploading...\n")

        _headers = get_sketchfab_props().skfb_api.headers

        try:
            r = SketchfabApi.requests.post(
                Config.SKETCHFAB_MODEL,
                data    = self.data,
                files   = {"modelFile": open(archiveName, 'rb')},
                headers = _headers
            )
        except requests.exceptions.RequestException as e:
            g_uploaded = False
            g_error = error
            return 

        result = r.json()

        if r.status_code != requests.codes.created:
            g_error = "Invalid response from server."
        else:
            model_id = result["uid"]
            g_uploaded = True
            # Open website on model page
            result = gui.MessageDialog("Your model was succesfully uploaded to Sketchfab.com.\nClick OK to open the browser on your model page", c4d.GEMB_OKCANCEL)
            if result == c4d.GEMB_R_OK:
                Utilities.ESOpen_website(__sketchfab__ + '/models/' + model_id)

        # Clean up
        self.cleanup_files(archiveName, exportFile)
        c4d.SpecialEventAdd(__exporter_id__)

    def get_fbxexport_options(self):
        ''' Set the good options for fbx export to Sketchfab '''
        # Get the fbx export plugin
        fbxplugin = c4d.plugins.FindPlugin(1026370, c4d.PLUGINTYPE_SCENESAVER)
        if not fbxplugin:
            return
        # Access the plugin options
        reply = {}
        if fbxplugin.Message(c4d.MSG_RETRIEVEPRIVATEDATA, reply):
                return reply.get('imexporter')

    def cleanup_files(self, archive_name=None, export_file=None):
        if archive_name and os.path.exists(archive_name):
            try:
                os.remove(archive_name)
            except Exception:
                print("Unable to remove file {0}".format(archive_name))

        if export_file and os.path.exists(export_file):
            try:
                os.remove(export_file)
            except Exception:
                print("Unable to remove file {0}".format(export_file))





class UserAreaPathsHeader(gui.GeUserArea):
    """Sketchfab header image."""

    bmp = c4d.bitmaps.BaseBitmap()

    def GetMinSize(self):
        self.width = 600
        self.height = 75
        return (self.width, self.height)

    def DrawMsg(self, x1, y1, x2, y2, msg):
        thisFile = os.path.abspath(__file__)
        thisDirectory = os.path.dirname(thisFile)
        path = os.path.join(thisDirectory, "res", "header.png")
        result, ismovie = self.bmp.InitWith(path)
        x1 = 0
        y1 = 0
        x2 = self.bmp.GetBw()
        y2 = self.bmp.GetBh()

        if result == c4d.IMAGERESULT_OK:
            self.DrawBitmap(self.bmp, 0, 0, self.bmp.GetBw(), self.bmp.GetBh(),
                            x1, y1, x2, y2, c4d.BMP_NORMALSCALED | c4d.BMP_ALLOWALPHA)

    def Redraw(self):
        thisFile = os.path.abspath(__file__)
        thisDirectory = os.path.dirname(thisFile)
        path = os.path.join(thisDirectory, "res", "header.png")
        result, ismovie = self.bmp.InitWith(path)
        x1 = 0
        y1 = 0
        x2 = self.bmp.GetBw()
        y2 = self.bmp.GetBh()

        if result == c4d.IMAGERESULT_OK:
            self.DrawBitmap(self.bmp, 0, 0, self.bmp.GetBw(), self.bmp.GetBh(),
                            x1, y1, x2, y2, c4d.BMP_NORMALSCALED | c4d.BMP_ALLOWALPHA)


class MainDialog(gui.GeDialog):
    """Main Dialog Class"""

    userarea_paths_header = UserAreaPathsHeader()
    save_api_token = False

    def InitValues(self):
        """Called when the dialog is initialized by the GUI.
        True if successful, or False to signalize an error.
        """

        global g_lastUpdated

        print("\n{0} v{1} loaded. Copyright (C) {2} {3}. All rights reserved.\n\nThis program comes with ABSOLUTELY NO WARRANTY. For details, please visit http://www.gnu.org/licenses/gpl.html\n\n"
              .format(__plugin_title__, __version__, __copyright_year__, __author__))

        try:
            prefs = shelve.open(FILEPATH, 'r')

            if 'api_token' in prefs:
                if prefs['api_token']:
                    self.MenuInitString(MENU_SAVE_API_TOKEN, True, True)
                    self.save_api_token = True
                    self.SetString(EDITXT_API_TOKEN, '-' * len(prefs['api_token']))
                else:
                    self.MenuInitString(MENU_SAVE_API_TOKEN, True, False)
                    self.save_api_token = False

            if 'lastUpdate' in prefs:
                g_lastUpdated = prefs['lastUpdate']
                self.groupSixWillRedraw()

            prefs.close()
        except:
            self.MenuInitString(MENU_SAVE_API_TOKEN, True, False)

        self.Enable(EDITXT_PASSWORD, False)

        return True

    def createGroupFiveItems(self):
        self.AddCheckbox(id=CHK_PRIVATE, flags=c4d.BFH_SCALEFIT | c4d.BFH_LEFT,
                         initw=0, inith=0, name="Private Model (Pro User Only)")
        self.AddStaticText(id=0, flags=c4d.BFH_LEFT,
                           initw=0, inith=0, name="Password (optional):    ")
        self.AddEditText(id=EDITXT_PASSWORD, flags=c4d.BFH_SCALEFIT,
                         initw=0, inith=0, editflags=c4d.EDITTEXT_PASSWORD)
        self.AddCheckbox(id=CHK_PUBLISHDRAFT, flags=c4d.BFH_LEFT,
                         initw=0, inith=0, name="Publish as a draft (not visible to public immediately)")

    def groupFiveWillRedraw(self):
        self.LayoutFlushGroup(GROUP_FIVE)
        self.createGroupFiveItems()
        self.LayoutChanged(GROUP_FIVE)

    def createGroupSixItems(self):
        self.AddStaticText(id=0, flags=c4d.BFH_LEFT | c4d.BFH_SCALEFIT, initw=0, inith=0, name=g_lastUpdated)
        self.AddButton(id=BTN_PUBLISH, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=16, name="Publish")

    def groupSixWillRedraw(self):
        self.LayoutFlushGroup(GROUP_SIX)
        self.createGroupSixItems()
        self.LayoutChanged(GROUP_SIX)

    def CreateLayout(self):
        """Override - Called when C4D is about to display the dialog.
        True if successful, or False to signalize an error.
        """

        self.SetTitle(__plugin_title__)

        # Create the menu
        self.MenuFlushAll()

        # Options menu
        self.MenuSubBegin("File")
        self.MenuAddCommand(c4d.IDM_CM_CLOSEWINDOW)
        self.MenuSubEnd()

        # Options menu
        self.MenuSubBegin("Options")
        self.MenuAddString(MENU_SAVE_API_TOKEN, "Save API token")
        self.MenuSubEnd()

        # Info menu
        self.MenuSubBegin("Info")
        self.MenuAddString(BTN_ABOUT, "About")
        self.MenuAddString(BTN_WEB, "Visit Sketchfab.com")
        self.MenuAddString(BTN_WEB_990, "Visit 990adjustments.com")
        self.MenuSubEnd()

        self.MenuFinished()

        docname = c4d.documents.GetActiveDocument().GetDocumentName()

        # ----------------------------------------------------------------------
        # Begin WRAPPER
        # ----------------------------------------------------------------------

        self.GroupBegin(id=GROUP_WRAPPER,
                        flags=c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
                        cols=1,
                        rows=1,
                        title="Wrapper",
                        groupflags=c4d.BORDER_NONE)

        # UA groups
        self.GroupBegin(id=GROUP_ONE,
                        flags=c4d.BFH_SCALEFIT,
                        cols=1,
                        rows=1,
                        title="Header",
                        groupflags=c4d.BORDER_NONE)

        self.GroupSpace(0, 0)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.AddUserArea(UA_HEADER, c4d.BFH_LEFT)
        self.AttachUserArea(self.userarea_paths_header, UA_HEADER)
        self.userarea_paths_header.LayoutChanged()

        self.GroupEnd()

        self.GroupBegin(id=GROUP_TWO,
                        flags=c4d.BFH_SCALEFIT,
                        cols=2,
                        rows=1)

        self.GroupSpace(40, 10)
        self.GroupBorderSpace(6, 6, 6, 6)

        self.AddStaticText(id=TXT_MODEL_NAME, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Model name:")
        self.AddEditText(id=EDITXT_MODEL_TITLE, flags=c4d.BFH_SCALEFIT, initw=0, inith=0)
        self.SetString(EDITXT_MODEL_TITLE, docname)

        self.AddStaticText(id=TXT_DESCRIPTION, flags=c4d.BFH_LEFT | c4d.BFV_TOP,
                           initw=0, inith=0, name="Description:")
        self.AddMultiLineEditText(id=EDITXT_DESCRIPTION, flags=c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
                                  initw=0, inith=100, style=c4d.DR_MULTILINE_WORDWRAP)
        self.SetString(EDITXT_DESCRIPTION, docname)

        self.AddStaticText(id=TXT_TAGS, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Tags: cinema4d ")
        self.AddEditText(id=EDITXT_TAGS, flags= c4d.BFH_RIGHT | c4d.BFH_SCALEFIT, initw=0, inith=0)

        self.AddCheckbox(id=CHK_ANIMATION, flags=c4d.BFH_LEFT,
                         initw=0, inith=0, name="Enable animation")

        self.GroupEnd()
        self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)
        self.GroupBegin(id=GROUP_FOUR,
                        flags=c4d.BFH_SCALEFIT,
                        cols=4,
                        rows=1)

        self.GroupSpace(11, 10)
        self.GroupBorderSpace(6, 6, 6, 6)

        self.AddStaticText(id=TXT_API_TOKEN, flags=c4d.BFH_LEFT, initw=0, inith=0, name="API token:")
        self.AddEditText(id=EDITXT_API_TOKEN,flags=c4d.BFH_SCALEFIT,
                         initw=230, inith=0, editflags=c4d.EDITTEXT_PASSWORD)
        self.AddButton(id=BTN_SKFB_TOKEN, flags=c4d.BFH_RIGHT, initw=145, inith=16, name="Get API token")
        self.AddButton(id=BTN_SKFB_SIGNUP, flags=c4d.BFH_RIGHT, initw=130, inith=16, name="Create account")

        self.GroupEnd()

        self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)

        # Group FIVE
        self.GroupBegin(id=GROUP_FIVE,
                        flags=c4d.BFH_SCALEFIT | c4d.BFV_BOTTOM,
                        cols=3,
                        rows=1)

        self.GroupSpace(4, 4)
        self.GroupBorderSpace(6, 6, 6, 6)

        self.groupFiveWillRedraw()

        self.GroupEnd()

        self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)

        self.GroupBegin(id=GROUP_SIX,
                        flags=c4d.BFH_SCALEFIT | c4d.BFV_BOTTOM,
                        cols=2,
                        rows=1)

        self.GroupSpace(4, 4)
        self.GroupBorderSpace(6, 6, 6, 6)

        self.groupSixWillRedraw()

        self.GroupEnd()

        self.GroupEnd()

        # ----------------------------------------------------------------------
        # End WRAPPER
        # ----------------------------------------------------------------------
        return True

    def setApiToken(self, _setApiToken, _api_token=None):
        """Saves API token.

        :param string _setApiToken: the api token
        :param bool _api_token: save or delete api token
        """

        if _setApiToken:
            try:
                prefs = shelve.open(FILEPATH, 'c')
                prefs['api_token'] = _api_token
                prefs.close()
            except Exception, err:
                print("Could not save API token. Reason: {0}".format(err))
        else:
            # delete settings
            try:
                os.remove(FILEPATH + '.db')
                self.SetString(EDITXT_API_TOKEN, "")
            except Exception, err:
                print("Unable to delete settings. Reason: {0}".format(err))

    def CoreMessage(self, id, msg):
        """Override this function if you want to react
        to C4D core messages. The original message is stored in msg.
        """

        global g_lastUpdated

        if id == __exporter_id__:
            c4d.StatusSetBar(100)

            time_start = datetime.datetime.now()
            # t = time_start.strftime("%a %b %d %I:%M %p")
            t = time_start.strftime("%c")

            try:
                prefs = shelve.open(FILEPATH, 'c')
            except Exception as err:
                print("\nUnable to load preferences. Reason: ".format(err))

            if g_uploaded:
                print("Your model was succesfully uploaded to Sketchfab.com.")

                print("\nUpload ended on {0}".format(t))

                g_lastUpdated = "Successful Upload on {0}".format(t)

                if prefs:
                    prefs['lastUpdate'] = g_lastUpdated
                    prefs.close()
            else:
                gui.MessageDialog("Unable to upload model to Sketchfab.com. Reason: {0}".format(g_error), c4d.GEMB_OK)
                print("Unable to upload model to Sketchfab.com. Reason: {0}".format(g_error))
                g_lastUpdated = "Upload failed on {0}".format(t)

                if prefs:
                    prefs['lastUpdate'] = g_lastUpdated
                    prefs.close()

            self.groupSixWillRedraw()
            self.Enable(BTN_PUBLISH, True)
            self.SetTitle(__plugin_title__)
            c4d.StatusClear()

        return True

    def Command(self, id, msg):
        """Override this function if you want to react to user clicks. Whenever the
        user clicks on a gadget and/or changes its value this function will be
        called.

        It is also called when a string menu item is selected.
        Override it to handle such events.
        """

        global g_lastUpdated

        if id == MENU_SAVE_API_TOKEN:
            if self.save_api_token:
                self.MenuInitString(MENU_SAVE_API_TOKEN, True, False)
                self.save_api_token = False
                self.setApiToken(False)
            else:
                self.MenuInitString(MENU_SAVE_API_TOKEN, True, True)
                self.save_api_token = True

        if id == BTN_ABOUT:
            Utilities.ESOpen_about()

        if id == BTN_WEB:
            Utilities.ESOpen_website(__sketchfab__)

        if id == BTN_WEB_990:
            Utilities.ESOpen_website(__website__)

        if id == BTN_THUMB_SRC_PATH:
            selected = c4d.storage.LoadDialog(type=c4d.FILESELECTTYPE_ANYTHING)
            if not selected:
                return False
            else:
                self.SetString(EDITXT_THUMB_SRC_PATH, selected)

        if id == BTN_SKFB_TOKEN:
            Utilities.ESOpen_website(__sketchfab__ + '/settings/password')

        if id == BTN_SKFB_SIGNUP:
            Utilities.ESOpen_website(__sketchfab__ + '/signup')

        if id == CHK_PRIVATE:
            if self.GetBool(CHK_PRIVATE):
                self.Enable(EDITXT_PASSWORD, True)
            else:
                self.groupFiveWillRedraw()
                self.Enable(EDITXT_PASSWORD, False)

        if id == BTN_PUBLISH:
            c4d.StatusSetBar(50)
            g_lastUpdated = "Working it..."
            self.groupSixWillRedraw()

            data = {}
            activeDoc = c4d.documents.GetActiveDocument()
            activeDocPath = activeDoc.GetDocumentPath()
            if not os.path.exists(activeDocPath):
                path = c4d.storage.SaveDialog(type=c4d.FILESELECTTYPE_ANYTHING, title="Please save your scene", force_suffix="c4d")
                result = c4d.documents.SaveDocument(activeDoc,path, c4d.SAVEDOCUMENTFLAGS_0, c4d.FORMAT_C4DEXPORT)
                c4d.documents.LoadFile(path)
                if not result:
                    gui.MessageDialog("Please save your scene first.", c4d.GEMB_OK)
                    c4d.StatusClear()
                    return False

            # Set document data with newly saved document
            activeDoc = c4d.documents.GetActiveDocument()
            activeDocPath = activeDoc.GetDocumentPath()

            self.Enable(BTN_PUBLISH, False)
            self.SetTitle("{0} publishing model...".format(__plugin_title__))

            title = self.GetString(EDITXT_MODEL_TITLE)
            description = self.GetString(EDITXT_DESCRIPTION)
            tags = self.GetString(EDITXT_TAGS)
            token = self.GetString(EDITXT_API_TOKEN)
            private = self.GetBool(CHK_PRIVATE)
            password = self.GetString(EDITXT_PASSWORD)
            enable_animation = self.GetBool(CHK_ANIMATION)
            auto_publish = not(self.GetBool(CHK_PUBLISHDRAFT))

            if '-' in token:
                try:
                    prefs = shelve.open(FILEPATH, 'r')
                except:
                    gui.MessageDialog("Please re-enter your API token.", c4d.GEMB_OK)
                    self.MenuInitString(MENU_SAVE_API_TOKEN, True, False)
                    self.Enable(BTN_PUBLISH, True)
                    self.SetTitle(__plugin_title__)
                    c4d.StatusClear()
                    return False
                else:
                    if 'api_token' in prefs:
                        if prefs['api_token']:
                            api_token = prefs['api_token']
                        else:
                            gui.MessageDialog("Please re-enter your API token.", c4d.GEMB_OK)
                            self.MenuInitString(MENU_SAVE_API_TOKEN, True, False)
                            self.Enable(BTN_PUBLISH, True)
                            self.SetTitle(__plugin_title__)
                            c4d.StatusClear()
                            return False

                    prefs.close()
            else:
                api_token = token

            if len(title) == 0:
                gui.MessageDialog("Please enter a name for your model.", c4d.GEMB_OK)
                self.Enable(BTN_PUBLISH, True)
                self.SetTitle(__plugin_title__)
                c4d.StatusClear()
                return False

            if len(title) > 32:
                gui.MessageDialog("The model name should not have more than 32 characters.", c4d.GEMB_OK)
                self.Enable(BTN_PUBLISH, True)
                self.SetTitle(__plugin_title__)
                c4d.StatusClear()
                return False

            if len(api_token) == 0:
                gui.MessageDialog("Please enter your API token. Your API token can be found in your dashboard at sketchfab.com", c4d.GEMB_OK)
                self.Enable(BTN_PUBLISH, True)
                self.SetTitle(__plugin_title__)
                c4d.StatusClear()
                return False

            if (len(description) > 1024):
                gui.MessageDialog("Please use a description with less than 1024 characters", c4d.GEMB_OK)
                self.Enable(BTN_PUBLISH, True)
                self.SetTitle(__plugin_title__)
                c4d.StatusClear()
                return False

            # populate data
            if len(description) != 0:
                data['description'] = description

            data['tags'] = 'cinema4d '
            if len(tags) != 0:
                data['tags'] += " ".join(props.tags.split(" ")[:41])

            data['title'] = title
            data['token'] = api_token

            if private:
                data['private'] = private

            if private and len(password) != 0:
                data['password'] = password

            if self.save_api_token:
                self.setApiToken(True, api_token)

            # Start Multithread operations
            # pass on data
            data['source'] = 'cinema4d'
            data['isPublished'] = auto_publish

            self.publish = PublishModelThread(data, title, activeDoc, activeDocPath, enable_animation)
            self.publish.Start()
            self.publish.Wait(True)

        return True