
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
BTN_SEARCH = 100001
BTN_VIEW_SKFB = 100002
BTN_IMPORT = 100003

TXT_SEARCH_QUERY = 100003
EDITXT_MSEARCH_QUERY = 100004

CHK_IS_PBR = 100017
CHK_IS_STAFFPICK = 100017
CHK_IS_ANIMATED = 100017

MODEL_WINDOW_DIALOG = 200051

class SkfbPluginDialog(gui.GeDialog):

    def InitValues(self):
        print("Initializing")
        #DEBGUG
        imp.reload(start)
        imp.reload(skfbapi)
        from start import *
        from skfbapi import *

        self.skfb_api = SketchfabApi()
        self.skfb_api.import_callback = self.import_model
        self.skfb_api.login(" ")
        self.buttons = []
        self.containers = []
        self.model_dialog = None

        return True

    def import_model(self, path, uid):
        ImportGLTF.run(path, uid)

    def CreateLayout(self):
        self.SetTitle(Config.__plugin_title__)

        # Create the menu
        self.MenuFlushAll()

        # Options menu
        self.MenuSubBegin("File")
        self.MenuAddCommand(c4d.IDM_CM_CLOSEWINDOW)
        self.MenuSubEnd()

        self.AddButton(id=BTN_SEARCH, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=16, name="Import")

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
        # self.AddStaticText(id=TXT_MODEL_NAME, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Model name:")
        # self.AddEditText(id=EDITXT_MODEL_TITLE, flags=c4d.BFH_SCALEFIT, initw=0, inith=0)
        # self.SetString(EDITXT_MODEL_TITLE, docname)

        # self.AddStaticText(id=TXT_DESCRIPTION, flags=c4d.BFH_LEFT | c4d.BFV_TOP,
        #                    initw=0, inith=0, name="Description:")
        # self.AddMultiLineEditText(id=EDITXT_DESCRIPTION, flags=c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
        #                           initw=0, inith=100, style=c4d.DR_MULTILINE_WORDWRAP)
        # self.SetString(EDITXT_DESCRIPTION, docname)

        # self.AddStaticText(id=TXT_TAGS, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Tags: cinema4d ")
        # self.AddEditText(id=EDITXT_TAGS, flags= c4d.BFH_RIGHT | c4d.BFH_SCALEFIT, initw=0, inith=0)

        # self.AddCheckbox(id=CHK_ANIMATION, flags=c4d.BFH_LEFT,
        #                  initw=0, inith=0, name="Enable animation")

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

        self.GroupBegin(0, c4d.BFH_SCALEFIT|c4d.BFH_SCALEFIT, 6, 4, "Bitmap Example",0) #id, flags, columns, rows, grouptext, groupflags
        # self.GroupBorder(c4d.BORDER_BLACK)

        if not self.result_valid:
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
            image_container.SetFilename(filenameid, skfb_model.thumbnail_path)

            self.mybutton = self.AddCustomGui(filenameid, c4d.CUSTOMGUI_BITMAPBUTTON, "Bitmap Button", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 10, 10, image_container)
            self.mybutton.SetLayoutMode(c4d.LAYOUTMODE_MINIMIZED)
            self.mybutton.SetImage(str(skfb_model.thumbnail_path), False)
            self.mybutton.SetToggleState(True)

            self.AddStaticText(id=3, flags=c4d.BFH_CENTER,
                   initw=Config.UI_THUMBNAIL_RESOLUTION, inith=32, name='{}'.format(skfb_model.title))
            self.GroupEnd()

        self.GroupEnd()
        self.LayoutChanged(GROUP_WRAPPER)

    def Command(self, id, msg):
        if id == BTN_SEARCH:
            self.skfb_api.search(Config.DEFAULT_SEARCH)
            self.resultGroupWillRedraw()

        for i in range(24):
            if id == resultContainerIDStart + i:
                print('ENABLED BUTTON  {}'.format(i))
                self.model_dialog = SkfbModelDialog()
                self.model_dialog.SetModelInfo(self.skfb_api.search_results['current'].values()[i], self.skfb_api)
                self.model_dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL_RESIZEABLE , defaultw=450, defaulth=300, xpos=-1, ypos=-1)

        return True


class SkfbModelDialog(gui.SubDialog):

    skfb_model = None

    def InitValues(self):
        return True

    def SetModelInfo(self, skfb_model, api):
        self.skfb_model = skfb_model
        self.skfb_api = api

    def CreateLayout(self):
        self.SetTitle("MODEL PAGE")

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
            initw=256, name='{}'.format(self.skfb_model.title))
        self.AddStaticText(id=3, flags=c4d.BFH_LEFT,
            initw=256, name=u'{}'.format(self.skfb_model.author))

        self.AddButton(id=BTN_IMPORT, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=16, name="Import")

        return True

    def Command(self, id, msg):
        if id == BTN_VIEW_SKFB:
            url = Config.SKETCHFAB_URL + '/models/' + self.skfb_model.uid
            webbrowser.open(url)

        if id == BTN_IMPORT:
            self.skfb_api.download_model(self.skfb_model.uid)

        return True