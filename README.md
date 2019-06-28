# Sketchfab Plugin for Cinema4D (Beta)

_This plugin is still in a BETA version, so please make sure to save your documents before using it_

_Only compatible with Cinema4D R.20_

## Installation

Go to the [latest release page](https://github.com/sketchfab/c4d-plugin/releases/latest) to download the plugin and follow the installation instructions.

## Development

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

The final releases can then be built by executing build.sh without arguments:
```
./build.sh
```

## Report an issue

Be sure to check the [release notes](https://github.com/sketchfab/c4d-plugin/releases/latest) for known issues or limitations of the plugin.

You can also report the issue using the [regular channel](https://help.sketchfab.com/hc/en-us/requests/new?type=exporters&subject=Cinema4D+Plugin) or directly from the plugin in **Help -> Report an issue**


## Sources and dependencies

The plugin uses glTF parsing code from [Khronos' glTF-Blender-IO](https://github.com/KhronosGroup/glTF-Blender-IO) (Apache 2.0)

### Dependencies
* **PIL** _is used to resize and crop Sketchfab models thumbnails_
* **Requests** _is used to communicate with Sketchfab API_
