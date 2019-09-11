#!/bin/bash
# Creates dev and release (.zip) versions of the Cinema4D plugin
#
# Usage:
#   git clone -b chore/gltf-dependency-uniformization_D3D-4952 --recursive git@github.com:sketchfab/c4d-plugin.git
#   cd c4d-plugin/
#   ./build.sh --patch    (AFTER CLONING ONLY!!!)
#   or
#   ./build.sh            (FOR SUBSEQUENT RELEASES)
#
# Make a symlink in Cinema4D from Powershell:
# cmd /c mklink /d 'C:\Program Files\MAXON\Cinema 4D R20\plugins\c4d-plugin/' C:\Users\Norgeotloic\Documents\TOTOTO\releases\c4d-plugin-win\

# Get the plugin version
version=$(cat sketchfab/config.py | grep 'PLUGIN_VERSION = ' | grep -o '".*"' | tr -d '"')

# If requested, apply the patch on Khronos' submodule (glTF-Blender-IO/)
if [[ $* == *--patch* ]]
then
  echo "Applying the patch on Khronos code"
  cd glTF-Blender-IO/
  git apply ../khronos-gltf.patch
  cp -r ./addons/io_scene_gltf2/io/ ../gltfio/
  cd ../
else
  echo "Creating releases for version $version"
  # Create the ZIP files for release
  mkdir -p releases
  rm -rf releases/*
  # OSX
  mkdir releases/sketchfab-osx-$version/
  cp -r SketchfabPlugin.pyp res sketchfab gltfio releases/sketchfab-osx-$version/
  cp -r dependencies/OSX/ releases/sketchfab-osx-$version/dependencies
  # WINDOWS
  mkdir releases/sketchfab-win-$version/
  cp -r SketchfabPlugin.pyp res sketchfab gltfio releases/sketchfab-win-$version/
  cp -r dependencies/WIN/ releases/sketchfab-win-$version/dependencies
  # Zip everything
  cd releases/
  zip -r -q sketchfab-osx-$version.zip sketchfab-osx-$version/
  zip -r -q sketchfab-win-$version.zip sketchfab-win-$version/
  cd ..
  echo "Releases available in $(pwd)/releases/"
fi
