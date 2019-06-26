## gltf IO patch (100% WIP)

To simplify the management of Sketchfab's plugins which depend on the [Khronos glTF IO library](https://github.com/KhronosGroup/glTF-Blender-IO) ([blender](https://github.com/sketchfab/blender-plugin) and [c4d](https://github.com/sketchfab/c4d-plugin)), submodules and patches are to be used for development.

#### Development

Here is the procedure to follow to set up the repository on your local machine:

```sh
# Initialize the repository
git clone https://github.com/sketchfab/c4d-plugin.git
cd c4d-plugin/
git checkout chore/gltf-dependency-uniformization_D3D-4952
git submodule update --init --recursive

# Apply the patch in Khronos' submodule
cd glTF-Blender-IO/
git apply ../khronos-gltf.patch
# Move the necessary files
cp -r ./addons/io_scene_gltf2/io/ ../gltfio/
# Delete the now useless repository
cd ../
rm -rf ./glTF-Blender-IO/
```
