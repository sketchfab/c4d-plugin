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

import os
import math
import sys
import c4d
import shutil

from c4d import plugins, gui

from gltfio.imp.gltf2_io_gltf import glTFImporter
from gltfio.imp.gltf2_io_binary import BinaryData
from utils import Utils


class TextureWrapper:
    def __init__(self, filepath, sampler):
        self.filepath = filepath
        self.sampler = sampler

    def to_c4d_shader(self, alpha_only=False):
        sha = c4d.BaseList2D(c4d.Xbitmap)
        sha[c4d.BITMAPSHADER_FILENAME] = self.filepath

        if alpha_only:
            ls = c4d.LayerSet()
            ls.SetMode(c4d.LAYERSETMODE_LAYERALPHA)
            sha[c4d.BITMAPSHADER_LAYERSET] = ls

        # Barely support texture filtering
        if self.sampler.min_filter in (9728, 9984) or self.sampler.mag_filter in (9728, 9984):
            sha[c4d.BITMAPSHADER_INTERPOLATION] = c4d.BITMAPSHADER_INTERPOLATION_NONE

        return sha


class ImportGLTF(plugins.ObjectData):
    COLOR_BLACK = c4d.Vector(0.0, 0.0, 0.0)
    COLOR_WHITE = c4d.Vector(1.0, 1.0, 1.0)

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.model_dir = ''
        self.gltf_textures = []
        self.gltf_materials = []
        self.is_done = False
        self.has_vertex_colors = False

    def run(self, filepath, uid=None):
        self.model_dir = os.path.split(filepath)[0]
        self.is_done = False

        gltf = glTFImporter(filepath)
        success, txt = gltf.read()

        # Images
        self.import_gltf_textures(gltf)

        # Materials
        imported_materials = self.import_gltf_materials(gltf)
        for index in imported_materials:
            c4d.documents.GetActiveDocument().InsertMaterial(imported_materials[index])
            # c4d.documents.GetActiveDocument().AddUndo(c4d.UNDOTYPE_NEW, imported_materials[index])

        # Nodes
        nodes = {}
        for nodeidx in range(len(gltf.data.nodes)):
            nodes[nodeidx] = self.convert_node(gltf, nodeidx, imported_materials)
            self.progress_callback("Importing nodes", nodeidx + 1, len(gltf.data.nodes))

        # Add objects to document and do parenting
        for node in nodes.keys():
            if gltf.data.nodes[int(node)].children:
                for child in gltf.data.nodes[int(node)].children:
                    c4d.documents.GetActiveDocument().InsertObject(nodes[child], parent=nodes[node])
                    # c4d.documents.GetActiveDocument().AddUndo(c4d.UNDOTYPE_NEW, nodes[child])

        # Add root objects to document
        for node in gltf.data.scenes[0].nodes:
            c4d.documents.GetActiveDocument().InsertObject(nodes[node])
            # c4d.documents.GetActiveDocument().AddUndo(c4d.UNDOTYPE_NEW, nodes[node])

        c4d.documents.GetActiveDocument().SetChanged()
        c4d.DrawViews()
        # c4d.documents.GetActiveDocument().EndUndo()
        self.is_done = True

        gltf_meta = gltf.data.asset
        if gltf_meta.extras:
            title = gltf_meta.extras.get('title', 'Imported')
            author = gltf_meta.extras.get('author')
            license = gltf_meta.extras.get('license')
            note = ''

            # Rename root node with model title
            roots = gltf.data.scenes[0].nodes
            if len(roots) == 1:
                nodes[roots[0]].SetName(title)

            if gltf.data.animations is not None and len(gltf.data.animations):
                note = note + ' - Animation: model has animation but they are not yet supported yet (you may encounter some issues)\n'

            if self.has_vertex_colors:
                note = note + "  - Vertex colors: some vertex colors have been imported but disabled to avoid unexpected results"
                note = note + "\nYou can enable them manually in their material Color and Reflection layer named 'Vertex Colors'"

            if note:
                note = '\n\nWarnings: \n' + note

            message = 'Successfuly imported model'
            if author and license:
                message = message + ' by {} under license {}'.format(Utils.remove_url(author), Utils.remove_url(license))

            message = message + note

            gui.MessageDialog(text=message, type=c4d.GEMB_OK)

        self.progress_callback('Done', 1, 1)

    def list_to_vec3(self, li):
        return c4d.Vector(li[0], li[1], li[2])

    def convert_primitive(self, prim, gltf, materials):
        # Helper functions
        def float2bytes(f):
            int_value = int(math.fabs(f * 32000.0))
            high_byte = int(int_value / 256)
            low_byte = int_value - 256 * high_byte

            if f < 0:
                high_byte = 255 - high_byte
                low_byte = 255 - low_byte

            return (low_byte, high_byte)

        # Normals tag. (Contains 12 WORDs per polygon, enumerated like the following: ax,ay,az,bx,by,bz,cx,cy,cz,dx,dy,dz.
        # The value is the Real value of the normal vector component multiplied by 32000.0.)
        def set_normals(normal_tag, polygon, normal_a, normal_b, normal_c, normal_d):
            normal_list = [normal_a, normal_b, normal_c, normal_d]
            normal_buffer = normal_tag.GetLowlevelDataAddressW()
            vector_size = 6
            component_size = 2

            for v in range(4):
                normal = normal_list[v]
                component = [normal.x, normal.y, normal.z]

                for c in range(3):
                    low_byte, high_byte = float2bytes(component[c])

                    normal_buffer[normal_tag.GetDataSize() * polygon + v * vector_size + c * component_size + 0] = chr(low_byte)
                    normal_buffer[normal_tag.GetDataSize() * polygon + v * vector_size + c * component_size + 1] = chr(high_byte)

        def parse_normals():
            normal = []
            if 'NORMAL' in prim.attributes:
                normal = BinaryData.get_data_from_accessor(gltf, prim.attributes['NORMAL'])

            if normal:
                normaltag = c4d.NormalTag(nb_poly)
                for polyidx in range(nb_poly):
                    poly = c4d_mesh.GetPolygon(polyidx)
                    normal_a = self.switch_handedness_v3(self.list_to_vec3(normal[poly.a]))
                    normal_b = self.switch_handedness_v3(self.list_to_vec3(normal[poly.b]))
                    normal_c = self.switch_handedness_v3(self.list_to_vec3(normal[poly.c]))
                    normal_d = c4d.Vector(0.0, 0.0, 0.0)

                    set_normals(normaltag, polyidx, normal_a, normal_b, normal_c, normal_d)

                c4d_mesh.InsertTag(normaltag)

                # A Phong tag is needed to make C4D use the Normal Tag (seems to be done for Collada)
                phong = c4d.BaseTag(5612)
                c4d_mesh.InsertTag(phong)

        def parse_texcoords(index, c4d_mesh):
            texcoord_key = 'TEXCOORD_{}'.format(index)
            if texcoord_key in prim.attributes:
                uvs = BinaryData.get_data_from_accessor(gltf, prim.attributes[texcoord_key])

                if uvs:
                    uvtag = c4d.UVWTag(nb_poly)
                    uvtag.SetName(texcoord_key)
                    for i in range(0, nb_poly):
                        poly = c4d_mesh.GetPolygon(i)
                        aa = (uvs[poly.a][0], uvs[poly.a][1], 0.0)
                        bb = (uvs[poly.b][0], uvs[poly.b][1], 0.0)
                        cc = (uvs[poly.c][0], uvs[poly.c][1], 0.0)
                        uvtag.SetSlow(i, aa, bb, cc, (0.0, 0.0, 0.0))

                    c4d_mesh.InsertTag(uvtag)

        def parse_vertex_colors(index, c4d_mesh):
            colors = []
            color_key = 'COLOR_{}'.format(index)
            colortag = None
            if color_key in prim.attributes:
                colors = BinaryData.get_data_from_accessor(gltf, prim.attributes[color_key])
                if colors:
                    nb_verts = len(verts)
                    colortag = c4d.VertexColorTag(nb_verts)
                    colortag.SetPerPointMode(True)
                    colortag.SetName(color_key)
                    vtx_color_data = colortag.GetDataAddressW()

                    has_alpha = len(colors[0]) > 3
                    for i in range(nb_verts):
                        c4d.VertexColorTag.SetPoint(vtx_color_data, None, None, i, c4d.Vector4d(colors[i][0], colors[i][1], colors[i][2], colors[i][3] if has_alpha else 1.0))

                c4d_mesh.InsertTag(colortag)

                self.has_vertex_colors = True

            return colortag

        def parse_tangents():
            tangent = []
            if 'TANGENT' in prim.attributes:
                tangent = BinaryData.get_data_from_accessor(gltf, prim.attributes['TANGENT'])
                if tangent:
                    tangentTag = c4d.TangentTag(nb_poly)
                    for polyidx in range(0, nb_poly):
                        poly = c4d_mesh.GetPolygon(polyidx)
                        normal_a = self.switch_handedness_v3(self.list_to_vec3(tangent[poly.a]))
                        normal_b = self.switch_handedness_v3(self.list_to_vec3(tangent[poly.b]))
                        normal_c = self.switch_handedness_v3(self.list_to_vec3(tangent[poly.c]))
                        normal_d = c4d.Vector(0.0, 0.0, 0.0)

                        set_normals(tangentTag, polyidx, normal_a, normal_b, normal_c, normal_d)

                    c4d_mesh.InsertTag(tangentTag)

        vertex = BinaryData.get_data_from_accessor(gltf, prim.attributes['POSITION'])
        nb_vertices = len(vertex)

        # Vertices are stored under the form # [(1.0, 0.0, 0.0), (0.0, 0.0, 0.0) ...]
        verts = []
        for i in range(len(vertex)):
            vect = c4d.Vector(vertex[i][0], vertex[i][1], vertex[i][2])
            verts.append(self.switch_handedness_v3(vect))

        indices = BinaryData.get_data_from_accessor(gltf, prim.indices)
        nb_poly = len(indices) / 3

        c4d_mesh = c4d.PolygonObject(nb_vertices, nb_poly)
        c4d_mesh.SetAllPoints(verts)

        # Indices are stored like [(0,), (1,), (2,)]
        current_poly = 0
        for i in range(0, len(indices), 3):
            poly = c4d.CPolygon(indices[i + 2][0], indices[i + 1][0], indices[i][0])  # indice list is like [(0,), (1,), (2,)]
            c4d_mesh.SetPolygon(current_poly, poly)
            current_poly += 1

        parse_normals()

        # TANGENTS (Commented for now, "Tag not in sync" error popup in c4d)
        # parse_tangents()

        for texcoord_index in range(10):
            parse_texcoords(texcoord_index, c4d_mesh)

        mat = materials[prim.material]

        # Only parse COLORS_0
        colortag = parse_vertex_colors(0, c4d_mesh)
        self.make_vertex_colors_layer(mat, colortag)
        # Enable vertex colors for material

        if not gltf.data.materials[prim.material].double_sided:
            mat.SetParameter(c4d.TEXTURETAG_SIDE, c4d.SIDE_FRONT, c4d.DESCFLAGS_SET_NONE)

        mattag = c4d.TextureTag()
        mattag.SetParameter(c4d.TEXTURETAG_MATERIAL, mat, c4d.DESCFLAGS_SET_NONE)
        mattag.SetParameter(c4d.TEXTURETAG_PROJECTION, c4d.TEXTURETAG_PROJECTION_UVW, c4d.DESCFLAGS_GET_NONE)
        c4d_mesh.InsertTag(mattag)

        c4d_mesh.SetDirty(c4d.DIRTYFLAGS_ALL)

        return c4d_mesh

    def convert_mesh(self, gltf, mesh_index, c4d_object, materials):
        gltf_mesh = gltf.data.meshes[mesh_index]
        if len(gltf_mesh.primitives) == 1:
            return self.convert_primitive(gltf_mesh.primitives[0], gltf, materials)

        c4d_object = c4d.BaseObject(c4d.Onull)
        for prim in gltf_mesh.primitives:
            c4d_mesh = self.convert_primitive(prim, gltf, materials)
            c4d_mesh.InsertUnder(c4d_object)

        return c4d_object

    def get_texture_path(self):
        return os.path.join(os.path.split(c4d.documents.GetActiveDocument().GetParameter(c4d.DOCUMENT_FILEPATH, c4d.DESCFLAGS_GET_NONE))[0], 'tex')

    def setGradient(self, colorizer, low, high):
        gradient = colorizer.GetParameter(c4d.SLA_COLORIZER_GRADIENT, c4d.DESCFLAGS_SET_NONE)
        gradient.FlushKnots()
        gradient.InsertKnot(low, 1.0, 0, 0.5, 0)
        gradient.InsertKnot(high, 1.0, 1, 0, 1)
        colorizer.SetParameter(c4d.SLA_COLORIZER_GRADIENT, gradient, c4d.DESCFLAGS_SET_NONE)

    def setGradientBlackWhite(self, colorizer):
        self.setGradient(colorizer, self.COLOR_BLACK, self.COLOR_WHITE)

    def setGradientInvert(self, colorizer):
        self.setGradient(colorizer, self.COLOR_WHITE, self.COLOR_BLACK)

    def make_specular_diffuse(self, spec_gloss, mat):
        mat[c4d.MATERIAL_USE_COLOR] = True
        if 'diffuseTexture' not in spec_gloss:
            return

        diffusetexshader = self.gltf_textures[spec_gloss['diffuseTexture']['index']].to_c4d_shader()
        mat.SetParameter(c4d.MATERIAL_COLOR_SHADER, diffusetexshader, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(diffusetexshader)

    def make_vertex_colors_layer(self, mat, colortag):
        vtxcolorshader = c4d.BaseShader(1011137)
        vtxcolorshader.SetParameter(c4d.SLA_DIRTY_VMAP_OBJECT, colortag, c4d.DESCFLAGS_GET_NONE)

        if not mat.GetParameter(c4d.MATERIAL_COLOR_SHADER, c4d.DESCFLAGS_SET_NONE):
            mat.SetParameter(c4d.MATERIAL_COLOR_SHADER, vtxcolorshader, c4d.DESCFLAGS_SET_NONE)

        # check if vertex color already enabled:
        if not colortag or mat.GetReflectionLayerIndex(0).GetName() == 'Vertex Colors':
            return

        vtx_color_diffuse = mat.AddReflectionLayer()
        vtx_color_diffuse.SetFlags(c4d.REFLECTION_FLAG_NONE)
        vtx_color_diffuse.SetName("Vertex Colors")
        vtxcolorid = vtx_color_diffuse.GetDataID()
        mat.SetParameter(vtxcolorid + c4d.REFLECTION_LAYER_ENABLED, False, c4d.DESCFLAGS_SET_NONE)

        refid = vtxcolorid + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
        mat.SetParameter(refid, c4d.REFLECTION_DISTRIBUTION_LAMBERTIAN, c4d.DESCFLAGS_SET_NONE)
        mat.SetParameter(vtxcolorid + c4d.REFLECTION_LAYER_COLOR_TEXTURE, vtxcolorshader, c4d.DESCFLAGS_SET_NONE)

        mat.InsertShader(vtxcolorshader)

    def make_diffuse_layer(self, pbr_metal, mat):
        # Diffuse: set lambert + baseColor in color + inverted metal in LayerMask
        diffuse = mat.AddReflectionLayer()
        diffuse.SetName("BaseColor")
        diffuseid = diffuse.GetDataID()

        # To lambert
        refid = diffuseid + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
        mat.SetParameter(refid, c4d.REFLECTION_DISTRIBUTION_LAMBERTIAN, c4d.DESCFLAGS_SET_NONE)

        if pbr_metal.base_color_factor:
            base_color_factor = pbr_metal.base_color_factor
            base_color = c4d.Vector(base_color_factor[0], base_color_factor[1], base_color_factor[2])
            mat.SetParameter(diffuseid + c4d.REFLECTION_LAYER_COLOR_COLOR, base_color, c4d.DESCFLAGS_SET_NONE)

        # Set base color texture
        if pbr_metal.base_color_texture:
            basecolortexshader = self.gltf_textures[pbr_metal.base_color_texture.index].to_c4d_shader()
            mat.SetParameter(diffuseid + c4d.REFLECTION_LAYER_COLOR_TEXTURE, basecolortexshader, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(basecolortexshader)

        # Add inverter colorizer and set metalness texture
        if pbr_metal.metallic_roughness_texture:
            metaltexshader = self.gltf_textures[pbr_metal.metallic_roughness_texture.index].to_c4d_shader()

            colorizer = c4d.BaseShader(c4d.Xcolorizer)
            colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, metaltexshader, c4d.DESCFLAGS_SET_NONE)
            colorizer.InsertShader(metaltexshader)
            colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_BLUE, c4d.DESCFLAGS_SET_NONE)
            self.setGradientInvert(colorizer)
            mat.SetParameter(diffuseid + c4d.REFLECTION_LAYER_TRANS_TEXTURE, colorizer, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(colorizer)

            # Report metallic factor
            metallic_factor = pbr_metal.metallic_factor if pbr_metal.metallic_factor is not None else 1.0
            mat.SetParameter(diffuseid + c4d.REFLECTION_LAYER_TRANS_MIX_STRENGTH, metallic_factor, c4d.DESCFLAGS_SET_NONE)

    def makeTextureShader(self, filepath, alpha_only=False):
        sha = c4d.BaseList2D(c4d.Xbitmap)
        sha[c4d.BITMAPSHADER_FILENAME] = filepath
        if alpha_only:
            ls = c4d.LayerSet()
            ls.SetMode(c4d.LAYERSETMODE_LAYERALPHA)
            sha[c4d.BITMAPSHADER_LAYERSET] = ls

        return sha

    def make_specular_layer(self, spec_gloss, mat):
        reflect = mat.AddReflectionLayer()
        reflect.SetName("Reflectance_specular")
        reflectid = reflect.GetDataID()

        if 'specularFactor' in spec_gloss:
            spec = spec_gloss['specularFactor']
            specularColor = c4d.Vector(spec[0], spec[1], spec[2])
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_COLOR_COLOR, specularColor, c4d.DESCFLAGS_SET_NONE)

        if 'specularGlossinessTexture' in spec_gloss:
            speculartexshader = self.gltf_textures[spec_gloss['specularGlossinessTexture']['index']].to_c4d_shader()
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION, c4d.REFLECTION_DISTRIBUTION_GGX, c4d.DESCFLAGS_SET_NONE)
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_COLOR_TEXTURE, speculartexshader, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(speculartexshader)

            glossinesstexshader = self.gltf_textures[spec_gloss['specularGlossinessTexture']['index']].to_c4d_shader(True)
            gloss_colorizer = c4d.BaseShader(c4d.Xcolorizer)
            gloss_colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_LUMINANCE, c4d.DESCFLAGS_SET_NONE)
            gloss_colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, glossinesstexshader, c4d.DESCFLAGS_SET_NONE)
            gloss_colorizer.InsertShader(glossinesstexshader)
            self.setGradientInvert(gloss_colorizer)
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS, gloss_colorizer, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(gloss_colorizer)

        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS, spec_gloss.get('glossinessFactor', 1.0), c4d.DESCFLAGS_SET_NONE)

    def make_metallic_reflectance_layer(self, pbr_metal, mat):
        reflect = mat.AddReflectionLayer()
        reflect.SetName("Reflectance_metal")
        reflectid = reflect.GetDataID()

        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_FRESNEL_MODE, c4d.REFLECTION_FRESNEL_CONDUCTOR, c4d.DESCFLAGS_SET_NONE)

        if pbr_metal.base_color_factor:
            base_color_factor = pbr_metal.base_color_factor
            base_color = c4d.Vector(base_color_factor[0], base_color_factor[1], base_color_factor[2])
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_COLOR_COLOR, base_color, c4d.DESCFLAGS_SET_NONE)

        if pbr_metal.base_color_texture:
            basecolortexshader = self.gltf_textures[pbr_metal.base_color_texture.index].to_c4d_shader()
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION, c4d.REFLECTION_DISTRIBUTION_GGX, c4d.DESCFLAGS_SET_NONE)
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_COLOR_TEXTURE, basecolortexshader, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(basecolortexshader)

        metallic_factor = pbr_metal.metallic_factor if pbr_metal.metallic_factor is not None else 1.0
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_TRANS_BRIGHTNESS, metallic_factor, c4d.DESCFLAGS_SET_NONE)

        roughness_factor = pbr_metal.roughness_factor if pbr_metal.roughness_factor is not None else 1.0
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS, roughness_factor, c4d.DESCFLAGS_SET_NONE)

        if pbr_metal.metallic_roughness_texture:
            # Metalness
            metalnesstexshader = self.gltf_textures[pbr_metal.metallic_roughness_texture.index].to_c4d_shader()
            metal_colorizer = c4d.BaseShader(c4d.Xcolorizer)
            metal_colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_BLUE, c4d.DESCFLAGS_SET_NONE)
            metal_colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, metalnesstexshader, c4d.DESCFLAGS_SET_NONE)
            metal_colorizer.InsertShader(metalnesstexshader)
            self.setGradientBlackWhite(metal_colorizer)
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_TRANS_TEXTURE, metal_colorizer, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(metal_colorizer)

            # Roughness
            roughnesstexshader = self.gltf_textures[pbr_metal.metallic_roughness_texture.index].to_c4d_shader()
            rough_colorizer = c4d.BaseShader(c4d.Xcolorizer)
            rough_colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_GREEN, c4d.DESCFLAGS_SET_NONE)
            rough_colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, roughnesstexshader, c4d.DESCFLAGS_SET_NONE)
            rough_colorizer.InsertShader(roughnesstexshader)
            self.setGradientBlackWhite(rough_colorizer)
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS, rough_colorizer, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(rough_colorizer)

    def make_dielectric_reflectance_layer(self, pbr_metal, mat):
        reflect = mat.AddReflectionLayer()
        reflect.SetName("Reflectance_dielectric")
        reflectid = reflect.GetDataID()

        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_FRESNEL_MODE, c4d.REFLECTION_FRESNEL_DIELECTRIC, c4d.DESCFLAGS_SET_NONE)

        if pbr_metal.base_color_factor:
            base_color_factor = pbr_metal.base_color_factor
            base_color = c4d.Vector(base_color_factor[0], base_color_factor[1], base_color_factor[2])
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_COLOR_COLOR, base_color, c4d.DESCFLAGS_SET_NONE)

        if pbr_metal.base_color_texture:
            basecolortexshader = self.gltf_textures[pbr_metal.base_color_texture.index].to_c4d_shader()
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION, c4d.REFLECTION_DISTRIBUTION_GGX, c4d.DESCFLAGS_SET_NONE)
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_COLOR_TEXTURE, basecolortexshader, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(basecolortexshader)

        if pbr_metal.metallic_roughness_texture:
            # Roughness
            roughnesstexshader = self.gltf_textures[pbr_metal.metallic_roughness_texture.index].to_c4d_shader()
            rough_colorizer = c4d.BaseShader(c4d.Xcolorizer)
            rough_colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_GREEN, c4d.DESCFLAGS_SET_NONE)
            rough_colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, roughnesstexshader, c4d.DESCFLAGS_SET_NONE)
            rough_colorizer.InsertShader(roughnesstexshader)
            self.setGradientBlackWhite(rough_colorizer)
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS, rough_colorizer, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(rough_colorizer)

            # Metalness
            metalnesstexshader = self.gltf_textures[pbr_metal.metallic_roughness_texture.index].to_c4d_shader()
            metal_colorizer = c4d.BaseShader(c4d.Xcolorizer)
            metal_colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_BLUE, c4d.DESCFLAGS_SET_NONE)
            metal_colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, metalnesstexshader, c4d.DESCFLAGS_SET_NONE)
            metal_colorizer.InsertShader(metalnesstexshader)
            self.setGradientInvert(metal_colorizer)
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_TRANS_TEXTURE, metal_colorizer, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(metal_colorizer)

        roughness_factor = pbr_metal.roughness_factor if pbr_metal.roughness_factor is not None else 1.0
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS, roughness_factor, c4d.DESCFLAGS_SET_NONE)

    def set_normal_map(self, material, mat):
        if not material.normal_texture:
            return

        mat[c4d.MATERIAL_USE_NORMAL] = 1
        normaltexshader = self.gltf_textures[material.normal_texture.index].to_c4d_shader()
        mat.SetParameter(c4d.MATERIAL_NORMAL_SHADER, normaltexshader, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(normaltexshader)

    def set_alpha(self, material, mat):
        if material.alpha_mode not in ('BLEND', 'MASK'):
            mat[c4d.MATERIAL_USE_ALPHA] = 0
            return

        mat[c4d.MATERIAL_USE_ALPHA] = 1
        alpha_factor = 1.0
        diffuse_alpha_shader = None

        if material.extensions and 'KHR_materials_pbrSpecularGlossiness' in material.extensions:
            pbr_specular = material.extensions['KHR_materials_pbrSpecularGlossiness']
            alpha_factor = pbr_specular['diffuse_factor'][3] if 'diffuse_factor' in pbr_specular else 1.0
            if 'diffuseTexture' in pbr_specular:
                diffuse_alpha_shader = self.gltf_textures[pbr_specular['diffuseTexture']['index']].to_c4d_shader(alpha_only=True)

        elif material.pbr_metallic_roughness:
            pbr_metal = material.pbr_metallic_roughness
            if pbr_metal.base_color_texture:
                diffuse_alpha_shader = self.gltf_textures[pbr_metal.base_color_texture.index].to_c4d_shader(alpha_only=True)
            if pbr_metal.base_color_factor:
                alpha_factor = pbr_metal.base_color_factor[3] if pbr_metal.base_color_factor else 1.0

        if material.alpha_mode == 'BLEND':
            mat.SetParameter(c4d.MATERIAL_ALPHA_SOFT, True, c4d.DESCFLAGS_SET_NONE)
            if diffuse_alpha_shader:
                mat.SetParameter(c4d.MATERIAL_ALPHA_IMAGEALPHA, True, c4d.DESCFLAGS_SET_NONE)

                diffuse_alpha_shader = diffuse_alpha_shader
                alpha_colorizer = c4d.BaseShader(c4d.Xcolorizer)
                alpha_colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, diffuse_alpha_shader, c4d.DESCFLAGS_SET_NONE)
                alpha_colorizer.InsertShader(diffuse_alpha_shader)
                alpha_colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_LUMINANCE, c4d.DESCFLAGS_SET_NONE)
                mat.SetParameter(c4d.MATERIAL_ALPHA_SHADER, alpha_colorizer, c4d.DESCFLAGS_SET_NONE)
                mat.InsertShader(alpha_colorizer)

                # Apply factor
                alpha_color_from_factor = c4d.Vector(alpha_factor, alpha_factor, alpha_factor)
                self.setGradient(alpha_colorizer, self.COLOR_BLACK, alpha_color_from_factor)
            else:
                mat.SetParameter(c4d.MATERIAL_ALPHA_IMAGEALPHA, False, c4d.DESCFLAGS_SET_NONE)
                alpha_color_shader = c4d.BaseShader(c4d.Xcolor)
                alpha_color_shader.SetParameter(c4d.COLORSHADER_COLOR, self.COLOR_WHITE, c4d.DESCFLAGS_SET_NONE)
                alpha_color_shader.SetParameter(c4d.COLORSHADER_BRIGHTNESS, alpha_factor, c4d.DESCFLAGS_SET_NONE)
                mat.SetParameter(c4d.MATERIAL_ALPHA_SHADER, alpha_color_shader, c4d.DESCFLAGS_SET_NONE)
                mat.InsertShader(alpha_color_shader)

        elif material.alpha_mode == 'MASK':  # # Masking without texture doesn't really make sense
            if diffuse_alpha_shader:
                mat.InsertShader(diffuse_alpha_shader)
                mat.SetParameter(c4d.MATERIAL_ALPHA_SHADER, diffuse_alpha_shader, c4d.DESCFLAGS_SET_NONE)
                mat.SetParameter(c4d.MATERIAL_ALPHA_COLOR, self.COLOR_BLACK, c4d.DESCFLAGS_SET_NONE)
                cutoff = max(material.alpha_cutoff, 0.99)  # a full white color makes everything fully transparent
                delta_color = c4d.Vector(cutoff, cutoff, cutoff)
                mat.SetParameter(c4d.MATERIAL_ALPHA_DELTA, delta_color, c4d.DESCFLAGS_SET_NONE)

    def set_emissive(self, material, mat):
        if not material.emissive_texture and not material.emissive_factor:
            return

        has_valid_emission = False

        if material.emissive_texture:
            emitShader = self.gltf_textures[material.emissive_texture.index].to_c4d_shader()
            mat.SetParameter(c4d.MATERIAL_LUMINANCE_SHADER, emitShader, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(emitShader)
            has_valid_emission = True

        if material.emissive_factor:
            emit_factor = material.emissive_factor
            emit_color = c4d.Vector(emit_factor[0], emit_factor[1], emit_factor[2])
            mat.SetParameter(c4d.MATERIAL_LUMINANCE_COLOR, emit_color, c4d.DESCFLAGS_SET_NONE)
            if emit_factor[0] != 0.0 and emit_factor[1] != 0.0 and emit_factor[2] != 0.0:
                has_valid_emission = True

        if has_valid_emission:
            mat[c4d.MATERIAL_USE_LUMINANCE] = 1

    def create_material(self, name):
        mat = c4d.Material()
        mat.SetName(name)
        mat[c4d.MATERIAL_USE_ALPHA] = False
        mat[c4d.MATERIAL_USE_COLOR] = False
        mat[c4d.MATERIAL_USE_LUMINANCE] = False
        mat[c4d.MATERIAL_USE_NORMAL] = False
        mat[c4d.MATERIAL_USE_SPECULAR] = False
        mat[c4d.MATERIAL_USE_TRANSPARENCY] = False

        return mat

    def import_gltf_materials(self, gltf):
        ''' Might be replaced by imported c4d mat'''
        # Following tricks from https://forum.allegorithmic.com/index.php?topic=9757.0#msg85512
        materials = gltf.data.materials
        if not materials:
            return None

        imported_materials = {}
        for index, material in enumerate(materials):
            mat = self.create_material(material.name)

            if material.extensions and 'KHR_materials_pbrSpecularGlossiness' in material.extensions:
                mat[c4d.MATERIAL_USE_COLOR] = 1
                mat.RemoveReflectionAllLayers()
                spec_gloss = material.extensions['KHR_materials_pbrSpecularGlossiness']
                self.make_specular_diffuse(spec_gloss, mat)
                self.make_specular_layer(spec_gloss, mat)

            else:
                # Turn off Color
                mat[c4d.MATERIAL_USE_COLOR] = 0
                mat.RemoveReflectionAllLayers()

                pbr_metal = material.pbr_metallic_roughness
                if pbr_metal:
                    self.make_diffuse_layer(pbr_metal, mat)
                    self.make_metallic_reflectance_layer(pbr_metal, mat)
                    self.make_dielectric_reflectance_layer(pbr_metal, mat)

            self.set_alpha(material, mat)
            self.set_normal_map(material, mat)
            self.set_emissive(material, mat)

            imported_materials[index] = mat
            self.progress_callback("Importing materials", index + 1, len(materials))

        return imported_materials

    # Build an image shader for each image and add it to material channels by index
    def import_gltf_textures(self, gltf):
        dest_textures_path = self.get_texture_path()
        if not os.path.exists(dest_textures_path):
            os.mkdir(dest_textures_path)

        self.gltf_textures = []
        if gltf.data.textures is None:
            return

        for texture in gltf.data.textures:
            # 1. Copy texture to project directory
            image = gltf.data.images[texture.source]
            fullpath = os.path.join(self.model_dir, image.uri)
            if not os.path.exists(fullpath):
                print('Texture not found')
                return

            if not os.path.exists(dest_textures_path):
                os.mkdir(dest_textures_path)

            final_texture_path = os.path.join(dest_textures_path, '{}_{}'.format(texture.source, os.path.basename(fullpath)))
            if not os.path.exists(final_texture_path):
                shutil.copy(fullpath, final_texture_path)

            sampler = gltf.data.samplers[texture.sampler]
            texture = TextureWrapper(final_texture_path, sampler)

            # Copy texture to project textures directory
            self.gltf_textures.append(texture)  # TODO use list instead
            self.progress_callback("Importing textures", len(self.gltf_textures), len(gltf.data.images))

        print('Imported {} textures'.format(len(self.gltf_textures)))

    def switch_handedness_v3(self, v3):
        v3[2] = -v3[2]

        return v3

    def quat_to_eulerxyz(self, quat):
        x, y, z, w = quat

        import math
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        X = math.degrees(math.atan2(t0, t1))

        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        Y = math.degrees(math.asin(t2))

        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        Z = math.degrees(math.atan2(t3, t4))

        return c4d.Vector(math.radians(X), math.radians(Y), math.radians(Z))

    def convert_node(self, gltf, node_idx, materials=None):
        gltf_node = gltf.data.nodes[node_idx]
        c4d_object = None

        if gltf_node.mesh is not None:
            c4d_object = self.convert_mesh(gltf, gltf_node.mesh, c4d_object, materials)
        else:
            c4d_object = c4d.BaseObject(c4d.Onull)

        c4d_object.SetName(gltf_node.name if gltf_node.name else "GLTFObject")
        c4d_object.SetRotationOrder(5)  # Local XYZ
        c4d_mat = c4d.Matrix()

        if gltf_node.matrix:
            mat = gltf_node.matrix
            v1 = c4d.Vector(mat[0], mat[1], mat[2])
            v2 = c4d.Vector(mat[4], mat[5], mat[6])
            v3 = c4d.Vector(mat[8], mat[9], mat[10])
            off = c4d.Vector(mat[12], mat[13], mat[14])
            c4d_mat = c4d.Matrix(off, v1, v2, v3)
            c4d_object.SetMg(c4d_mat)

            pos = c4d_object.GetAbsPos()
            rot = c4d_object.GetAbsRot()

            pos[2] = -pos[2]

            rot[0] = -rot[0]
            rot[1] = -rot[1]

            c4d_object.SetAbsPos(pos)
            c4d_object.SetAbsRot(rot)

        else:
            if gltf_node.rotation:
                c4d_object.SetAbsRot(self.quat_to_eulerxyz(gltf_node.rotation))

            if gltf_node.scale:
                scale = gltf_node.scale
                c4d_object.SetAbsScale(c4d.Vector(scale[0], scale[1], scale[2]))

            if gltf_node.translation:
                tr = gltf_node.translation
                c4d_object.SetAbsPos(c4d.Vector(tr[0], tr[1], tr[2]))

            pos = c4d_object.GetAbsPos()
            rot = c4d_object.GetAbsRot()

            pos[0] = pos[0]
            pos[2] = -pos[2]
            rot[2] = -rot[2]

            c4d_object.SetAbsPos(pos)
            c4d_object.SetAbsRot(rot)

        return c4d_object

    def AbortImport(self):
        pass
        # if not self.is_done:
        #   c4d.documents.GetActiveDocument().EndUndo()
        #   c4d.documents.GetActiveDocument().DoUndo()
