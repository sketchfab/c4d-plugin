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

__importer_id__    = 1052778
__importer_title__ = "Sketchfab Importer"

import textwrap
import webbrowser
import os

# C4D modules
import c4d
from c4d import gui

# Plugins modules
from import_gltf import ImportGLTF
from config import Config
from utils import Utils

import ui_login


# enums
UI_PROGRESSBAR = 1002

# Groups
GROUP_QUERY = 2003
GROUP_FILTERS = 24004
GROUP_RESULTS_SCROLL = 2006
GROUP_RESULTS = 2007
GROUP_PREVNEXT = 2009
# Model window
GROUP_MODEL_WINDOW = 2014
GROUP_MODEL_INFO = 2015
GROUP_MODEL_IMPORT = 2016
GROUP_MODEL_PROGRESS = 2017

# Buttons
BTN_SEARCH = 2100
BTN_VIEW_SKFB = 2101
BTN_IMPORT = 2102
BTN_NEXT_PAGE = 2103
BTN_PREV_PAGE = 2104

# Labels
LB_SEARCH_QUERY = 2200
LB_FACE_COUNT = 2202
LB_SORT_BY = 2203
LB_RESULT_NAME_START = 2209
# Model Window
LB_MODEL_NAME = 2210
LB_MODEL_AUTHOR = 2211
LB_MODEL_LICENCE = 2212
LB_MODEL_VERTEX_COUNT = 2213
LB_MODEL_FACE_COUNT = 2214
LB_MODEL_ANIMATION_COUNT = 2215
LB_MODEL_STEP = 2216

EDITXT_SEARCH_QUERY = 2302
CBOX_SEARCH_DOMAIN = 2303
CBOX_SEARCH_DOMAIN_ELT = 2304

# Checkboxes
CHK_MY_MODELS = 2400
CHK_IS_PBR = 2401
CHK_IS_STAFFPICK = 2402
CHK_IS_ANIMATED = 2403
CHILD_VALUES = 2404

# Comboboxes
CBOX_CATEGORY = 2500
CBOX_CATEGORY_ELT = 2501
# 2501 -> 2519 reserved for categories

CBOX_SORT_BY = 2520
CBOX_SORT_BY_ELT = 2521
# 2521 -> 2524 reserved for orderby

CBOX_FACE_COUNT = 2525
CBOX_FACE_COUNT_ELT = 2526
# 2526 -> 2531 reserved for orderby

resultContainerIDStart = 2600  # + 24 since 24 results on page

TEXT_WIDGET_HEIGHT = 10


class SkfbPluginDialog(ui_login.SketchfabDialogWithLogin):

	redraw_results = False

	def InitValues(self):
		super(SkfbPluginDialog, self).InitValues()
		self.model_dialog = None
		self.SetBool(CHK_IS_STAFFPICK, True)
		self.userarea_paths_header.set_img(os.path.join(Config.PLUGIN_DIRECTORY, 'res', 'Sketchfab_Logo_importer.png'))
		return True

	def refresh(self):
		self.redraw_login   = True
		self.redraw_results = True

	def refresh_login_ui(self):
		self.draw_login_ui()
		self.draw_search_ui()
		#if self.model_dialog:
		#	self.model_dialog.refresh_window()

	def Timer(self, msg):
		if self.redraw_results:
			self.resultGroupWillRedraw()

		if self.redraw_login:
			self.draw_login_ui()
			self.redraw_login = False

	def CreateLayout(self):

		# Title
		self.SetTitle(__importer_title__)

		# Main UI
		super(SkfbPluginDialog, self).CreateLayout()
		self.skfb_api.request_callback = self.refresh
		self.skfb_api.login_callback   = self.refresh_login_ui

		# Toggle CHK_My8models
		if self.is_initialized:
			self.Enable(CHK_MY_MODELS, self.skfb_api.is_user_logged())

		self.GroupBegin(id=GROUP_QUERY,
						flags=c4d.BFH_CENTER | c4d.BFV_FIT,
						cols=4,
						rows=1,
						title="Search",
						groupflags=c4d.BORDER_NONE)

		self.draw_search_ui()

		self.GroupEnd()

		self.GroupBegin(id=GROUP_FILTERS,
						flags=c4d.BFH_SCALEFIT | c4d.BFV_FIT,
						cols=9,
						rows=1,
						title="Search",
						groupflags=c4d.BORDER_NONE | c4d.BFV_BORDERGROUP_FOLD_OPEN)

		self.GroupBorderSpace(6, 6, 6, 6)

		self.draw_filters_ui()

		self.GroupEnd()

		self.AddSeparatorH(initw=0, flags=c4d.BFH_FIT)

		self.GroupBegin(GROUP_PREVNEXT, c4d.BFH_FIT | c4d.BFV_CENTER, 3, 1, "Prevnext")
		self.GroupBorderSpace(4, 2, 4, 2)
		self.draw_prev_next()
		self.GroupEnd()


		warning = self.needs_warning()
		if self.is_initialized and warning:
			self.draw_warning_ui(warning)
		else:
			self.ScrollGroupBegin(GROUP_RESULTS_SCROLL, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, c4d.SCROLLGROUP_VERT | c4d.SCROLLGROUP_HORIZ | c4d.SCROLLGROUP_AUTOHORIZ | c4d.SCROLLGROUP_AUTOVERT, 200, 200)
			self.GroupBegin(GROUP_RESULTS, c4d.BFH_SCALEFIT | c4d.BFV_TOP, 6, 4, "Results", c4d.BFV_GRIDGROUP_EQUALCOLS | c4d.BFV_GRIDGROUP_EQUALROWS)
			self.GroupBorderSpace(6, 2, 6, 2)
			self.draw_results_ui()
			self.GroupEnd()
			self.GroupEnd()

		self.draw_footer()

		self.trigger_default_search()

		return True

	def draw_search_ui(self):
		self.LayoutFlushGroup(GROUP_QUERY)

		self.AddStaticText(id=LB_SEARCH_QUERY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=90, inith=TEXT_WIDGET_HEIGHT, name=" Search: ")
		self.AddComboBox(id=CBOX_SEARCH_DOMAIN, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=150, inith=TEXT_WIDGET_HEIGHT)
		for index, category in enumerate(Config.SKETCHFAB_SEARCH_DOMAINS):
			self.AddChild(id=CBOX_SEARCH_DOMAIN, subid=CBOX_SEARCH_DOMAIN_ELT + index, child=category[2])
		self.SetInt32(CBOX_SEARCH_DOMAIN, CBOX_SEARCH_DOMAIN_ELT)
		self.AddEditText(id=EDITXT_SEARCH_QUERY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=500, inith=TEXT_WIDGET_HEIGHT)
		self.AddButton(id=BTN_SEARCH, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Search")
		self.Enable(CBOX_SEARCH_DOMAIN, int(self.skfb_api.is_user_logged()))

		self.LayoutChanged(GROUP_QUERY)

	def refresh_search_ui(self):
		self.draw_search_ui()

	def draw_filters_ui(self):
		self.LayoutFlushGroup(GROUP_FILTERS)

		# Categories
		self.AddComboBox(id=CBOX_CATEGORY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=250, inith=TEXT_WIDGET_HEIGHT)
		for index, category in enumerate(Config.SKETCHFAB_CATEGORIES):
			self.AddChild(id=CBOX_CATEGORY, subid=CBOX_CATEGORY_ELT + index, child=category[2])
		self.SetInt32(CBOX_CATEGORY, CBOX_CATEGORY_ELT)

		self.AddCheckbox(id=CHK_IS_PBR, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=80, inith=TEXT_WIDGET_HEIGHT, name='PBR')
		self.SetBool(CHK_IS_PBR, False)
		self.AddCheckbox(id=CHK_IS_STAFFPICK, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=120, inith=TEXT_WIDGET_HEIGHT, name='Staffpick')
		self.SetBool(CHK_IS_STAFFPICK, False)
		self.AddCheckbox(id=CHK_IS_ANIMATED, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=150, inith=TEXT_WIDGET_HEIGHT, name='Animated')
		self.SetBool(CHK_IS_ANIMATED, False)

		self.AddStaticText(id=LB_FACE_COUNT, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=90, inith=TEXT_WIDGET_HEIGHT, name="Face count: ")
		self.AddComboBox(id=CBOX_FACE_COUNT, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=120, inith=TEXT_WIDGET_HEIGHT)
		for index, face_count in enumerate(Config.SKETCHFAB_FACECOUNT):
			self.AddChild(id=CBOX_FACE_COUNT, subid=CBOX_FACE_COUNT_ELT + index, child=face_count[1])
		self.SetInt32(CBOX_FACE_COUNT, CBOX_FACE_COUNT_ELT)

		self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
		self.AddStaticText(id=LB_FACE_COUNT, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=60, inith=TEXT_WIDGET_HEIGHT, name="Sort by: ")
		self.AddComboBox(id=CBOX_SORT_BY, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=90, inith=TEXT_WIDGET_HEIGHT)
		for index, sort_by in enumerate(Config.SKETCHFAB_SORT_BY):
			self.AddChild(id=CBOX_SORT_BY, subid=CBOX_SORT_BY_ELT + index, child=sort_by[1])
		self.SetInt32(CBOX_SORT_BY, CBOX_SORT_BY_ELT + 3)

		self.LayoutChanged(GROUP_FILTERS)

	def refresh_filters_ui(self):
		self.draw_filters_ui()

	def result_valid(self):
		if 'current' not in self.skfb_api.search_results:
			return False

		return True

	def needs_warning(self):
		"""
		returns 0 if no warning is needed, the warning code otherwise:
		1 - Normal search, no results
		2 - Own models but not pro
		3 - No Store purchases
		"""

		if not self.result_valid():
			return 0

		search_domain = self.GetInt32(CBOX_SEARCH_DOMAIN) - CBOX_SEARCH_DOMAIN_ELT
		if search_domain == 1 and not self.skfb_api.is_user_pro:
			return 2

		n_results = len(self.skfb_api.search_results['current'])
		if n_results == 0:
			if search_domain in [0,1]:
				return 1
			else:
				return 3
		else:
			return 0

	def resultGroupWillRedraw(self):
		self.draw_prev_next()
		self.draw_results_ui()

	def draw_results_ui(self):
		self.LayoutFlushGroup(GROUP_RESULTS)
		if not self.result_valid():
			return

		# Warning message
		warning = self.needs_warning()
		if warning:
			self.draw_warning_ui(warning)

		for index, skfb_model in enumerate(self.skfb_api.search_results['current'].values()):
			image_container = c4d.BaseContainer()  # Create a new container to store the image we will load for the button later on
			self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFH_SCALEFIT, 1, 2, "Bitmap Example", 0)
			filenameid = resultContainerIDStart + index
			image_container.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
			image_container.SetBool(c4d.BITMAPBUTTON_NOBORDERDRAW, True)
			image_container.SetFilename(filenameid, str(skfb_model.thumbnail_path))

			self.mybutton = self.AddCustomGui(filenameid, c4d.CUSTOMGUI_BITMAPBUTTON, "Sketchfab model button", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 10, 10, image_container)
			self.mybutton.SetLayoutMode(c4d.LAYOUTMODE_MINIMIZED)
			self.mybutton.SetImage(str(skfb_model.thumbnail_path), False)
			self.mybutton.SetToggleState(True)

			nameid = LB_RESULT_NAME_START + index
			modelname = textwrap.wrap(skfb_model.title, 18)[0]  # dumbly truncate names for the UI

			self.AddStaticText(id=nameid,
							   flags=c4d.BFV_BOTTOM | c4d.BFH_CENTER,
							   initw=192,
							   inith=16,
							   name=u'{}'.format(modelname),
							   borderstyle=c4d.BORDER_WITH_TITLE)

			self.GroupEnd()

		self.LayoutChanged(GROUP_RESULTS)

		self.Enable(BTN_PREV_PAGE, self.skfb_api.has_prev())
		self.Enable(BTN_NEXT_PAGE, self.skfb_api.has_next())

		self.redraw_results = False

	def draw_prev_next(self):
		self.LayoutFlushGroup(GROUP_PREVNEXT)

		if self.result_valid() and len(self.skfb_api.search_results['current']) > 0:
			self.AddButton(id=BTN_PREV_PAGE, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Previous")
			self.AddSeparatorV(0.0, flags=c4d.BFH_SCALE)
			self.AddButton(id=BTN_NEXT_PAGE, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Next")
			self.Enable(BTN_PREV_PAGE, self.skfb_api.has_prev())
			self.Enable(BTN_NEXT_PAGE, self.skfb_api.has_next())

		self.LayoutChanged(GROUP_PREVNEXT)

	def trigger_default_search(self):
		self.skfb_api.search(Config.DEFAULT_SEARCH)

	def trigger_search(self):
		search_domain_str = Config.SKETCHFAB_SEARCH_DOMAINS[self.GetInt32(CBOX_SEARCH_DOMAIN) - CBOX_SEARCH_DOMAIN_ELT][0]
		final_query = Config.SKETCHFAB_API + '/v3' + search_domain_str

		if self.GetString(EDITXT_SEARCH_QUERY):
			final_query = final_query + '&q={}'.format(self.GetString(EDITXT_SEARCH_QUERY))

		if self.GetBool(CHK_IS_ANIMATED):
			final_query = final_query + '&animated=true'

		if self.GetBool(CHK_IS_STAFFPICK):
			final_query = final_query + '&staffpicked=true'

		if self.GetInt32(CBOX_SORT_BY) == CBOX_SORT_BY_ELT + 1:
			final_query = final_query + '&sort_by=-likeCount'
		elif self.GetInt32(CBOX_SORT_BY) == CBOX_SORT_BY_ELT + 2:
			final_query = final_query + '&sort_by=-viewCount'
		elif self.GetInt32(CBOX_SORT_BY) == CBOX_SORT_BY_ELT + 3:
			final_query = final_query + '&sort_by=-publishedAt'

		if self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 1:
			final_query = final_query + '&min_face_count=1&max_face_count=10000'
		elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 2:
			final_query = final_query + '&min_face_count=10000&max_face_count=50000'
		elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 3:
			final_query = final_query + '&min_face_count=50000&max_face_count=100000'
		elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 4:
			final_query = final_query + "&min_face_count=100000&max_face_count=250000"
		elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 5:
			final_query = final_query + "&min_face_count=250000"
		else:
			final_query = final_query + "&min_face_count=1"

		if self.GetInt32(CBOX_CATEGORY) != CBOX_CATEGORY_ELT:
			final_query = final_query + '&categories={}'.format(Config.SKETCHFAB_CATEGORIES[self.GetInt32(CBOX_CATEGORY) - CBOX_CATEGORY_ELT][0])

		if self.GetBool(CHK_IS_PBR):
			final_query = final_query + '&pbr_type=true'

		self.skfb_api.search(final_query)

	def reset_filters(self, is_own_model):
		self.SetBool(CHK_IS_STAFFPICK, not is_own_model)
		self.SetBool(CHK_IS_ANIMATED, False)
		self.SetBool(CHK_IS_PBR, False)
		self.SetInt32(CBOX_CATEGORY, CBOX_CATEGORY_ELT)
		self.SetInt32(CBOX_FACE_COUNT, CBOX_FACE_COUNT_ELT)
		self.SetInt32(CBOX_SORT_BY, CBOX_SORT_BY_ELT + 1)

	def Command(self, id, msg):
		trigger_search = False

		self.common_commands(id, msg)

		if id == BTN_PREV_PAGE:
			self.skfb_api.search_prev()

		if id == BTN_NEXT_PAGE:
			self.skfb_api.search_next()

		bc = c4d.BaseContainer()
		if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.KEY_ENTER, bc):
			if bc[c4d.BFM_INPUT_VALUE] == 1:
				if self.IsActive(EDITXT_SEARCH_QUERY):
					trigger_search = True

		if id in [
			BTN_SEARCH,
			CBOX_SEARCH_DOMAIN,
			CBOX_CATEGORY,
			CBOX_SORT_BY,
			CBOX_FACE_COUNT,
			CHK_IS_PBR,
			CHK_IS_ANIMATED,
			CHK_IS_STAFFPICK]:
			trigger_search = True

		if id == CBOX_SEARCH_DOMAIN:
			self.Enable(GROUP_FILTERS, (self.GetInt32(CBOX_SEARCH_DOMAIN) - CBOX_SEARCH_DOMAIN_ELT) != 2)
			self.refresh_filters_ui()

		if trigger_search:
			self.trigger_search()

		for i in range(24):
			if id == resultContainerIDStart + i:
				if self.model_dialog:
					self.model_dialog.Close()

				model = list(self.skfb_api.search_results['current'].values())[i]
				self.skfb_api.request_model_info(model.uid)
				self.model_dialog = SkfbModelDialog()
				self.model_dialog.SetModelInfo(model, self.skfb_api)
				self.model_dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC, defaultw=450, defaulth=300, xpos=-1, ypos=-1)

		return True


class SkfbModelDialog(gui.GeDialog):
	skfb_model = None

	def __init__(self):
		self.progress = 0
		self.step = ''
		self.status = ''
		self.importer = None

	def SetModelInfo(self, skfb_model, api):
		self.skfb_model = skfb_model
		self.skfb_api = api
		self.skfb_api.import_callback = self.progress_callback

		self.Enable(BTN_IMPORT, self.skfb_api.is_user_logged())

	def CreateLayout(self):
		# Create the menu
		self.MenuFlushAll()

		self.GroupBegin(GROUP_MODEL_WINDOW, c4d.BFH_CENTER | c4d.BFV_TOP, 1, 1, "Model Window")
		self.draw_model_window()
		self.GroupEnd()

		self.GroupBegin(GROUP_MODEL_INFO, c4d.BFH_CENTER | c4d.BFV_TOP, 3, 3, "Results", 0)
		self.draw_model_details()
		self.GroupEnd()

		self.GroupBegin(GROUP_MODEL_IMPORT, c4d.BFH_CENTER | c4d.BFV_CENTER, 1, 3)
		self.draw_model_import()
		self.GroupEnd()

		self.GroupBegin(GROUP_MODEL_PROGRESS, c4d.BFH_SCALEFIT | c4d.BFV_CENTER, 1, 3)
		self.draw_model_progress()
		self.GroupEnd()

		self.Enable(BTN_IMPORT, self.skfb_api.is_user_logged())
		return True

	def draw_model_window(self):
		self.LayoutFlushGroup(GROUP_MODEL_WINDOW)

		# BIG Thumbnail
		use_thumbnail = True
		if use_thumbnail:
			image_container = c4d.BaseContainer()  # Create a new container to store the image we will load for the button later on
			image_container.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
			image_container.SetBool(c4d.BITMAPBUTTON_NOBORDERDRAW, True)
			image_container.SetFilename(resultContainerIDStart, self.skfb_model.thumbnail_path)

			self.mybutton = self.AddCustomGui(2, c4d.CUSTOMGUI_BITMAPBUTTON, "Sketchfab thumbnail Button", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 10, 10, image_container)
			self.mybutton.SetLayoutMode(c4d.LAYOUTMODE_MINIMIZED)
			self.mybutton.SetImage(str(self.skfb_model.preview_path), False)
			self.mybutton.SetToggleState(False)

			self.AddButton(id=BTN_VIEW_SKFB, flags=c4d.BFH_CENTER | c4d.BFV_TOP, initw=150, inith=16, name="View on Sketchfab")
		else:
			self.html = self.AddCustomGui(1000, c4d.CUSTOMGUI_HTMLVIEWER, "html", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 405, 720)
			self.html.SetUrl("https://sketchfab.com/models/{}/embed?autostart=1".format(self.skfb_model.uid), c4d.URL_ENCODING_UTF16)
			self.html.DoAction(c4d.WEBPAGE_REFRESH)

		self.LayoutChanged(GROUP_MODEL_WINDOW)

	def draw_model_details(self):
		self.LayoutFlushGroup(GROUP_MODEL_INFO)

		self.AddStaticText(id=LB_MODEL_NAME, flags=c4d.BFH_LEFT,
						   initw=500,
						   name=u'Title:         {}'.format(self.skfb_model.title))

		self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
		self.AddStaticText(id=LB_MODEL_VERTEX_COUNT,
						   flags=c4d.BFH_RIGHT,
						   initw=500,
						   name=u'          Vertex Count:    {}'.format(Utils.humanify_number(self.skfb_model.vertex_count)))

		self.AddStaticText(id=LB_MODEL_AUTHOR, flags=c4d.BFH_LEFT,
						   initw=500,
						   name=u'Author:    {}'.format(self.skfb_model.author))

		self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
		self.AddStaticText(id=LB_MODEL_FACE_COUNT, flags=c4d.BFH_RIGHT,
						   initw=500,
						   name=u'          Face Count:       {}'.format(Utils.humanify_number(self.skfb_model.face_count)))

		self.AddStaticText(id=LB_MODEL_LICENCE, flags=c4d.BFH_LEFT,
						   initw=500,
						   name=u'License:    {}'.format(self.skfb_model.license))
		self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
		self.AddStaticText(id=LB_MODEL_ANIMATION_COUNT, flags=c4d.BFH_RIGHT,
						   initw=500,
						   name=u'          Animated:          {}'.format(self.skfb_model.animated))

		self.LayoutChanged(GROUP_MODEL_INFO)

	def draw_model_import(self):
		self.LayoutFlushGroup(GROUP_MODEL_IMPORT)

		self.Enable(BTN_IMPORT, self.skfb_api.is_user_logged())
		self.AddStaticText(id=LB_MODEL_STEP, flags=c4d.BFH_SCALEFIT, initw=250, inith=TEXT_WIDGET_HEIGHT)
		caption = self.GetString(BTN_IMPORT)
		caption = self.status

		if not caption:
			caption = "IMPORT MODEL" if self.skfb_api.is_user_logged() else "You need to be logged in"
		if self.skfb_model is not None and self.skfb_model.download_size:
			caption += " (" + self.skfb_model.download_size + ")"

		self.AddButton(id=BTN_IMPORT, flags=c4d.BFH_CENTER | c4d.BFV_CENTER, initw=200, inith=38, name=caption)
		self.LayoutChanged(GROUP_MODEL_IMPORT)

	def draw_model_progress(self):
		self.LayoutFlushGroup(GROUP_MODEL_PROGRESS)
		self.AddCustomGui(UI_PROGRESSBAR, c4d.CUSTOMGUI_PROGRESSBAR, "", c4d.BFH_SCALEFIT, 0, 0)
		self.LayoutChanged(GROUP_MODEL_PROGRESS)

	def set_status(self, status):
		self.step = status
		self.SetString(BTN_IMPORT, status)

	def refresh_window(self):
		self.draw_model_import()

	def Command(self, id, msg):
		if id == BTN_VIEW_SKFB:
			url = Config.SKETCHFAB_URL + '/models/' + self.skfb_model.uid
			webbrowser.open(url)

		if id == BTN_IMPORT:
			self.EnableStatusBar()
			self.set_status('Downloading')
			self.download_model()

		return True

	def download_model(self):
		model_url = self.skfb_api.request_model_url(self.skfb_model.uid)
		if not model_url:
			return

		filepath = self.skfb_api.get_archive(model_url, self.progress_callback)
		if os.path.exists(filepath):
			self.import_model(filepath, self.skfb_model.uid)

	def import_model(self, filepath, uid):
		self.set_status('Importing model..')
		self.importer = ImportGLTF(self.progress_callback)
		self.importer.run(filepath, uid)

	def EnableStatusBar(self):
		progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
		progressMsg[c4d.BFM_STATUSBAR_PROGRESSON] = True
		progressMsg[c4d.BFM_STATUSBAR_PROGRESS] = 0.2

	def progress_callback(self, step, current, total):
		real_current = 100 / total * current / 100.0
		self.progress = real_current

		progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
		progressMsg[c4d.BFM_STATUSBAR_PROGRESSON] = True
		progressMsg[c4d.BFM_STATUSBAR_PROGRESS] = self.progress
		self.SendMessage(UI_PROGRESSBAR, progressMsg)

		if step != self.step:
			self.step = step
			self.status = step

		if self.importer and self.importer.is_done:
			self.StopProgress()

	def StopProgress(self):
		self.set_status('IMPORT MODEL')
		progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
		progressMsg.SetBool(c4d.BFM_STATUSBAR_PROGRESSON, False)
		self.SendMessage(UI_PROGRESSBAR, progressMsg)

	def Timer(self, msg):
		progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
		progressMsg[c4d.BFM_STATUSBAR_PROGRESSON] = True
		progressMsg[c4d.BFM_STATUSBAR_PROGRESS] = self.progress
		self.SendMessage(UI_PROGRESSBAR, progressMsg)
		self.refresh_window()

	def Message(self, msg, result):
		if msg.GetId() == c4d.BFM_TIMER_MESSAGE:
			if self.step == 'FINISHED':
				self.StopProgress()
				return True

		return gui.GeDialog.Message(self, msg, result)

	def AskClose(self):
		if self.importer and not self.importer.is_done:
			answer = gui.MessageDialog(text='Are you sure you want to abort the import ?', type=c4d.GEMB_YESNO)
			if answer == c4d.GEMB_R_YES:
				self.importer.AbortImport()
			else:
				return
		return False
