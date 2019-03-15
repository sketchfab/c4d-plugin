
from __future__ import division
import c4d
from c4d import documents, gui, plugins, bitmaps, storage
from c4d.threading import C4DThread

import start
import imp
import textwrap
import requests
from .skfbapi import *
import webbrowser



import time

# enums
UA_HEADER = 30000
UA_ICON = 30001

GROUP_WRAPPER = 50000
GROUP_LOGIN = 50001
GROUP_SEARCH = 50002
GROUP_QUERY = 50003
GROUP_FILTERS = 50004
GROUP_FIVE = 50005
GROUP_RESULTS = 50006
GROUP_LOGIN_CONNECTED = 50007
GROUP_PREVNEXT = 50008

BTN_SEARCH = 10000
BTN_VIEW_SKFB = 10001
BTN_IMPORT = 10002
BTN_NEXT_PAGE = 10003
BTN_PREV_PAGE = 10004
BTN_LOGIN = 10005
BTN_NEXT_PAGE = 10006
BTN_PREV_PAGE = 10007
BTN_CONNECT_SKETCHFAB = 10080

EDITXT_LOGIN_EMAIL = 10008
EDITXT_LOGIN_PASSWORD = 10009

LB_SEARCH_QUERY = 100010
EDITXT_SEARCH_QUERY = 100011
CHK_MY_MODELS = 100012
CHK_IS_PBR = 100013
CHK_IS_STAFFPICK = 100014
CHK_IS_ANIMATED = 100015
CHILD_VALUES = 100016
RDBN_FACE_COUNT = 100017
LB_FACE_COUNT = 100018
LB_SORT_BY = 100019

CBOX_CATEGORY = 100020
CBOX_CATEGORY_ELT = 100021
# 100021 -> 100039 reserved for categories

CBOX_SORT_BY = 100040
CBOX_SORT_BY_ELT = 1000041
# 100041 -> 100044 reserved for orderby

CBOX_FACE_COUNT = 100050
CBOX_FACE_COUNT_ELT = 100051
# 100051 -> 100056 reserved for orderby

TXT_CONNECT_STATUS_CONNECTED = 100054
TXT_CONNECT_STATUS = 100055
TXT_EMAIL = 49999
TXT_PASSWORD = 49999
resultContainerIDStart = 100061 # + 24 since 24 results on page
resultNameIDStart = 100086


OVERRIDE_DOWNLOAD = True
MODEL_PATH = 'D:\\Sketchfab\\repos\\samples\\'
HEADER_PATH = 'D:\\Softwares\\MAXON\\Cinema4DR20\\plugins\\ImportGLTF\\res\\header.png'
TEXT_WIDGET_HEIGHT = 10

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
        path = HEADER_PATH
        result, ismovie = self.bmp.InitWith(path)
        x1 = 0
        y1 = 0
        x2 = self.bmp.GetBw()
        y2 = self.bmp.GetBh()

        if result == c4d.IMAGERESULT_OK:
            self.DrawBitmap(self.bmp, 0, 0, self.bmp.GetBw(), self.bmp.GetBh(),
                            x1, y1, x2, y2, c4d.BMP_NORMALSCALED | c4d.BMP_ALLOWALPHA)

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

    redraw_login = False
    redraw_results = False
    status_widget = None

    def InitValues(self):
        self.SetTimer(20)

        self.SetString(EDITXT_LOGIN_EMAIL, "aurelien+test@sketchfab.com")
        #DEBGUG
        imp.reload(start)
        imp.reload(skfbapi)
        from start import *
        from skfbapi import *

        self.model_dialog = None

        self.SetBool(CHK_IS_STAFFPICK, True)

        self.login = ThreadedLogin(self.skfb_api, None, None, self.refresh)
        self.login.Start()

        # Create the menu
        self.MenuFlushAll()
        self.MenuSubBegin("File")
        self.MenuAddCommand(c4d.IDM_CM_CLOSEWINDOW)
        self.MenuSubEnd()
        self.MenuFinished()

        self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)
        self.draw_login_ui()
        self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)
        self.draw_search_ui()
        self.draw_filters_ui()
        self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)

        return True

    def refresh(self):
        self.redraw_login = True
        self.redraw_results = True

    def Timer(self, msg):
        if self.redraw_results:
            self.resultGroupWillRedraw()

        if self.redraw_login:
            self.draw_login_ui()
            self.redraw_login = False

    def CreateLayout(self):
        self.SetTitle(Config.__plugin_title__)
        self.AddUserArea(UA_HEADER, c4d.BFH_CENTER)
        self.AttachUserArea(self.userarea_paths_header, UA_HEADER)
        self.userarea_paths_header.LayoutChanged()

        # Setup API
        self.skfb_api = SketchfabApi()
        self.skfb_api.request_callback = self.refresh
        self.skfb_api.login_callback = self.draw_login_ui

        return True

    def draw_login_ui(self):
        self.LayoutFlushGroup(GROUP_LOGIN)
        self.GroupBegin(id=GROUP_LOGIN,
                        flags=c4d.BFH_RIGHT,
                        cols=5,
                        rows=1,
                        title="Login",
                        groupflags=c4d.BORDER_NONE)
        # self.AddStaticText(id=TXT_CONNECT_STATUS, flags=c4d.BFH_LEFT, initw=0, inith=0, name='Connect to your user account')
        if hasattr(self, "skfb_api") and self.skfb_api.is_user_logged():
            self.AddStaticText(id=TXT_EMAIL, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Connected as " + self.skfb_api.display_name)
            self.AddButton(id=BTN_CONNECT_SKETCHFAB, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Logout")
        else:
            self.AddStaticText(id=TXT_EMAIL, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Email:")
            self.AddEditText(id=EDITXT_LOGIN_EMAIL, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=350, inith=TEXT_WIDGET_HEIGHT)
            self.AddStaticText(id=TXT_EMAIL, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Password:")
            self.AddEditText(id=EDITXT_LOGIN_PASSWORD, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=350, inith=TEXT_WIDGET_HEIGHT, editflags=c4d.EDITTEXT_PASSWORD)
            self.AddButton(id=BTN_LOGIN, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Login")

        self.GroupEnd()
        self.LayoutChanged(GROUP_LOGIN)

    def refresh_login_ui(self):
        self.LayoutFlushGroup(GROUP_LOGIN)
        self.draw_login_ui()
        self.LayoutChanged(GROUP_LOGIN)

    def draw_search_ui(self):
        self.GroupBegin(id=GROUP_QUERY,
                        flags=c4d.BFH_LEFT | c4d.BFV_FIT,
                        cols=4,
                        rows=1,
                        title="Search",
                        groupflags=c4d.BORDER_NONE)

        mymodels_caption = 'My models ' + str('(PRO)' if not self.skfb_api.is_user_pro else '')
        self.AddStaticText(id=LB_SEARCH_QUERY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=90, inith=TEXT_WIDGET_HEIGHT, name=" Search: ")
        self.AddEditText(id=EDITXT_SEARCH_QUERY, flags=c4d.BFH_LEFT| c4d.BFV_CENTER, initw=500, inith=TEXT_WIDGET_HEIGHT)
        self.AddButton(id=BTN_SEARCH, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Search")
        self.AddCheckbox(id=CHK_MY_MODELS, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=250, inith=TEXT_WIDGET_HEIGHT, name=mymodels_caption)
        self.Enable(CHK_MY_MODELS, self.skfb_api.is_user_pro)
        self.GroupEnd()

    def refresh_search_ui(self):
        self.LayoutFlushGroup(GROUP_QUERY)
        self.draw_search_ui()
        self.LayoutChanged(GROUP_QUERY)

    def draw_filters_ui(self):
        self.GroupBegin(id=GROUP_FILTERS,
                flags=c4d.BFH_SCALEFIT | c4d.BFV_FIT,
                cols=9,
                rows=1,
                title="Search",
                groupflags=c4d.BORDER_NONE)

        # Categories
        self.AddComboBox(id=CBOX_CATEGORY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=250, inith=TEXT_WIDGET_HEIGHT)
        for index, category in enumerate(Config.SKETCHFAB_CATEGORIES):
            self.AddChild(id=CBOX_CATEGORY, subid=CBOX_CATEGORY_ELT + index, child=category[2])
        self.SetInt32(CBOX_CATEGORY, CBOX_CATEGORY_ELT)

        self.AddCheckbox(id=CHK_IS_PBR, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=100, inith=TEXT_WIDGET_HEIGHT, name='PBR')
        self.SetBool(CHK_IS_PBR, False)
        self.AddCheckbox(id=CHK_IS_STAFFPICK, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=120, inith=TEXT_WIDGET_HEIGHT, name='Staffpick')
        self.SetBool(CHK_IS_STAFFPICK, True)
        self.AddCheckbox(id=CHK_IS_ANIMATED, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=150, inith=TEXT_WIDGET_HEIGHT, name='Animated')
        self.SetBool(CHK_IS_ANIMATED, False)

        self.AddStaticText(id=LB_FACE_COUNT, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=90, inith=TEXT_WIDGET_HEIGHT, name="Face count: ")
        self.AddComboBox(id=CBOX_FACE_COUNT, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=250, inith=TEXT_WIDGET_HEIGHT)
        for index, face_count in enumerate(Config.SKETCHFAB_FACECOUNT):
            self.AddChild(id=CBOX_FACE_COUNT, subid=CBOX_FACE_COUNT_ELT + index, child=face_count[1])
        self.SetInt32(CBOX_FACE_COUNT, CBOX_FACE_COUNT_ELT)

        self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
        self.AddStaticText(id=LB_FACE_COUNT, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=90, inith=TEXT_WIDGET_HEIGHT, name="Sort by: ")
        self.AddComboBox(id=CBOX_SORT_BY, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=90, inith=TEXT_WIDGET_HEIGHT)
        for index, sort_by in enumerate(Config.SKETCHFAB_SORT_BY):
            self.AddChild(id=CBOX_SORT_BY, subid=CBOX_SORT_BY_ELT + index, child=sort_by[1])
        self.SetInt32(CBOX_SORT_BY, CBOX_SORT_BY_ELT + 2)

        self.GroupEnd()

    def refresh_filters_ui(self):
        self.LayoutFlushGroup(GROUP_FILTERS)
        self.draw_filters_ui()
        self.LayoutChanged(GROUP_FILTERS)

    def result_valid(self):
        if not 'current' in self.skfb_api.search_results:
            return False

        return True

    def resultGroupWillRedraw(self):
        self.LayoutFlushGroup(GROUP_RESULTS)
        self.draw_results_ui()
    def draw_results_ui(self):
        if hasattr(self, 'skfb_api'):
            if not self.result_valid:
                return

            if not 'current' in self.skfb_api.search_results:
                return

            self.GroupBegin(GROUP_RESULTS, c4d.BFH_SCALEFIT|c4d.BFV_TOP, 6, 4, "Results",0) #id, flags, columns, rows, grouptext, groupflags
            for index, skfb_model in enumerate(self.skfb_api.search_results['current'].values()):
                image_container = c4d.BaseContainer() #Create a new container to store the image we will load for the button later on
                self.GroupBegin(0, c4d.BFH_SCALEFIT|c4d.BFH_SCALEFIT, 1, 2, "Bitmap Example",0)
                fn = c4d.storage.GeGetC4DPath(c4d.C4D_PATH_DESKTOP) #Gets the desktop path
                filenameid = resultContainerIDStart + index
                image_container.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
                image_container.SetBool(c4d.BITMAPBUTTON_NOBORDERDRAW, True)
                image_container.SetFilename(filenameid, str(skfb_model.thumbnail_path))

                self.mybutton = self.AddCustomGui(filenameid, c4d.CUSTOMGUI_BITMAPBUTTON, "Sketchfab model button", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 10, 10, image_container)
                self.mybutton.SetLayoutMode(c4d.LAYOUTMODE_MINIMIZED)
                self.mybutton.SetImage(str(skfb_model.thumbnail_path), False)
                self.mybutton.SetToggleState(True)

                nameid = resultNameIDStart + index
                modelname = textwrap.wrap(skfb_model.title, 18)[0]  # dumbly truncate names for the UI

                self.AddStaticText(id=nameid, flags=c4d.BFV_BOTTOM | c4d.BFH_CENTER,
                        initw=192, inith=16, name=u'{}'.format(modelname), borderstyle=c4d.BORDER_WITH_TITLE)

                self.GroupEnd()

            self.GroupEnd()
            if len(self.skfb_api.search_results['current']) > 0:
                self.LayoutFlushGroup(GROUP_PREVNEXT)
                self.GroupBegin(GROUP_PREVNEXT, c4d.BFH_CENTER, 3, 1, "Prevnext",3) #id, flags, columns, rows, grouptext, groupflags
                self.AddButton(id=BTN_PREV_PAGE, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Previous")
                self.AddSeparatorH(inith=250, flags=c4d.BFH_FIT)
                self.AddButton(id=BTN_NEXT_PAGE, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Next")
                self.GroupEnd()

            self.LayoutChanged(GROUP_RESULTS)
            self.Enable(BTN_PREV_PAGE, self.skfb_api.has_prev())
            self.Enable(BTN_NEXT_PAGE, self.skfb_api.has_next())
            self.LayoutChanged(GROUP_PREVNEXT)
            self.redraw_results = False

    def trigger_default_search(self):
        self.skfb_api.search(Config.DEFAULT_SEARCH)

    def trigger_search(self):
        final_query = Config.BASE_SEARCH

        if self.GetString(EDITXT_SEARCH_QUERY) and not OVERRIDE_DOWNLOAD:
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

        if id == BTN_CONNECT_SKETCHFAB:
            self.skfb_api.logout()
            self.refresh()

        if id == BTN_LOGIN:
            self.skfb_api.login(self.GetString(EDITXT_LOGIN_EMAIL), self.GetString(EDITXT_LOGIN_PASSWORD))

        if id == BTN_PREV_PAGE:
            self.skfb_api.search_prev()

        if id == BTN_NEXT_PAGE:
            self.skfb_api.search_next()

        bc = c4d.BaseContainer()
        if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.KEY_ENTER,bc):
            if bc[c4d.BFM_INPUT_VALUE] == 1:
                if self.IsActive(EDITXT_SEARCH_QUERY):
                    trigger_search = True

        if id == BTN_SEARCH:
            trigger_search = True

        if id == CBOX_CATEGORY:
            trigger_search = True

        if id == CBOX_SORT_BY:
            trigger_search = True

        if id == CBOX_FACE_COUNT:
            trigger_search = True

        if id == CHK_IS_PBR:
            trigger_search = True

        if id == CHK_IS_ANIMATED:
            trigger_search = True

        if id == CHK_IS_STAFFPICK:
            trigger_search = True

        if trigger_search:
            self.trigger_search()

        for i in range(24):
            if id == resultContainerIDStart + i:
                self.skfb_api.request_model_info(self.skfb_api.search_results['current'].values()[i].uid)
                self.model_dialog = SkfbModelDialog()
                self.model_dialog.SetModelInfo(self.skfb_api.search_results['current'].values()[i], self.skfb_api)
                self.model_dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC , defaultw=450, defaulth=300, xpos=-1, ypos=-1)

        return True

class SkfbModelDialog(gui.GeDialog):

    skfb_model = None
    PROGRESSBAR = 1001
    PROGRESS_GROUP = 1000
    IMG_MODEL_THUMBNAIL = 1010
    LB_MODEL_NAME = 1011
    LB_MODEL_AUTHOR = 1012
    LB_MODEL_LICENCE = 1013
    LB_VERTEX_COUNT = 1014
    LB_FACE_COUNT = 1015
    LB_ANIMATION_COUNT = 1016

    GRP_MODEL_INFO_1 = 1020
    GRP_MODEL_INFO_2 = 1021
    GRP_MODEL_INFO_3 = 1022

    def __init__(self):
        self.progress = 0
        self.step = ''

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

            self.mybutton = self.AddCustomGui(2, c4d.CUSTOMGUI_BITMAPBUTTON, "Sketchfab thumbnail Button", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 10, 10, image_container)
            self.mybutton.SetLayoutMode(c4d.LAYOUTMODE_MINIMIZED)
            self.mybutton.SetImage(str(self.skfb_model.preview_path), False)
            self.mybutton.SetToggleState(False)
            self.AddButton(id=BTN_VIEW_SKFB, flags=c4d.BFH_CENTER | c4d.BFV_TOP, initw=150, inith=16, name="View on Sketchfab")
        else:
            self.html = self.AddCustomGui(1000, c4d.CUSTOMGUI_HTMLVIEWER, "html", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 405, 720 )
            self.html.SetUrl("https://sketchfab.com/models/{}/embed?autostart=1".format(self.skfb_model.uid), c4d.URL_ENCODING_UTF16)
            self.html.DoAction(c4d.WEBPAGE_REFRESH)

        # Model infos
        self.GroupBegin(self.GRP_MODEL_INFO_1, c4d.BFH_CENTER|c4d.BFV_TOP, 3, 1, "Results",0) #id, flags, columns, rows, grouptext, groupflags
        self.AddStaticText(id=self.LB_MODEL_NAME, flags=c4d.BFH_LEFT,
            initw=500, name=u'Title:         {}'.format(self.skfb_model.title))
        self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
        self.AddStaticText(id=self.LB_VERTEX_COUNT, flags=c4d.BFH_RIGHT,
            initw=500, name=u'          Vertex Count:    {}'.format(Utils.humanify_number(self.skfb_model.vertex_count)))
        self.GroupEnd()

        self.GroupBegin(self.GRP_MODEL_INFO_2, c4d.BFH_CENTER|c4d.BFV_TOP, 3, 1, "Results",0) #id, flags, columns, rows, grouptext, groupflags
        self.AddStaticText(id=self.LB_MODEL_AUTHOR, flags=c4d.BFH_LEFT,
            initw=500, name=u'Author:    {}'.format(self.skfb_model.author))
        self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
        self.AddStaticText(id=self.LB_FACE_COUNT, flags=c4d.BFH_RIGHT,
            initw=500, name=u'          Face Count:       {}'.format(Utils.humanify_number(self.skfb_model.face_count)))
        self.GroupEnd()

        self.GroupBegin(self.GRP_MODEL_INFO_3, c4d.BFH_CENTER|c4d.BFV_TOP, 3, 1, "Results",0) #id, flags, columns, rows, grouptext, groupflags
        self.AddStaticText(id=self.LB_MODEL_LICENCE, flags=c4d.BFH_LEFT,
            initw=500, name=u'License:    {}'.format(self.skfb_model.license))
        self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
        self.AddStaticText(id=self.LB_ANIMATION_COUNT, flags=c4d.BFH_RIGHT,
            initw=500, name=u'          Animated:          {}'.format(self.skfb_model.animated))
        self.GroupEnd()

        self.AddEditText(id=EDITXT_SEARCH_QUERY, flags=c4d.BFH_LEFT| c4d.BFV_CENTER, initw=500, inith=TEXT_WIDGET_HEIGHT)

        self.GroupBegin(id=self.PROGRESS_GROUP, flags=c4d.BFH_CENTER|c4d.BFV_CENTER, cols=1, rows=3)
        self.AddStaticText(id=3, flags=c4d.BFH_LEFT, initw=60, inith=0, name=u'{}'.format(self.step))
        self.AddButton(id=BTN_IMPORT, flags=c4d.BFH_CENTER | c4d.BFV_CENTER, initw=200, inith=38, name="IMPORT MODEL")
        #self.AddStaticText(id=3, flags=c4d.BFH_LEFT, initw=60, inith=30, name=u'{}'.format(self.step))
        self.AddCustomGui(self.PROGRESSBAR, c4d.CUSTOMGUI_PROGRESSBAR, "", c4d.BFH_SCALEFIT, 0, 0)
        self.GroupEnd()

        return True

    def Command(self, id, msg):
        if id == BTN_VIEW_SKFB:
            url = Config.SKETCHFAB_URL + '/models/' + self.skfb_model.uid
            webbrowser.open(url)

        if id == BTN_IMPORT:
            self.EnableStatusBar()
            if OVERRIDE_DOWNLOAD:
                query = self.GetString(EDITXT_SEARCH_QUERY)
                path = os.path.join(MODEL_PATH, query)
                for file in os.listdir(path):
                    if os.path.splitext(file)[-1] in ('.gltf', '.glb'):
                        self.skfb_api.import_model(os.path.join(path, file), self.skfb_model.uid)
                else:
                    print('NOPATH')
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