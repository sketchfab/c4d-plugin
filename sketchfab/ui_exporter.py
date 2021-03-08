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

__exporter_id__    = 1029390
__exporter_title__ = "Sketchfab Exporter"

import webbrowser
import os
import datetime
import requests
import json
import tempfile
import shutil

# C4D modules
import c4d
from c4d import gui

# Plugins modules
from api    import SketchfabApi
from config import Config
from utils  import Utils

import ui_login


TXT_MODEL_NAME = 100003
EDITXT_MODEL_TITLE = 100004
TXT_DESCRIPTION = 100005
EDITXT_DESCRIPTION = 100006
TXT_TAGS = 100007
EDITXT_TAGS = 100008
BTN_PUBLISH = 100011
CHK_PRIVATE = 100014
BTN_THUMB_SRC_PATH = 100015
EDITXT_THUMB_SRC_PATH = 100015
EDITXT_PASSWORD = 100016
CHK_ANIMATION = 100017
CHK_PUBLISHDRAFT = 100018
CBOX_PROJECT = 100019
CBOX_PROJECT_ELT = 100020
TXT_PASSWORD = 100021
TXT_PROJECT = 100022

GROUP_WRAPPER = 20000
GROUP_ONE = 20001
GROUP_TWO = 20002
GROUP_THREE = 20003
GROUP_FOUR = 20004
GROUP_FIVE = 20005
GROUP_SIX = 20006
GROUP_PROJECT = 20007

# Constants
FBX20142 = 1026370

export_options = {
	c4d.FBXEXPORT_LIGHTS: 0,
	c4d.FBXEXPORT_CAMERAS: 0,
	c4d.FBXEXPORT_SPLINES: 1,
	# Geometry and Materials
	c4d.FBXEXPORT_SAVE_NORMALS: 1,
	c4d.FBXEXPORT_EMBED_TEXTURES: 1,
	c4d.FBXEXPORT_FBX_VERSION: c4d.FBX_EXPORTVERSION_NATIVE,
	# cancel all these one
	c4d.FBXEXPORT_PLA_TO_VERTEXCACHE: 0,
	c4d.FBXEXPORT_SAVE_VERTEX_MAPS_AS_COLORS: 0,
	c4d.FBXEXPORT_TRIANGULATE: 0,
	c4d.FBXEXPORT_SDS_SUBDIVISION: 1,
	c4d.FBXEXPORT_ASCII: 0
}

# Take API changes from R22 into account
# https://developers.maxon.net/docs/Cinema4DPythonSDK/html/misc/changelog/changelog_s22.html
if c4d.GetC4DVersion() >= 22000:
	export_options[c4d.FBXEXPORT_BAKE_MATERIALS] = 0
	export_options[c4d.FBXEXPORT_MATERIALS] = c4d.FBXEXPORT_MATERIALS_PHONGLAMBERT
else:
	# In S22+, this becomes enforced by FBXEXPORT_EMBED_TEXTURES
	export_options[c4d.FBXEXPORT_TEXTURES] = 1

# Globals
g_uploaded = False
g_error = ""
g_upload_message = ""
model_id = ""


class PublishModelThread(c4d.threading.C4DThread):
	"""Class that publishes 3D model to Sketchfab.com."""

	def __init__(self, api, data, title, activeDoc, activeDocPath, enable_animation):
		c4d.threading.C4DThread.__init__(self)
		self.skfb_api = api
		self.data = data
		self.title = title
		self.activeDoc = activeDoc
		self.activeDocPath = activeDocPath
		self.enable_animation = enable_animation

	def Main(self):
		global g_uploaded
		global g_error
		global model_id

		# Create a temporary directory to export everything in
		exportDirectory = tempfile.mkdtemp()
		zipName         = os.path.join(self.activeDocPath, self.title)
		
		# Save the current FBX export options
		options = self.get_fbxexport_options()
		export_options[c4d.FBXEXPORT_TRACKS] = self.enable_animation
		export_options[c4d.FBXEXPORT_BAKE_ALL_FRAMES] = self.enable_animation
		backup_options = {}
		for key in export_options:
			if options[key] != export_options[key]:
				backup_options[key] = options[key]
			options[key] = export_options[key]

		# Export the FBX file
		exportFBX = os.path.join(exportDirectory, self.title + '.fbx')
		c4d.documents.SaveDocument(self.activeDoc, exportFBX,
							   c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST, FBX20142)
		if not os.path.exists(exportFBX):
			g_uploaded = False
			g_error = "FBX export failed."
			c4d.SpecialEventAdd(__exporter_id__)
			return False
		print("FBX export successful.")

		# Restore the old FBX export options
		for key in backup_options:
			options[key] = backup_options[key]

		# Zip the temporary directory content
		shutil.make_archive(zipName, 'zip', exportDirectory)

		# If using an org, modify the url and data with the selected project
		url = Config.SKETCHFAB_MODEL
		if self.skfb_api.use_org_profile:
			url = "{}/{}/models".format(Config.SKETCHFAB_ORGS, self.skfb_api.active_org["uid"])

		# Do the request
		_headers = self.skfb_api.headers
		try:
			r = requests.post(
				url,
				data    = self.data,
				files   = {"modelFile": open(zipName + ".zip", 'rb')},
				headers = _headers
			)
		except requests.exceptions.RequestException as e:
			g_uploaded = False
			g_error = e
			return 

		result = r.json()

		if r.status_code != requests.codes.created:
			g_error = "Invalid response from server: %d." % r.status_code
			# Was the file too big ?
			if "size" in r.text:
				print("request:")
				print(r.text)
		else:
			# We'll open the messagebox in CoreMessage
			g_uploaded = True
			model_id = result["uid"]

		# Clean up
		self.cleanup_files([zipName + ".zip", exportDirectory])
		c4d.SpecialEventAdd(__exporter_id__)
			
		return

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

	def cleanup_files(self, files):
		for f in files:
			if os.path.exists(f):
				try:
					if os.path.isdir(f):
						shutil.rmtree(f)
					else:
						os.remove(f)
				except Exception:
					print("Unable to remove file {0}".format(f))
		

class MainDialog(ui_login.SketchfabDialogWithLogin):
	"""Main Dialog Class"""

	def InitValues(self):
		super(MainDialog, self).InitValues()
		self.userarea_paths_header.set_img(os.path.join(Config.PLUGIN_DIRECTORY, 'res', 'Sketchfab_Logo_exporter.png'))
		return True

	def refresh(self):
		self.draw_login_ui()
		self.draw_upload_button()

	def draw_model_properties(self):
		docname = c4d.documents.GetActiveDocument().GetDocumentName()

		self.AddStaticText(id=TXT_PROJECT, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Export to project:")
		self.AddComboBox(id=CBOX_PROJECT, flags=c4d.BFH_RIGHT | c4d.BFH_SCALEFIT, initw=0, inith=0)
		if self.skfb_api.use_org_profile:
			for index, project in enumerate(self.skfb_api.active_org["projects"]):
				self.AddChild(id=CBOX_PROJECT, subid=CBOX_PROJECT_ELT + index, child=project["name"])
		self.SetInt32(CBOX_PROJECT, CBOX_PROJECT_ELT)
		self.Enable(TXT_PROJECT, False)
		self.Enable(CBOX_PROJECT, False)

		self.AddStaticText(id=TXT_MODEL_NAME, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Model name:")
		self.AddEditText(id=EDITXT_MODEL_TITLE, flags=c4d.BFH_SCALEFIT, initw=0, inith=0)
		self.SetString(EDITXT_MODEL_TITLE, docname)

		self.AddStaticText(id=TXT_DESCRIPTION, flags=c4d.BFH_LEFT | c4d.BFV_TOP,
						   initw=0, inith=0, name="Description:")
		self.AddMultiLineEditText(id=EDITXT_DESCRIPTION, flags=c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
								  initw=0, inith=100, style=c4d.DR_MULTILINE_WORDWRAP)

		self.AddStaticText(id=TXT_TAGS, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Tags: cinema4d ")
		self.AddEditText(id=EDITXT_TAGS, flags= c4d.BFH_RIGHT | c4d.BFH_SCALEFIT, initw=0, inith=0)

		self.AddCheckbox(id=CHK_ANIMATION, flags=c4d.BFH_LEFT,
						 initw=0, inith=0, name="Enable animation")

	def draw_private_options(self):
		self.LayoutFlushGroup(GROUP_FIVE)
		self.AddCheckbox(id=CHK_PUBLISHDRAFT, flags=c4d.BFH_LEFT,
						 initw=0, inith=0, name="Publish as a draft (not visible to public immediately)")
		self.AddCheckbox(id=CHK_PRIVATE, flags=c4d.BFH_SCALEFIT | c4d.BFH_LEFT,
						 initw=0, inith=0, name="Private Model (Pro User Only)")
		self.AddStaticText(id=TXT_PASSWORD, flags=c4d.BFH_LEFT,
						   initw=0, inith=0, name="Password (optional):    ")
		self.AddEditText(id=EDITXT_PASSWORD, flags=c4d.BFH_LEFT,
						 initw=200, inith=0, editflags=c4d.EDITTEXT_PASSWORD)
		self.Enable(TXT_PASSWORD, False)
		self.Enable(EDITXT_PASSWORD, False)
		self.LayoutChanged(GROUP_FIVE)

	def draw_upload_button(self):
		self.LayoutFlushGroup(GROUP_SIX)
		self.AddStaticText(id=0, flags=c4d.BFH_LEFT | c4d.BFH_SCALEFIT, initw=0, inith=0, name=g_upload_message)
		self.AddButton(id=BTN_PUBLISH, flags=c4d.BFH_CENTER | c4d.BFV_CENTER, initw=200, inith=38, name="Upload")
		self.Enable(BTN_PUBLISH, self.skfb_api.is_user_logged())
		self.LayoutChanged(GROUP_SIX)

	def Timer(self, msg):
		if self.redraw_login:
			self.draw_login_ui()
			self.redraw_login = False
		
		if self.org_changed:
			if self.skfb_api.use_org_profile:
				self.Enable(GROUP_PROJECT, True)
				self.Enable(TXT_PROJECT, True)
				self.Enable(CBOX_PROJECT, True)
				self.FreeChildren(CBOX_PROJECT)
				for index, project in enumerate(self.skfb_api.active_org["projects"]):
					self.AddChild(id=CBOX_PROJECT, subid=CBOX_PROJECT_ELT + index, child=project["name"])
				self.SetInt32(CBOX_PROJECT, CBOX_PROJECT_ELT)
				
			else:
				self.Enable(GROUP_PROJECT, False)
				self.Enable(TXT_PROJECT, False)
				self.Enable(CBOX_PROJECT, False)

			self.org_changed = False

	def CreateLayout(self):
		
		# Title
		self.SetTitle(__exporter_title__)

		# Header and inheritance
		super(MainDialog, self).CreateLayout()

		self.skfb_api.login_callback = self.refresh

		# Model properties
		self.GroupBegin(id=GROUP_TWO,
						flags=c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT,
						cols=2,
						rows=1)
		self.GroupSpace(40, 10)
		self.GroupBorderSpace(6, 6, 6, 6)
		self.draw_model_properties()
		self.GroupEnd()

		self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)

		# Private options
		self.GroupBegin(id=GROUP_FIVE,
						flags=c4d.BFH_SCALEFIT | c4d.BFV_BOTTOM,
						cols=1,
						rows=1)
		self.GroupSpace(4, 4)
		self.GroupBorderSpace(6, 6, 6, 2)
		self.draw_private_options()
		self.GroupEnd()

		# Upload button
		self.GroupBegin(id=GROUP_SIX,
						flags=c4d.BFH_SCALEFIT | c4d.BFV_CENTER | c4d.BFH_CENTER,
						cols=1,
						rows=1)
		self.GroupSpace(4, 4)
		self.GroupBorderSpace(6, 2, 6, 6)
		self.draw_upload_button()
		self.GroupEnd()

		self.draw_footer()

		return True

	def CoreMessage(self, id, msg):
		"""Override this function if you want to react
		to C4D core messages. The original message is stored in msg.
		"""
		if id == __exporter_id__:
			c4d.StatusSetBar(100)

			if g_uploaded:
				result = gui.MessageDialog("Your model was uploaded to Sketchfab.com.\nClick OK to open it in your browser.", c4d.GEMB_OKCANCEL)
				if result == c4d.GEMB_R_OK:
					webbrowser.open(Config.SKETCHFAB_URL + '/models/' + model_id)
			else:
				print("Unable to upload model to Sketchfab.com. Reason: {0}".format(g_error))
				gui.MessageDialog("Unable to upload model to Sketchfab.com. Reason: {0}".format(g_error), c4d.GEMB_OK)

			self.draw_upload_button()
			self.Enable(BTN_PUBLISH, True)
			self.SetTitle("Upload status")
			c4d.StatusClear()

		return True

	def Command(self, id, msg):

		self.common_commands(id, msg)

		if id == BTN_THUMB_SRC_PATH:
			selected = c4d.storage.LoadDialog(type=c4d.FILESELECTTYPE_ANYTHING)
			if not selected:
				return False
			else:
				self.SetString(EDITXT_THUMB_SRC_PATH, selected)

		if id == CHK_PRIVATE:
			if self.GetBool(CHK_PRIVATE):
				self.Enable(EDITXT_PASSWORD, True)
				self.Enable(TXT_PASSWORD, True)
			else:
				self.draw_private_options()
				self.Enable(EDITXT_PASSWORD, False)
				self.Enable(TXT_PASSWORD, False)

		if id == BTN_PUBLISH:
			c4d.StatusSetBar(50)
			g_upload_message = "Uploading..."
			self.draw_upload_button()

			activeDoc = c4d.documents.GetActiveDocument()
			activeDocPath = activeDoc.GetDocumentPath()
			if not os.path.exists(activeDocPath):
				path = c4d.storage.SaveDialog(type=c4d.FILESELECTTYPE_ANYTHING, title="Please save your .c4d scene", force_suffix="c4d")
				result = c4d.documents.SaveDocument(activeDoc, path, c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST, c4d.FORMAT_C4DEXPORT)
				c4d.documents.LoadFile(path)
				if not result:
					gui.MessageDialog("Please save your .c4d scene first.", c4d.GEMB_OK)
					c4d.StatusClear()
					return False

			# Set document data with newly saved document
			activeDoc = c4d.documents.GetActiveDocument()
			activeDocPath = activeDoc.GetDocumentPath()

			self.Enable(BTN_PUBLISH, False)
			self.SetTitle("{0} uploading model...".format(__exporter_title__))

			title = self.GetString(EDITXT_MODEL_TITLE)
			description = self.GetString(EDITXT_DESCRIPTION)
			tags = self.GetString(EDITXT_TAGS)
			private = self.GetBool(CHK_PRIVATE)
			password = self.GetString(EDITXT_PASSWORD)
			enable_animation = self.GetBool(CHK_ANIMATION)
			auto_publish = not(self.GetBool(CHK_PUBLISHDRAFT))

			# Error messages
			if len(title) == 0 or len(title) > 48 or len(description) > 1024:
				error_message = ""
				if len(title) == 0:
					error_message = "Please enter a title for your model"
				if len(title) > 48:
					error_message = "The model title must be less than 48 characters long"
				if len(description) > 1024:
					error_message = "The description must be less than 1024 characters long"
				gui.MessageDialog(error_message, c4d.GEMB_OK)
				self.Enable(BTN_PUBLISH, True)
				self.SetTitle(__exporter_title__)
				c4d.StatusClear()
				return False

			# populate data
			data = {
				"source": "cinema4d",
				"tags": "cinema4d ",
				"title": title
			}
			data['isPublished'] = auto_publish
			if len(description) != 0:
				data['description'] = description
			if len(tags) != 0:
				data['tags'] += " ".join(tags.split(" ")[:41]).strip()
			if private:
				data['private'] = private
			if private and len(password) != 0:
				data['password'] = password
			if self.skfb_api.use_org_profile:
				project_index = self.GetInt32(CBOX_PROJECT) - CBOX_PROJECT_ELT
				data["orgProject"] = self.skfb_api.active_org["projects"][project_index]["uid"]

			# Start Multithread operations		
			self.publish = PublishModelThread(self.skfb_api, data, title, activeDoc, activeDocPath, enable_animation)
			self.publish.Start()
			self.publish.Wait(True)

		return True