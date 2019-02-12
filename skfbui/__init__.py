
from __future__ import division
import c4d
from c4d import documents, gui, plugins, bitmaps, storage
from c4d.threading import C4DThread

import start
import imp
import requests
from .skfbapi import *
import webbrowser

from gltfio.imp.gltf2_io_gltf import glTFImporter
from gltfio.imp.gltf2_io_binary import BinaryData
from start import ImportGLTF

import time

# enums
UA_HEADER = 30000
UA_ICON = 30001

GROUP_WRAPPER = 50000
GROUP_ONE = 50001
GROUP_SEARCH = 50002
GROUP_THREE = 50003
GROUP_FOUR = 50004
GROUP_FIVE = 50005
GROUP_RESULTS = 50006

# class SkfbModelDialog(gui.GeDialog):
BTN_SEARCH = 10001
BTN_VIEW_SKFB = 10002
BTN_IMPORT = 10003
BTN_NEXT_PAGE = 10004
BTN_PREV_PAGE = 10005

LB_SEARCH_QUERY = 100010
EDITXT_SEARCH_QUERY = 100011
CHK_IS_PBR = 100012
CHK_IS_STAFFPICK = 100013
CHK_IS_ANIMATED = 100014
CHILD_VALUES = 100015
RDBN_FACE_COUNT = 100016

CBOX_CATEGORY = 100020
CBOX_CATEGORY_ELT = 100021
# 100021 -> 100039 reserved for categories

CBOX_SORT_BY = 100040
CBOX_SORT_BY_ELT = 1000041
# 100041 -> 100044 reserved for orderby

CBOX_FACE_COUNT = 100050
CBOX_FACE_COUNT_ELT = 100051
# 100051 -> 100056 reserved for orderby

resultContainerIDStart = 100061 # + 24 since 24 results on page

OVERRIDE_DOWNLOAD = True
MODEL_PATH = 'D:\\Softwares\\MAXON\\plugins\\ImportGLTF\\samples\\Camera\\scene.gltf'
HEADER_PATH = 'D:\\Softwares\\MAXON\\plugins\\ImportGLTF\\res\\SketchfabHeader.png'
TEXT_WIDGET_HEIGHT=10

import c4d
from c4d import gui

class UserAreaPathsHeader(gui.GeUserArea):
    """Sketchfab header image."""

    bmp = c4d.bitmaps.BaseBitmap()

    def GetMinSize(self):
        self.width = 600
        self.height = 75
        return (self.width, self.height)

    def DrawMsg(self, x1, y1, x2, y2, msg):
        # thisFile = os.path.abspath(__file__)
        # thisDirectory = os.path.dirname(thisFile)
        # path = os.path.join(thisDirectory, "res", "header.png")
        path = HEADER_PATH
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

class ThreadedImporter(C4DThread):
    def __init__(self, filepath, uid, progress_callback=None):
        C4DThread.__init__(self)
        self.filepath = filepath
        self.uid = uid
        self.importer = ImportGLTF(progress_callback)

    def Main(self):
        self.importer.run(self.filepath, self.uid)


class ThreadedLogin(C4DThread):
    def __init__(self, api, email, password, callback=None):
        self.skfb_api = api
        self.email = email
        self.password = password
        self.callback = callback

    def Main(self):
        self.skfb_api.request_callback = self.callback

class SkfbPluginDialog(gui.GeDialog):

    userarea_paths_header = UserAreaPathsHeader()
    last_refresh_time = 0.0

    redraw_requested = False

    def InitValues(self):
        self.SetTimer(50)
        print("Initializing")
        #DEBGUG
        imp.reload(start)
        imp.reload(skfbapi)
        from start import *
        from skfbapi import *

        self.skfb_api = SketchfabApi()
        self.skfb_api.request_callback = self.refresh
        self.login = ThreadedLogin(self.skfb_api, None, None, self.refresh)
        self.login.Start()

        self.buttons = []
        self.containers = []
        self.model_dialog = None

        return True
    def refresh(self):
        self.redraw_requested = True

    def Timer(self, msg):
        if not self.redraw_requested:
            return

        self.resultGroupWillRedraw()
        self.redraw_requested = False

    def CreateLayout(self):
        self.SetTitle(Config.__plugin_title__)

        # Create the menu
        self.MenuFlushAll()

        self.GroupSpace(0, 0)
        self.GroupBorderSpace(0, 0, 0, 0)

        self.AddUserArea(UA_HEADER, c4d.BFH_LEFT)
        self.AttachUserArea(self.userarea_paths_header, UA_HEADER)
        self.userarea_paths_header.LayoutChanged()

        self.GroupEnd()

        # Options menu
        self.MenuSubBegin("File")
        self.MenuAddCommand(c4d.IDM_CM_CLOSEWINDOW)
        self.MenuSubEnd()
        self.AddStaticText(id=LB_SEARCH_QUERY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=170, inith=TEXT_WIDGET_HEIGHT, name="Search")
        self.AddEditText(id=EDITXT_SEARCH_QUERY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=250, inith=TEXT_WIDGET_HEIGHT)
        self.AddButton(id=BTN_SEARCH, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Import")

        # Categories
        self.AddComboBox(id=CBOX_CATEGORY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=250, inith=TEXT_WIDGET_HEIGHT)
        for index, category in enumerate(Config.SKETCHFAB_CATEGORIES):
            self.AddChild(id=CBOX_CATEGORY, subid=CBOX_CATEGORY_ELT + index, child=category[2])
        self.SetInt32(CBOX_CATEGORY, CBOX_CATEGORY_ELT)

        self.AddComboBox(id=CBOX_SORT_BY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=250, inith=TEXT_WIDGET_HEIGHT)
        for index, sort_by in enumerate(Config.SKETCHFAB_SORT_BY):
            self.AddChild(id=CBOX_SORT_BY, subid=CBOX_SORT_BY_ELT + index, child=sort_by[1])
        self.SetInt32(CBOX_SORT_BY, CBOX_SORT_BY_ELT + 2)

        self.AddComboBox(id=CBOX_FACE_COUNT, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=250, inith=TEXT_WIDGET_HEIGHT)
        for index, face_count in enumerate(Config.SKETCHFAB_FACECOUNT):
            self.AddChild(id=CBOX_FACE_COUNT, subid=CBOX_FACE_COUNT_ELT + index, child=face_count[1])
        self.SetInt32(CBOX_FACE_COUNT, CBOX_FACE_COUNT_ELT)

        self.AddCheckbox(id=CHK_IS_PBR, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=70, inith=TEXT_WIDGET_HEIGHT, name='PBR')
        self.AddCheckbox(id=CHK_IS_STAFFPICK, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=170, inith=TEXT_WIDGET_HEIGHT, name='Staffpick')
        self.AddCheckbox(id=CHK_IS_ANIMATED, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=170, inith=TEXT_WIDGET_HEIGHT, name='Animated')

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

        self.GroupEnd()
        return True


    def result_valid(self):
        if not 'current' in self.skfb_api.search_results:
            return False

        return True

    def resultGroupWillRedraw(self):
        self.LayoutFlushGroup(GROUP_RESULTS)
        self.create_results_ui()
        self.LayoutChanged(GROUP_RESULTS)

    def create_results_ui(self):
        self.LayoutFlushGroup(GROUP_RESULTS)
        self.GroupBegin(GROUP_RESULTS, c4d.BFH_SCALEFIT|c4d.BFH_SCALEFIT, 6, 4, "Bitmap Example",0) #id, flags, columns, rows, grouptext, groupflags

        if not self.result_valid:
            return

        if not 'current' in self.skfb_api.search_results:
            return

        for index, skfb_model in enumerate(self.skfb_api.search_results['current'].values()):
            image_container = c4d.BaseContainer() #Create a new container to store the image we will load for the button later on
            self.GroupBegin(0, c4d.BFH_SCALEFIT|c4d.BFH_SCALEFIT, 1, 2, "Bitmap Example",0)
            fn = c4d.storage.GeGetC4DPath(c4d.C4D_PATH_DESKTOP) #Gets the desktop path
            filenameid = resultContainerIDStart + index
            image_container.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
            # image_container.SetBool(c4d.BITMAPBUTTON_IGNORE_BITMAP_WIDTH, True)
            # image_container.SetBool(c4d.BITMAPBUTTON_IGNORE_BITMAP_HEIGHT, True)
            image_container.SetBool(c4d.BITMAPBUTTON_NOBORDERDRAW, True)
            image_container.SetFilename(filenameid, str(skfb_model.thumbnail_path))

            self.mybutton = self.AddCustomGui(filenameid, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 10, 10, image_container)
            self.mybutton.SetLayoutMode(c4d.LAYOUTMODE_MINIMIZED)
            self.mybutton.SetImage(str(skfb_model.thumbnail_path), False)
            self.mybutton.SetToggleState(True)

            self.AddStaticText(id=3, flags=c4d.BFH_CENTER,
                   initw=Config.UI_THUMBNAIL_RESOLUTION, inith=32, name=u'{}'.format(skfb_model.title))
            self.GroupEnd()

        self.GroupEnd()
        self.LayoutChanged(GROUP_RESULTS)
        self.last_refresh_time = time.time()

    def trigger_search(self):
        final_query = Config.BASE_SEARCH

        if self.GetString(EDITXT_SEARCH_QUERY):
            final_query = final_query + '&q={}'.format(self.GetString(EDITXT_SEARCH_QUERY))

        if self.GetBool(CHK_IS_ANIMATED):
            final_query = final_query + '&animated=true'

        if self.GetBool(CHK_IS_STAFFPICK):
            final_query = final_query + '&staffpicked=true'

        if self.GetInt32(CBOX_SORT_BY) == CBOX_SORT_BY_ELT + 1:
            final_query = final_query + '&sort_by=-viewCount'
        elif self.GetInt32(CBOX_SORT_BY) == CBOX_SORT_BY_ELT + 2:
            final_query = final_query + '&sort_by=-likeCount'
        elif self.GetInt32(CBOX_SORT_BY) == CBOX_SORT_BY_ELT + 3:
            final_query = final_query + '&sort_by=-publishedAt'

        if self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 1:
            final_query = final_query + '&max_face_count=10000'
        elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 2:
            final_query = final_query + '&min_face_count=10000&max_face_count=50000'
        elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 3:
            final_query = final_query + '&min_face_count=50000&max_face_count=100000'
        elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 4:
            final_query = final_query + "&min_face_count=100000&max_face_count=250000"
        elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 5:
            final_query = final_query + "&min_face_count=250000"

        if self.GetInt32(CBOX_CATEGORY) != CBOX_CATEGORY_ELT:
            final_query = final_query + '&categories={}'.format(Config.SKETCHFAB_CATEGORIES[self.GetInt32(CBOX_CATEGORY) - CBOX_CATEGORY_ELT][0])

        if self.GetBool(CHK_IS_PBR):
            final_query = final_query + '&pbr_type=true'

        self.skfb_api.search(final_query)

    def Command(self, id, msg):
        trigger_search = False

        bc = c4d.BaseContainer()
        if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.KEY_ENTER,bc):
            if bc[c4d.BFM_INPUT_VALUE] == 1:
                if self.IsActive(EDITXT_SEARCH_QUERY):
                    trigger_search = True

        if id == BTN_SEARCH:
            trigger_search = True

        if id == CBOX_CATEGORY:
            print(self.GetInt32(CBOX_CATEGORY))
            trigger_search = True

        if id == CBOX_SORT_BY:
            print(self.GetInt32(CBOX_SORT_BY))
            trigger_search = True

        if id == CBOX_FACE_COUNT:
            print(self.GetInt32(CBOX_FACE_COUNT))
            trigger_search = True

        if id == CHK_IS_PBR:
            print(self.GetBool(CHK_IS_PBR))
            trigger_search = True

        if id == CHK_IS_ANIMATED:
            print(self.GetBool(CHK_IS_ANIMATED))
            trigger_search = True

        if id == CHK_IS_STAFFPICK:
            print(self.GetBool(CHK_IS_STAFFPICK))
            trigger_search = True

        if trigger_search:
            self.trigger_search()

        for i in range(24):
            if id == resultContainerIDStart + i:
                self.model_dialog = SkfbModelDialog()
                self.model_dialog.SetModelInfo(self.skfb_api.search_results['current'].values()[i], self.skfb_api)
                self.model_dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL_RESIZEABLE , defaultw=450, defaulth=300, xpos=-1, ypos=-1)

        return True


class SkfbModelDialog(gui.GeDialog):

    skfb_model = None
    PROGRESSBAR = 1001
    PROGRESS_GROUP = 1000

    def __init__(self):
        self.progress = 0
        self.step = 'Idle'

    def InitValues(self):
        return True

    def import_model(self, path, uid):
        self.publish = ThreadedImporter(path, uid, self.progress_callback)
        self.publish.Start()

    def SetModelInfo(self, skfb_model, api):
        self.skfb_model = skfb_model
        self.skfb_api = api
        self.skfb_api.import_callback = self.progress_callback

    def CreateLayout(self):
        # Create the menu
        self.MenuFlushAll()
        # BIG Thumbnail
        use_thumbnail = True
        if use_thumbnail:
            image_container = c4d.BaseContainer() #Create a new container to store the image we will load for the button later on
            image_container.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
            image_container.SetBool(c4d.BITMAPBUTTON_NOBORDERDRAW, True)
            image_container.SetFilename(resultContainerIDStart, self.skfb_model.thumbnail_path)

            self.mybutton = self.AddCustomGui(BTN_VIEW_SKFB, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 10, 10, image_container)
            self.mybutton.SetLayoutMode(c4d.LAYOUTMODE_MINIMIZED)
            self.mybutton.SetImage(str(self.skfb_model.preview_path), False)
            self.mybutton.SetToggleState(False)
            self.AddStaticText(id=3, flags=c4d.BFH_CENTER,
                initw=512, name='Click on image to view model on Sketchfab.com')
        else:
            self.html = self.AddCustomGui(1000, c4d.CUSTOMGUI_HTMLVIEWER, "html", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 405, 720 )
            self.html.SetUrl("https://sketchfab.com/models/{}/embed?autostart=1".format(self.skfb_model.uid), c4d.URL_ENCODING_UTF16)
            self.html.DoAction(c4d.WEBPAGE_REFRESH)

        # Model infos
        self.AddStaticText(id=3, flags=c4d.BFH_LEFT,
            initw=256, name=u'{}'.format(self.skfb_model.title))
        self.AddStaticText(id=3, flags=c4d.BFH_LEFT,
            initw=256, name=u'{}'.format(self.skfb_model.author))

        self.GroupBegin(id=self.PROGRESS_GROUP, flags=c4d.BFH_SCALEFIT|c4d.BFV_TOP, cols=0, rows=1)
        self.AddStaticText(id=3, flags=c4d.BFH_LEFT, initw=50, name='Status: ')
        self.AddStaticText(id=3, flags=c4d.BFH_LEFT, initw=60, name=u'{}'.format(self.step))
        self.AddCustomGui(self.PROGRESSBAR, c4d.CUSTOMGUI_PROGRESSBAR, "", c4d.BFH_SCALEFIT|c4d.BFV_SCALEFIT, 0, 0)
        self.GroupEnd()

        self.AddButton(id=BTN_IMPORT, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=16, name="Import")
        return True

    def Command(self, id, msg):
        if id == BTN_VIEW_SKFB:
            url = Config.SKETCHFAB_URL + '/models/' + self.skfb_model.uid
            webbrowser.open(url)

        if id == BTN_IMPORT:
            self.EnableStatusBar()
            if OVERRIDE_DOWNLOAD:
                self.import_model(MODEL_PATH, self.skfb_model.uid)
            else:
                self.skfb_api.download_model(self.skfb_model.uid)

        return True

    def EnableStatusBar(self):
        progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
        progressMsg[c4d.BFM_STATUSBAR_PROGRESSON] = True
        progressMsg[c4d.BFM_STATUSBAR_PROGRESS] = 0.0

    def StopProgress(self):
        self.SetTimer(0)
        progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
        self.step = 'Done'
        progressMsg.SetBool(c4d.BFM_STATUSBAR_PROGRESSON, False)
        self.SendMessage(self.PROGRESSBAR, progressMsg)
        self.LayoutChanged(GROUP_WRAPPER)

    def InitValues(self):
        self.SetTimer(100)
        return True

    def progress_callback(self, step, current, total):
        real_current = 100 / total * current / 100.0
        self.progress = real_current
        self.step = step
        self.LayoutChanged(GROUP_WRAPPER)

    def Timer(self, msg):
        progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
        progressMsg[c4d.BFM_STATUSBAR_PROGRESSON] = True
        progressMsg[c4d.BFM_STATUSBAR_PROGRESS] = self.progress
        self.SendMessage(self.PROGRESSBAR, progressMsg)

    def Message(self, msg, result):
        if msg.GetId() == c4d.BFM_TIMER_MESSAGE:
            if self.step == 'FINISHED':
                print("CLOSE")
                self.StopProgress()
                return True

        return gui.GeDialog.Message(self, msg, result)

    def AskClose(self):
        self.StopProgress()
        return False