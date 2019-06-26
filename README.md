# Sketchfab Plugin for C4D (Beta)

**Temporary: See [PATCH.md](PATCH.md) for instructions**

_This is a BETA version so it's important to save your document before using it_
_Works only with C4D R20_

## Version
Sketchfab Plugin version 0.0.85 for Cinema4D

## Installation
Go to the [latest release page](https://github.com/sketchfab/c4d-plugin/releases/latest) to download the plugin and follow the documentation for installation.

## Report an issue

Be sure to check the [release notes](https://github.com/sketchfab/c4d-plugin/releases/latest) for known issues or limitations of the plugin.

You can also report the issue using the [regular channel](https://help.sketchfab.com/hc/en-us/requests/new?type=exporters&subject=Cinema4D+Plugin) or directly from the plugin in **Help -> Report an issue**


## Sources and dependencies

The plugin uses glTF parsing code from [Khronos' glTF-Blender-IO](https://github.com/KhronosGroup/glTF-Blender-IO) (Apache 2.0)

### Dependencies
* **PIL** _is used to resize and crop Sketchfab models thumbnails_
* **Requests** _is used to communicate with Sketchfab API_
