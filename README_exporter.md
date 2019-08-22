Cinema4D Sketchfab Exporter
===========================

Welcome!
--------

Thank you for trying out Sketchfab Exporter! Sketchfab Exporter is a plugin for Cinema 4D that automatically exports and uploads your 3d models to the Sketchfab.com website.

System Requirements
-------------------

- Apple Mac OS X v10.6 or later
- Windows 7 or later
- MAXON® Cinema 4D® R13 or later

Installation
------------

You have two options. You can place the exporter folder in the application’s plugin directory. This the recommended installation path. However, make sure you have the proper permissions for the Applications directory.

Windows: C:\Program Files\MAXON\CINEMA 4D R1X\plugins
OS X: /Applications/MAXON/CINEMA 4D R1X/plugins

You can also place it in the user preferences plugin directory. e.g.:

/Users/UserName/Library/Preferences/MAXON/CINEMA 4D R1X_XXXXXXXX/plugins

Just drag the whole Sketchfab Exporter folder into either one of the above folders and you are good to go!

Special Note:

The Sketchfab plugin for Cinema 4D uses the third party Poster module to do some of its magic. The plugin installs the module behind the scenes without user intervention. However, it is possible that things may not go as planned. If when starting the Sketchfab plugin, it complains about not being able to install the necessary files, you will need to install this module manually.

1. Look inside the Sketchfab plugin folder and find a zip file called “poster-0.8.1.zip”. i.e /Sketchfab-C4D-Exporter/res/poster-0.8.1.zip

2. Unpack the contents of the poster zip file to your python modules folder located in your user preferences folder for Cinema 4D.
    OS X:  /Users/UserName/Library/Preferences/MAXON/CINEMA 4D R1X/library/python/packages/osx
    Windows:  /Users/UserName/Library/Preferences/MAXON/CINEMA 4D R1X/library/python/packages/win64

3. Restart Cinema 4D


How do I use the Cinema 4D Sketchfab Exporter?
----------------------------------------------

Sketchfab Exporter will be available in your Plugins menu in Cinema 4D.

Once you have your scene file ready, open Sketchfab Exporter and enter a name, description, tags separated by spaces, and enter your API token ( https://sketchfab.com/settings/password ). Enable animation if your model is animated. You can also choose to publish the model immediately or upload in Draft mode. PRO Sketchfab users can also make the upload private (unlisted) and optionally password-protected. If you wish to save the API token for future uploads, go to options menu and select the Save API Token option.

You also have the option to make your uploaded model private. This option, however, requires you have a premium Sketchfab.com account. If you would like to give access to your private model to certain people, you can enter a password in the text field provided.

All you have to do now is hit Publish and Sketchfab Exporter will export and upload your model in the background. Once Sketchfab Exporter is done, it will pop up a dialog indicating if the model was successfully published. From there you can open the model page in your browser.

Version History
---------------

Sketchfab Exporter 1.3.0

- Uses FBX instead of Collada
- Animation support
- Draft mode support

Sketchfab Exporter 1.2.2

- Updated to work with new Sketchfab infrastructure

Sketchfab Exporter 1.2.1

- Added check for OS type and Cinema 4D version

Sketchfab Exporter 1.2

- Ability to enter a password for private models. (PRO User Only)
– Now works on Windows platform under Cinema 4D R15

Sketchfab Exporter 1.1

- Ability to make uploaded model private. (PRO User Only)

Sketchfab Exporter 1.0

- First "official" release!

Contact, Suggestions, Bugs, Spam
--------------------------------

E-Mail: support@sketchfab.com
Web: http://sketchfab.com/
Twitter: @sketchfab

Legal
-----

THIS PROGRAM IS FREE SOFTWARE: YOU CAN REDISTRIBUTE IT AND/OR MODIFY
IT UNDER THE TERMS OF THE GNU GENERAL PUBLIC LICENSE AS PUBLISHED BY
THE FREE SOFTWARE FOUNDATION, EITHER VERSION 3 OF THE LICENSE, OR
(AT YOUR OPTION) ANY LATER VERSION.

THIS PROGRAM IS DISTRIBUTED IN THE HOPE THAT IT WILL BE USEFUL,
BUT WITHOUT ANY WARRANTY; WITHOUT EVEN THE IMPLIED WARRANTY OF
MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.  SEE THE
GNU GENERAL PUBLIC LICENSE FOR MORE DETAILS.

YOU SHOULD HAVE RECEIVED A COPY OF THE GNU GENERAL PUBLIC LICENSE ALONG
WITH THIS PROGRAM.  IF NOT, SEE <HTTP://WWW.GNU.ORG/LICENSES/>.
