import c4d
from c4d import documents, gui, plugins, bitmaps, storage
from c4d.threading import C4DThread

__author__ = "Sketchfab"
__website__ = "sketchfab.com"
__sketchfab__ = "http://sketchfab.com"
__email__ = "aurelien@sketchfab.com"
__plugin_title__ = "Sketchfab Plugin"
__version__ = "0.0.1"

BTN_IMPORT = 100010

import start
import imp
import requests
from .skfbapi import *

from collections import OrderedDict

# enums
resultContainerIDStart = 100015 # + 24 since 24 results on page

GROUP_WRAPPER = 50000
GROUP_ONE = 50001
GROUP_SEARCH = 50002
GROUP_THREE = 50003
GROUP_FOUR = 50004
GROUP_FIVE = 50005
GROUP_RESULTS = 50006

# class SkfbModelDialog(gui.GeDialog):

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


class SkfbPluginDialog(gui.GeDialog):

    def InitValues(self):
        print("Initializing")
        #DEBGUG
        imp.reload(start)
        imp.reload(skfbapi)
        from start import *
        from skfbapi import *

        self.search_results = {}
        self.skfb_api = SketchfabApi()
        self.buttons = []
        self.containers = []

        return True

    def CreateLayout(self):
        self.SetTitle(__plugin_title__)
        # Create the menu
        self.MenuFlushAll()

        # Options menu
        self.MenuSubBegin("File")
        self.MenuAddCommand(c4d.IDM_CM_CLOSEWINDOW)
        self.MenuSubEnd()

        # self.redraw_search_group()
        # self.redraw_results()
        self.AddButton(id=BTN_IMPORT, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=16, name="Import")
        # if self.result_valid:
        #     self.GroupBegin(0, c4d.BFH_SCALEFIT|c4d.BFH_SCALEFIT, 4, 4, "Bitmap Example",0) #id, flags, columns, rows, grouptext, groupflags
        #     self.GroupBorder(c4d.BORDER_BLACK)
        #     self.create_model_button(self.search_results['current'].values()[0])
        #     self.GroupEnd()
        self.MenuFinished()

        self.GroupBegin(id=GROUP_WRAPPER,
                        flags=c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
                        cols=1,
                        rows=1,
                        title="Wrapper",
                        groupflags=c4d.BORDER_NONE)


        self.GroupBegin(id=GROUP_SEARCH,
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
        return True


    def result_valid(self):
        if not 'current' in self.search_results:
            return False

        return True

    def redraw_search_group(self):
        self.LayoutFlushGroup(GROUP_SEARCH)
        self.AddButton(id=BTN_IMPORT, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=16, name="Search")

        self.LayoutChanged(GROUP_SEARCH)

    def resultGroupWillRedraw(self):
        self.LayoutFlushGroup(GROUP_RESULTS)
        self.create_results_ui()
        self.LayoutChanged(GROUP_RESULTS)

    def create_results_ui(self):
        image_container = c4d.BaseContainer() #Create a new container to store the image we will load for the button later on
        self.GroupBegin(0, c4d.BFH_SCALEFIT|c4d.BFH_SCALEFIT, 4, 4, "Bitmap Example",0, 256, 256) #id, flags, columns, rows, grouptext, groupflags
        self.GroupBorder(c4d.BORDER_BLACK)

        if not self.result_valid:
            return

        for index, skfb_model in enumerate(self.search_results['current'].values()):
            fn = c4d.storage.GeGetC4DPath(c4d.C4D_PATH_DESKTOP) #Gets the desktop path
            filenameid = resultContainerIDStart + index
            image_container.SetLong(c4d.BITMAPBUTTON_BORDER, c4d.BORDER_OUT) #Sets the border to look like a button
            image_container.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
            image_container.SetFilename(filenameid, skfb_model.thumbnail_path)

            self.mybutton = self.AddCustomGui(filenameid, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 30, 30, image_container)
            self.mybutton.SetImage(str(skfb_model.thumbnail_path), False)
            self.mybutton.SetToggleState(True)

        self.GroupEnd()
        self.LayoutChanged(10042)

    def Command(self, id, msg):
        if id == BTN_IMPORT:
            self.skfb_api.search(Config.DEFAULT_SEARCH, self.parse_results)
            self.resultGroupWillRedraw()

        for i in range(24):
            if id == resultContainerIDStart + i:
                print('ENABLED BUTTON  {}'.format(i))

        return True

    def parse_results(self, r, *args, **kwargs):
        # skfb = get_sketchfab_props()
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
                self.skfb_api.request_thumbnail(result['thumbnails'], self.handle_thumbnail)
            # elif uid not in skfb.custom_icons:
            #     self.custom_icons.load(uid, os.path.join(Config.SKETCHFAB_THUMB_DIR, "{}.jpeg".format(uid)), 'IMAGE')

        if json_data['next']:
            self.skfb_api.next_results_url = json_data['next']
        else:
            self.skfb_api.next_results_url = None

        if json_data['previous']:
            self.skfb_api.prev_results_url = json_data['previous']
        else:
            self.skfb_api.prev_results_url = None

    def handle_thumbnail(self, r, *args, **kwargs):
        uid = r.url.split('/')[4]
        if not os.path.exists(Config.SKETCHFAB_THUMB_DIR):
            os.makedirs(Config.SKETCHFAB_THUMB_DIR)
        thumbnail_path = os.path.join(Config.SKETCHFAB_THUMB_DIR, uid) + '.jpeg'

        with open(thumbnail_path, "wb") as f:
            total_length = r.headers.get('content-length')

            if total_length is None and r.content:
                f.write(r.content)
            else:
                dl = 0
                total_length = int(total_length)
                for data in r.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)

        self.search_results['current'][uid].thumbnail_path = thumbnail_path


class SketchfabModel:
    def __init__(self, json_data):
        self.title = str(json_data['name'])
        self.author = json_data['user']['displayName']
        self.uid = json_data['uid']
        self.vertex_count = json_data['vertexCount']
        self.face_count = json_data['faceCount']
        self.thumbnail_path = ''

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
