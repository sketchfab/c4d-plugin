# Sketchfab Cinema4D Plugin

**Directly import and export models from and to Sketchfab in Cinema4D (R.20 or later)**

* [Installation](#installation)
* [Login](#login)
* [Import from Sketchfab](#import-a-model-from-sketchfab)
* [Export to Sketchfab](#export-a-model-to-sketchfab)
* [Known issues](#known-issues)
* [Report an issue](#report-an-issue)
* [Addon development](#addon-development)

*Based on parsing code from  [Khronos Group](https://github.com/KhronosGroup) - [glTF-Blender-IO](https://github.com/KhronosGroup/glTF-Blender-IO)*

## Installation

First download the **sketchfab-x-y-z.zip** file attached to the [latest release](https://github.com/sketchfab/c4d-plugin/releases/latest) according to your O.S., and extract its content into a directory.

**Note**: Make sure to remove any previous installation of Sketchfab plugins. It is also recommended to rename the directory into "Sketchfab", as this will allow the plugin to be displayed under the name "Sketchfab" instead of "sketchfab-win-1.3.0" for instance.

To install the plugin, you should copy the newly extracted directory into an adequate directory, before restarting Cinema4D (you will find more information about plugin installation on the [dedicated page of Maxon FAQ](https://support.maxon.net/kb/faq.php?id=52)).

#### User Preferences directory

You can find your user preferences directory through the **Open Preferences Folder** in the **Edit -> Preferences** menu. From there, just copy the downloaded directory into the **plugins** folder (you might need to create it if it does not exist).

#### Custom directory

You can also install the plugin in a custom location. To do so, add the path containing the newly extracted directory to the search paths in the **Edit -> Preferences -> Plugins** menu.

Upon restarting Cinema 4D, the Sketchfab plugin should be available under the "Plugins" (R20) or "Extensions" (R21) menu:

![menu](https://user-images.githubusercontent.com/52042414/65263442-f9e2ed80-db0c-11e9-96ba-76e7edab1c1d.png)

## Login

The login process (mandatory to import or export models) should be straightforward: type in the email adress associated with your Sketchfab account as well as your password in the login form:

![login](https://user-images.githubusercontent.com/52042414/65263673-652cbf80-db0d-11e9-8204-ceca46b6813e.png)

Your Sketchfab username should then be displayed upon successful login, and you will gain access to the full import and export capabilities of the addon. 

Please note that your login credentials are stored in a temporary file on your local machine (to avoid repeating the login process multiple times). 
You can clear it by simply logging out of your Sketchfab account through the **Log Out** button.


## Import a model from Sketchfab

*Please note that all downloadable models are licensed under specific licenses: make sure to follow the different [Creative Commons licensing schemes](https://help.sketchfab.com/hc/en-us/articles/201368589-Downloading-Models#licenses).*

Once logged in into the **Sketchfab Importer**, you should be able to easily import any downloadable model from Sketchfab. 

To do so, just run a search query and adapt the search filters:

![Screenshot-1](https://user-images.githubusercontent.com/4066133/60028977-90d01300-96a0-11e9-8892-d228a7943d0d.JPG)


Note that **PRO** users can use the **My Models** checkbox to import any published model from their own library (even the private ones).

You can navigate through the models available for download with the **Previous** and **Next** buttons, and inspect a model before importing it by selecting an icon:

![Screenshot-2](https://user-images.githubusercontent.com/4066133/60028983-93cb0380-96a0-11e9-8f98-b9f257bdb079.JPG)

Selecting the "Import Model" button will download the current asset and import it into your C4D scene

![Screenshot-3](https://user-images.githubusercontent.com/4066133/60028986-96c5f400-96a0-11e9-887f-395c957cf150.JPG)

Please note that as Sketchfab models come from many different sources, the imported model might not be scaled correctly upon import: try rescaling it after having it selected in the hierarchy if you can see the object upon import !

## Export a model to Sketchfab

Exporting should also be straightforward:

Once you have your scene file ready, open the **Exporter** and enter a title, description, and tags (separated by spaces) for your model. You can then choose to publish the model later with the "Draft" checkbox, and PRO users can also set their model as private, and optionally protect them with a password ([here](https://sketchfab.com/plans) are more information about the different plans available on Sketchfab).

![exporter](https://user-images.githubusercontent.com/52042414/65264692-74ad0800-db0f-11e9-8ae8-1c300764b5cb.png)

Hitting the **Upload** button will process your model, and a pop-up should appear upon success, with a link to the model on your Sketchfab profile.

Please note that although the uploading process can be quite fast (as it entirely depends upon your internet connection), the model will still need to process, and you will be available to monitor their status on the "Upload" tab of your profile:

![Uploads](https://user-images.githubusercontent.com/52042414/65265316-edf92a80-db10-11e9-8d1d-0c3235cea640.png)

## Known Issues

If none of the following description matches your problem, please feel free to [report an issue](#report-an-issue).

#### Model has material using several UV layers

Mutli-UV models are not *yet* supported by this plugin, so models having these properties can look messed up.

#### Sketchfab <-> Cinema4D material conversion

Cinema4D and Sketchfab (glTF) are both using PBR materials but using two different models (different channels and material properties), which may lead to different material settings between Sketchfab and Cinema 4D.

In particular, **metalness and roughness maps are not exported yet**.

If you notice important differences, [reporting the issue](#report-an-issue) can help us investigate, and maybe find a way to solve the problem!

#### Vertex colors

Some models are using vertex colors, and this data is imported but not used by default. The reason is that vertex colors are exported for editing purpose but they are not always used for final render.
In order to make Cinema4D use this data for a model, you need to edit its material(s) and enable both the _COLOR_ channel and the _Vertex Color_ layer in Reflectance channel.
After this, vertex colors should be used for render.

## Report an issue

If you feel like you've encountered a bug not listed in the [known issues](#known-issues), or that the plugin lacks an important feature, you can contact us through [Sketchfab's Help Center](https://help.sketchfab.com/hc/en-us/requests/new?type=exporters&subject=Cinema4D+Plugin) (or directly from the plugin through the **Help -> Report an issue** menu).

To help us track a possible error, please try to append the logs of Cinema4D Python console in your message (available in the **Script -> Console** menu for R20, or **Extensions -> Console** menu for R21).


## Addon development

To prepare a development version of the plugin, you'll first have to clone this repository and update the [Khronos glTF IO](https://github.com/KhronosGroup/glTF-Blender-IO) submodule:
```sh
git clone https://github.com/sketchfab/c4d-plugin.git
cd c4d-plugin/
git submodule update --init --recursive
```

You'll then need (only once) to patch the code from the Khronos submodule with the command:
```sh
./build.sh --patch
```

or (on Windows) 

```sh
bash.exe build.sh --patch
```

The final releases can then be built by executing build.sh without arguments:
```
./build.sh
```