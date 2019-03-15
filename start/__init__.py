"""
RoundedTube
Copyright: MAXON Computer GmbH
Written for Cinema 4D R18

Modified Date: 05/12/2018
"""

import os
import math
import sys
import c4d
import shutil

from gltfio.imp.gltf2_io_gltf import glTFImporter
from gltfio.imp.gltf2_io_binary import BinaryData
from c4d import plugins

# Be sure to use a unique ID obtained from www.plugincafe.com
PLUGIN_ID = 1025251

CURRENT_PATH = os.path.join('D:\\Softwares\\MAXON\\', 'plugins\\ImportGLTF')
# SAMPLE_PATH = CURRENT_PATH + '\\samples\\centaur'
# MODEL_PATH = SAMPLE_PATH + '\\scene.gltf'
sys.path.insert(0, CURRENT_PATH)
use_model_normals = False
doc = c4d.documents.GetActiveDocument()


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

        return sha


class ImportGLTF(plugins.ObjectData):
    COLOR_BLACK = c4d.Vector(0.0, 0.0, 0.0)
    COLOR_WHITE = c4d.Vector(1.0, 1.0, 1.0)

    def __init__(self, progress_callback=None):
        self.progress_callback = progress_callback
        self.sample_directory = ''
        self.gltf_textures = []
        self.gltf_materials = []
        pass

    def run(self, filepath, uid=None):
        import gltfio

        gltf = glTFImporter(filepath)
        success, txt = gltf.read()

        self.sample_directory = os.path.split(filepath)[0]

        # Images
        self.loadTextures(gltf)
        print('Imported {} textures'.format(len(self.gltf_textures)))

        # Materials
        imported_materials = self.loadMaterials(gltf)
        for index in imported_materials:
            c4d.documents.GetActiveDocument().InsertMaterial(imported_materials[index])
        print('Imported {} materials'.format(len(imported_materials)))

        # Nodes
        nodes = {}
        for nodeidx in range(len(gltf.data.nodes)):
            nodes[nodeidx] = self.convert_node(gltf, nodeidx, imported_materials)
            self.progress_callback("Nodes", nodeidx + 1, len(gltf.data.nodes))
        print('Imported {} nodes'.format(len(nodes.keys())))

        # Add parented objects to document
        current_document = c4d.documents.GetActiveDocument()
        for node in nodes.keys():
            if gltf.data.nodes[int(node)].children:
                for child in gltf.data.nodes[int(node)].children:
                    current_document.InsertObject(nodes[child], parent=nodes[node])

        # Add root objects to document
        for node in gltf.data.scenes[0].nodes:
            rot = nodes[node].GetRelRot()
            rot[1] += math.radians(180)
            nodes[node].SetRelRot(rot)
            nodes[node].SetRelScale([10.0, 10.0, 10.0])
            current_document.InsertObject(nodes[node])

        self.progress_callback('FINISHED', 1, 1)

    def convert_mesh(self, gltf, mesh_index, c4d_object, materials):

        # Helper functions
        def set_normals(normal_tag, polygon, normal_a, normal_b, normal_c, normal_d):
            def float2bytes(f):
                int_value = int(math.fabs(f * 32000.0))
                high_byte = int(int_value / 256)
                low_byte = int_value - 256 * high_byte

                if f < 0:
                    high_byte = 255 - high_byte
                    low_byte = 255 - low_byte

                return (low_byte, high_byte)

            normal_list = [normal_a, normal_b, normal_c, normal_d]
            normal_buffer = normal_tag.GetLowlevelDataAddressW()
            vector_size = 6
            component_size = 2

            for v in range(0, 4):
                normal = normal_list[v]
                component = [normal[0], normal[1], normal[2]]

                for c in range(0, 3):
                    low_byte, high_byte = float2bytes(component[c])

                    normal_buffer[normal_tag.GetDataSize() * polygon + v * vector_size + c * component_size + 0] = chr(low_byte)
                    normal_buffer[normal_tag.GetDataSize() * polygon + v * vector_size + c * component_size + 1] = chr(high_byte)

        gltf_mesh = gltf.data.meshes[mesh_index]

        # Import only first primitive for now
        prim = gltf_mesh.primitives[0]
        vertex = BinaryData.get_data_from_accessor(gltf, prim.attributes['POSITION'])
        verts = []
        for i in range(len(vertex)):
            vect = c4d.Vector(vertex[i][0], vertex[i][1], vertex[i][2])
            verts.append(self.switch_handedness_v3(vect))

        indices = BinaryData.get_data_from_accessor(gltf, prim.indices)

        c4d_mesh = c4d.PolygonObject(len(vertex), len(indices))
        c4d_mesh.SetAllPoints(verts)

        for i in range(0, len(indices), 3):
            poly = c4d.CPolygon(indices[i][0], indices[i + 1][0], indices[i + 2][0])
            c4d_mesh.SetPolygon(i, poly)

        # NORMALS
        if use_model_normals:
            normal = []
            if 'NORMAL' in prim.attributes:
                normal = BinaryData.get_data_from_accessor(gltf, prim.attributes['NORMAL'])

            if normal:
                nb_normal = len(indices)
                normaltag = c4d.NormalTag(nb_normal)
                for i in range(0, nb_normal):
                    poly = c4d_mesh.GetPolygon(i)
                    normal_a = normal[poly.a]
                    normal_b = normal[poly.b]
                    normal_c = normal[poly.c]
                    normal_d = (0.0, 0.0, 0.0)

                    set_normals(normaltag, i, normal_a, normal_b, normal_c, normal_d)

                c4d_mesh.InsertTag(normaltag)
        else:
            phong = c4d.BaseTag(5612)
            c4d_mesh.InsertTag(phong)

        # # UVS TANGENTS
        # uvs = []
        # tangent = []
        # if 'TANGENT' in prim.attributes:
        #     tangent = BinaryData.get_data_from_accessor(gltf, prim.attributes['TANGENT'])
        #     if tangent:
        #         nb_tangent = len(indices)
        #         tangentTag = c4d.TangentTag(nb_tangent)
        #         for i in range(0, nb_tangent):
        #             poly = c4d_mesh.GetPolygon(i)
        #             normal_a = tangent[poly.a]
        #             normal_b = tangent[poly.b]
        #             normal_c = tangent[poly.c]
        #             normal_d = (0.0, 0.0, 0.0, 0.0)

        #             set_normals(tangentTag, i, normal_a, normal_b, normal_c, normal_d)

        #         c4d_mesh.InsertTag(tangentTag)

        # VERTEX COLORS
        colors = []
        colortag = None
        if 'COLOR_0' in prim.attributes:
            colors = BinaryData.get_data_from_accessor(gltf, prim.attributes['COLOR_0'])
            if colors:
                nb_verts = len(verts)
                colortag = c4d.VertexColorTag(nb_verts)
                colortag.SetPerPointMode(True)
                colortag.SetName('GLTFVertexColor')
                vtx_color_data = colortag.GetDataAddressW()
                for i in range(nb_verts):
                    c4d.VertexColorTag.SetPoint(vtx_color_data, None, None, i, c4d.Vector4d(colors[i][0], colors[i][1], colors[i][2], colors[i][3]))

            c4d_mesh.InsertTag(colortag)

        if 'TEXCOORD_0' in prim.attributes:
            uvs = BinaryData.get_data_from_accessor(gltf, prim.attributes['TEXCOORD_0'])

            if uvs:
                nb_poly = len(indices)
                uvtag = c4d.UVWTag(nb_poly)
                for i in range(0, nb_poly):
                    poly = c4d_mesh.GetPolygon(i)
                    aa = (uvs[poly.a][0], uvs[poly.a][1], 0.0)
                    bb = (uvs[poly.b][0], uvs[poly.b][1], 0.0)
                    cc = (uvs[poly.c][0], uvs[poly.c][1], 0.0)
                    uvtag.SetSlow(i, aa, bb, cc, (0.0, 0.0, 0.0))

            c4d_mesh.InsertTag(uvtag)

        mat = materials[prim.material]
        if colortag:
            # Set material to use Vertex colors
            self.enable_vertex_colors_material(mat, colortag)

        if not gltf.data.materials[prim.material].double_sided:
            mat.SetParameter(c4d.TEXTURETAG_SIDE,c4d.SIDE_FRONT ,c4d.DESCFLAGS_SET_NONE)

        mattag = c4d.TextureTag()
        mattag.SetParameter(c4d.TEXTURETAG_MATERIAL, mat, c4d.DESCFLAGS_SET_NONE)
        mattag.SetParameter(c4d.TEXTURETAG_PROJECTION, c4d.TEXTURETAG_PROJECTION_UVW, c4d.DESCFLAGS_GET_NONE)
        c4d_mesh.InsertTag(mattag)

        return c4d_mesh

    def get_texture_path(self):
        return os.path.join(os.path.split(doc.GetParameter(c4d.DOCUMENT_FILEPATH, c4d.DESCFLAGS_GET_NONE))[0], 'tex')

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
        if not 'diffuseTexture' in spec_gloss:
            return

        diffusetexshader = self.gltf_textures[spec_gloss['diffuseTexture']['index']].to_c4d_shader()
        mat.SetParameter(c4d.MATERIAL_COLOR_SHADER, diffusetexshader, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(diffusetexshader)

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

    def makeTextureShader(self, filepath, alpha_only=False):
        sha = c4d.BaseList2D(c4d.Xbitmap)
        sha[c4d.BITMAPSHADER_FILENAME] = filepath
        if alpha_only:
            ls = c4d.LayerSet()
            ls.SetMode(c4d.LAYERSETMODE_LAYERALPHA)
            sha[c4d.BITMAPSHADER_LAYERSET] = ls

        return sha

    def do_update(self, mat):
        mat.Message(c4d.MSG_UPDATE)
        mat.Update(True, True)
        c4d.EventAdd()

    def enable_vertex_colors_material(self, mat, colortag):
        # multi: 1019397
        # single: 1011137
        mat[c4d.MATERIAL_USE_COLOR] = True
        vtxcolorshader = c4d.BaseShader(1011137)
        vtxcolorshader.SetParameter(c4d.SLA_DIRTY_VMAP_OBJECT, colortag, c4d.DESCFLAGS_GET_NONE)
        mat.SetParameter(c4d.MATERIAL_COLOR_SHADER, vtxcolorshader, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(vtxcolorshader)

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
            self.setGradientBlackWhite(gloss_colorizer)
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS, gloss_colorizer, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(gloss_colorizer)

        if 'glossinessFactor' in spec_gloss:
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS, 1.0 - spec_gloss['glossinessFactor'], c4d.DESCFLAGS_SET_NONE)

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

        if pbr_metal.metallic_factor:
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_TRANS_BRIGHTNESS, pbr_metal.metallic_factor, c4d.DESCFLAGS_SET_NONE)

        if pbr_metal.roughness_factor:
            mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS, pbr_metal.roughness_factor, c4d.DESCFLAGS_SET_NONE)

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

        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS, pbr_metal.roughness_factor, c4d.DESCFLAGS_SET_NONE)

    def set_normal_map(self, material, mat):
        if not material.normal_texture:
            return

        mat[c4d.MATERIAL_USE_NORMAL] = 1
        normaltexshader = self.gltf_textures[material.normal_texture.index].to_c4d_shader()
        mat.SetParameter(c4d.MATERIAL_NORMAL_SHADER, normaltexshader, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(normaltexshader)
        # if need flipY normalmap: mat.SetParameter(c4d.MATERIAL_NORMAL_REVERSEY, 1,  c4d.DESCFLAGS_SET_NONE)

    def set_alpha(self, material, mat):
        if material.alpha_mode not in ('BLEND', 'MASK'):
            mat[c4d.MATERIAL_USE_ALPHA] = 0
            return
        else:
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

        mat[c4d.MATERIAL_USE_LUMINANCE] = 1
        if material.emissive_texture:
            emitShader = self.gltf_textures[material.emissive_texture.index].to_c4d_shader()
            mat.SetParameter(c4d.MATERIAL_LUMINANCE_SHADER, emitShader, c4d.DESCFLAGS_SET_NONE)
            mat.InsertShader(emitShader)

        if material.emissive_factor:
            emit_factor = material.emissive_factor
            emit_color = c4d.Vector(emit_factor[0], emit_factor[1], emit_factor[2])
            mat.SetParameter(c4d.MATERIAL_LUMINANCE_COLOR, emit_color, c4d.DESCFLAGS_SET_NONE)


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

    def loadMaterials(self, gltf):
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
            self.progress_callback("Material", index + 1, len(materials))

        return imported_materials

    # Build an image shader for each image and add it to material channels by index
    def loadTextures(self, gltf):
        dest_textures_path = self.get_texture_path()
        self.gltf_textures = []

        if gltf.data.textures is None:
            return

        for texture in gltf.data.textures:
            # 1. Copy texture to project directory
            image = gltf.data.images[texture.source]
            fullpath = os.path.join(self.sample_directory, image.uri).replace('/', '\\')
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
            self.gltf_textures.append(texture)  #TODO use list instead
            self.progress_callback("Texture", len(self.gltf_textures), len(gltf.data.images))

    def switch_handedness_v3(self, v3):
        v3[2] = -v3[2]
        return v3

    def switch_handedness_rot(self, quat):
        quat[0] = -quat[0]
        quat[1] = -quat[1]

        return quat
        # axis = quat.v
        # angle = quat.w
        # axis[2] = -axis[2]
        # quat.SetAxis(axis, angle)

        # return quat

    def gtf_to_c4d_quat(self, quat):
        qx, qy, qz, qw = quat
        axis = [1.0, 0.0, 0.0]
        angle = 2 * math.acos(qw)
        if angle != 0 and qw * qw != 1:
            axis[0] = qx / math.sqrt(1 - qw * qw)
            axis[1] = qy / math.sqrt(1 - qw * qw)
            axis[2] = qz / math.sqrt(1 - qw * qw)

        c4d_quat = c4d.Quaternion()
        c4d_quat.SetAxis(axis, angle)

        return c4d_quat

    def convert_node(self, gltf, node_idx, materials=None):
        gltf_node = gltf.data.nodes[node_idx]
        c4d_object = None
        print("CONVERTING {}".format(node_idx))

        if gltf_node.mesh is not None:
            c4d_object = self.convert_mesh(gltf, gltf_node.mesh, c4d_object, materials)
        else:
            c4d_object = c4d.BaseObject(c4d.Onull)

        c4d_object.SetName(gltf_node.name if gltf_node.name else "GLTFObject")
        c4d_mat = c4d.Matrix()
        if gltf_node.matrix:
            mat = gltf_node.matrix
            v1 = c4d.Vector(mat[0], mat[1], mat[2])
            v2 = c4d.Vector(mat[4], mat[5], mat[6])
            v3 = c4d.Vector(mat[8], mat[9], mat[10])
            off = c4d.Vector(mat[12], mat[13], mat[14])
            c4d_mat = c4d.Matrix(off, v1, v2, v3)
        else:
            if gltf_node.translation:
                c4d_mat.off = c4d.Vector(gltf_node.translation[0], gltf_node.translation[1], gltf_node.translation[2])
            if gltf_node.rotation:
                c4d_quat = self.gtf_to_c4d_quat(gltf_node.rotation)
                c4d_mat = c4d_mat * c4d_quat.GetMatrix()
            if gltf_node.scale:
                scale = gltf_node.scale
                c4d_scalemat = c4d.Matrix()
                c4d_scalemat.v1[0] = scale[0]
                c4d_scalemat.v2[1] = scale[1]
                c4d_scalemat.v2[2] = scale[2]
                c4d_mat = c4d_mat * c4d_scalemat

        c4d_object.SetMl(c4d_mat)

        # Convert to left-handed
        c4d_object.SetRelPos(self.switch_handedness_v3(c4d_object.GetRelPos()))
        c4d_object.SetRelPos(self.switch_handedness_v3(c4d.Vector(0.0, 0.0, 0.0)))
        c4d_object.SetRelRot(self.switch_handedness_rot(c4d_object.GetRelRot()))
        c4d_object.SetRelScale(self.switch_handedness_v3(c4d_object.GetRelScale()))
        print("CONVERTED {}".format(node_idx))
        return c4d_object
