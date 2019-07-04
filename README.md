# Sketchfab Plugin for C4D (Beta)

_This is a BETA version so it's important to save your document before using it_
_Works only with C4D R20_

## Version
Sketchfab Plugin version 0.0.85 for Cinema4D

## Installation
Go to the [latest release page](https://github.com/sketchfab/c4d-plugin/releases/latest) to download the plugin and follow the documentation for installation.

To prepare a development version of the plugin, clone the repo and run [build.sh](build.sh) with the **--patch** flag to patch the Khronos gltf code:

```sh
git clone -b chore/gltf-dependency-uniformization_D3D-4952 --recursive git@github.com:sketchfab/c4d-plugin.git
cd c4d-plugin
./build.sh --patch
```

For the next releases, just run ```./build.sh``` in the repository directory.

## Report an issue

Be sure to check the [release notes](https://github.com/sketchfab/c4d-plugin/releases/latest) for known issues or limitations of the plugin.

You can also report the issue using the [regular channel](https://help.sketchfab.com/hc/en-us/requests/new?type=exporters&subject=Cinema4D+Plugin) or directly from the plugin in **Help -> Report an issue**


## Sources and dependencies

The plugin uses glTF parsing code from [Khronos' glTF-Blender-IO](https://github.com/KhronosGroup/glTF-Blender-IO) (Apache 2.0)

### Dependencies
* **PIL** _is used to resize and crop Sketchfab models thumbnails_
* **Requests** _is used to communicate with Sketchfab API_
