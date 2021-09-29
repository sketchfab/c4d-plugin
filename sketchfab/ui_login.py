"""
une classe commune aux deux plugins
qui contient le login et fait les checks de connexion / identification
"""

import os
import webbrowser

import c4d

from config import Config
from cache  import Cache
from utils  import Utils
from api    import SketchfabApi


UA_HEADER = 1000

GROUP_HEADER = 2000
GROUP_LOGIN = 2001
GROUP_FOOTER = 2011
GROUP_FOOTER_VERSION = 2012
GROUP_FOOTER_CONTACT = 2013
GROUP_WARNING = 2010

BTN_CONNECT_SKETCHFAB = 2108
BTN_LOGIN = 2105
BTN_CREATE_ACCOUNT = 2113
BTN_DOCUMENTATION = 2111
BTN_REPORT = 2112
BTN_OPEN_CACHE = 2114
BTN_UPGRADE_PLUGIN = 2110
BTN_WARNING = 2109

LB_WARNING = 2201
LB_CONNECT_STATUS = 2205
LB_LOGIN_EMAIL = 2206
LB_LOGIN_PASSWORD = 2207
LB_PLUGIN_VERSION = 2208
LB_CONNECT_STATUS_CONNECTED = 2204

EDITXT_LOGIN_EMAIL = 2300
EDITXT_LOGIN_PASSWORD = 2301

TEXT_WIDGET_HEIGHT = 10

class UserAreaPathsHeader(c4d.gui.GeUserArea):
	"""Sketchfab header image."""
	img_path = ""
	bmp      = c4d.bitmaps.BaseBitmap()

	def set_img(self, path):
		self.img_path = path

	def GetMinSize(self):
		self.width = 448
		self.height = 75
		return (self.width, self.height)

	def DrawMsg(self, x1, y1, x2, y2, msg):
		logo, _  = self.bmp.InitWith(self.img_path)
		if logo == c4d.IMAGERESULT_OK:
			self.DrawBitmap(self.bmp, 0, 0, 448, 75,
							0, 0, self.bmp.GetBw(), self.bmp.GetBh(), 
							c4d.BMP_NORMALSCALED | c4d.BMP_ALLOWALPHA)

	def Redraw(self):
		logo, _  = self.bmp.InitWith(self.img_path)
		if logo == c4d.IMAGERESULT_OK:
			self.DrawBitmap(self.bmp, 0, 0, 448, 75,
							0, 0, self.bmp.GetBw(), self.bmp.GetBh(), 
							c4d.BMP_NORMALSCALED | c4d.BMP_ALLOWALPHA)

class SketchfabDialogWithLogin(c4d.gui.GeDialog):

	userarea_paths_header = UserAreaPathsHeader()

	redraw_login   = False
	status_widget  = None
	is_initialized = False
	cta_link       = None
	
	def initialize(self):
		self.is_initialized = True
		self.skfb_api.connect_to_sketchfab()

	def draw_header(self):
		self.LayoutFlushGroup(GROUP_HEADER)

		self.AddUserArea(UA_HEADER, c4d.BFH_CENTER)
		self.AttachUserArea(self.userarea_paths_header, UA_HEADER)
		self.userarea_paths_header.LayoutChanged()

		self.LayoutChanged(GROUP_HEADER)

	def draw_login_ui(self):
		
		self.LayoutFlushGroup(GROUP_LOGIN)

		if not self.is_initialized:
			self.AddButton(id=BTN_CONNECT_SKETCHFAB, flags=c4d.BFH_CENTER | c4d.BFV_BOTTOM, initw=350, inith=TEXT_WIDGET_HEIGHT, name="Connect to Sketchfab")
		else:
			if self.skfb_api.is_user_logged():
				self.AddStaticText(id=LB_CONNECT_STATUS, flags=c4d.BFH_LEFT, initw=0, inith=0, name=u"Connected as {}".format(self.skfb_api.display_name))
				self.AddButton(id=BTN_CONNECT_SKETCHFAB, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Logout")
			else:
				self.AddStaticText(id=LB_LOGIN_EMAIL, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Email:")
				self.AddEditText(id=EDITXT_LOGIN_EMAIL, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=350, inith=TEXT_WIDGET_HEIGHT)
				self.AddStaticText(id=LB_LOGIN_PASSWORD, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Password:")
				self.AddEditText(id=EDITXT_LOGIN_PASSWORD, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=350, inith=TEXT_WIDGET_HEIGHT, editflags=c4d.EDITTEXT_PASSWORD)
				self.AddButton(id=BTN_LOGIN, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Login")

		# Little hack to get username set in UI
		self.SetString(LB_CONNECT_STATUS, u"Connected as {}".format(self.skfb_api.display_name))
		self.LayoutChanged(GROUP_LOGIN)	

	def refresh_version_ui(self):
		self.draw_version_ui()

	def msgbox_message(self, text):
		c4d.gui.MessageDialog(text, type=c4d.GEMB_OK)

	def draw_version_ui(self):
		self.LayoutFlushGroup(GROUP_FOOTER_VERSION)

		version_state = 'connect to check version'
		is_latest_version = True
		if self.skfb_api.latest_release_version:
			if self.skfb_api.latest_release_version != Config.PLUGIN_VERSION:
				version_state = 'outdated'
				is_latest_version = False
			else:
				version_state = 'up to date'

		self.AddStaticText(id=LB_PLUGIN_VERSION, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=0, inith=0, name="Plugin version: {} ({})".format(Config.PLUGIN_VERSION, version_state))
		if not is_latest_version:
			self.AddButton(id=BTN_UPGRADE_PLUGIN, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=75, inith=TEXT_WIDGET_HEIGHT, name='Upgrade')

		self.LayoutChanged(GROUP_FOOTER_VERSION)

	def draw_warning_ui(self, _type):
		"""
		1 - Normal search, no results
		2 - Own models but not pro
		3 - No Store purchases
		"""
		msg, btn = u'No results found', None
		if _type == 2:
			msg = u'Access your personal library of 3D models'
			btn = 'Upgrade to PRO'
			self.cta_link = Config.SKETCHFAB_PLANS
		elif _type == 3:
			msg = u'You did not purchase any model yet'
			btn = 'Visit the Store'
			self.cta_link = Config.SKETCHFAB_STORE

		self.GroupBegin(GROUP_WARNING, c4d.BFH_CENTER | c4d.BFV_CENTER, 6, 4, "Warning")
		self.LayoutFlushGroup(GROUP_WARNING)
		self.GroupBorderSpace(6, 2, 6, 2)
		self.AddStaticText(id=LB_WARNING, flags=c4d.BFH_CENTER | c4d.BFV_CENTER, initw=500, name=msg)
		if btn:
			self.AddButton(id=BTN_WARNING, flags=c4d.BFH_CENTER | c4d.BFV_CENTER, initw=150, inith=TEXT_WIDGET_HEIGHT * 2, name=btn)
		self.LayoutChanged(GROUP_WARNING)
		self.GroupEnd()

	def draw_footer(self):
		self.AddSeparatorH(initw=0, flags=c4d.BFH_FIT)
		self.GroupBegin(GROUP_FOOTER, c4d.BFH_FIT | c4d.BFV_CENTER, 3, 1, "Footer")

		self.LayoutFlushGroup(GROUP_FOOTER)
		self.GroupBorderSpace(6, 2, 6, 6)
		self.AddSeparatorV(0.0, flags=c4d.BFH_SCALE)

		self.GroupBegin(GROUP_FOOTER_VERSION, c4d.BFH_RIGHT | c4d.BFV_CENTER, 5, 1, "Footer_version")
		self.draw_version_ui()
		self.GroupEnd()

		self.LayoutChanged(GROUP_FOOTER)

		self.GroupEnd()

	def draw_contact_ui(self):
		self.AddButton(id=BTN_UPGRADE_PLUGIN, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=120, inith=TEXT_WIDGET_HEIGHT, name='Documentation')
		self.AddButton(id=BTN_REPORT, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=120, inith=TEXT_WIDGET_HEIGHT, name='Report an issue')

	def setup_api(self):
		self.skfb_api = SketchfabApi()
		self.skfb_api.version_callback = self.refresh_version_ui
		self.skfb_api.request_callback = self.draw_login_ui # self.refresh
		self.skfb_api.login_callback   = self.draw_login_ui
		self.skfb_api.msgbox_callback  = self.msgbox_message

	def InitValues(self):
		self.SetTimer(20)
		self.SetString(EDITXT_LOGIN_EMAIL, Cache.get_key('username'))
		return True

	def CreateLayout(self):
		# Initialization
		self.setup_api()
		
		# Menu
		self.MenuFlushAll()
		self.MenuSubBegin("File")
		self.MenuAddCommand(c4d.IDM_CM_CLOSEWINDOW)
		self.MenuSubEnd()
		self.MenuSubBegin("Help")
		self.MenuAddString(BTN_CREATE_ACCOUNT, "Create an account")
		self.MenuAddString(BTN_REPORT, "Report an issue")
		self.MenuAddString(BTN_DOCUMENTATION, "Documentation")
		self.MenuAddString(BTN_OPEN_CACHE, "Open cache directory")
		self.MenuSubEnd()
		self.MenuFinished()

		# Header
		self.GroupBegin(GROUP_HEADER, c4d.BFH_LEFT | c4d.BFV_TOP, 1, 1, "Header")
		self.draw_header()
		self.GroupEnd()
		self.AddSeparatorH(initw=0, flags=c4d.BFH_FIT)

		# Login
		self.GroupBegin(id=GROUP_LOGIN,
						flags=c4d.BFH_CENTER,
						cols=7,
						rows=1,
						title="Login",
						groupflags=c4d.BORDER_NONE | c4d.BFV_GRIDGROUP_EQUALCOLS | c4d.BFV_GRIDGROUP_EQUALROWS)
		self.draw_login_ui()
		self.GroupEnd()

		self.AddSeparatorH(initw=0, flags=c4d.BFH_FIT)

	def AskClose(self):
		self.is_initialized = False
		return False

	def common_commands(self, id, msg):
		if id == BTN_CONNECT_SKETCHFAB:
			if not self.is_initialized:
				self.initialize()
			else:
				self.skfb_api.logout()
				self.SetString(EDITXT_LOGIN_EMAIL, Cache.get_key('username'))
			self.skfb_api.login_callback()

		if id == BTN_LOGIN:
			self.skfb_api.login(self.GetString(EDITXT_LOGIN_EMAIL), self.GetString(EDITXT_LOGIN_PASSWORD))

		#if id == BTN_WEB:
		#	Utilities.ESOpen_website(Config.SKETCHFAB_URL)

		if id == BTN_DOCUMENTATION:
			webbrowser.open(Config.PLUGIN_LATEST_RELEASE)

		if id == BTN_UPGRADE_PLUGIN:
			webbrowser.open(Config.PLUGIN_LATEST_RELEASE)

		if id == BTN_CREATE_ACCOUNT:
			webbrowser.open(Config.SKETCHFAB_SIGNUP)

		if id == BTN_OPEN_CACHE:
			Utils.open_directory('{}'.format(Config.SKETCHFAB_TEMP_DIR))

		if id == BTN_WARNING:
			webbrowser.open(self.cta_link)

		if id == BTN_REPORT:
			webbrowser.open(Config.SKETCHFAB_REPORT_URL)
