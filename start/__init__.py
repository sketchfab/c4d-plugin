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

from c4d import plugins, utils, bitmaps, gui

# Be sure to use a unique ID obtained from www.plugincafe.com
PLUGIN_ID = 1025251

CURRENT_PATH = os.path.join('D:\\Softwares\\MAXON\\', 'plugins\\ImportGLTF')
SAMPLE_PATH = CURRENT_PATH + '\\samples\\camera'
MODEL_PATH = SAMPLE_PATH + '\\scene.gltf'
sys.path.insert(0, CURRENT_PATH)

from gltfio.imp.gltf2_io_gltf import glTFImporter
from gltfio.imp.gltf2_io_binary import BinaryData

doc = c4d.documents.GetActiveDocument()
class ImportGLTF(plugins.ObjectData):
    # """RoundedTube Generator"""


    # # define the number of handles that will be drawn, it's actually a constant.
    # HANDLECOUNT = 5


    # Enable few optimizations, take a look at the GetVirtualObjects method for more information.
    def __init__(self):
        pass


    @staticmethod
    def run():
        import gltfio

        gltf = glTFImporter(MODEL_PATH)
        success, txt = gltf.read()

        print('no')
        imported_images = ImportGLTF.loadImages(gltf)
        for index in imported_images:
            print('{} {}'.format(index, imported_images[index]))

        imported_materials = ImportGLTF.loadMaterials(gltf, imported_images)
        for index in imported_materials:
            print('{} {}'.format(index, imported_materials[index]))
            c4d.documents.GetActiveDocument().InsertMaterial(imported_materials[index])


        nodes = {}
        for nodeidx in range(len(gltf.data.nodes)):
            nodes[nodeidx] = ImportGLTF.convert_node(gltf, nodeidx, imported_materials)

        doc = c4d.documents.GetActiveDocument()
        for node in nodes.keys():
            if gltf.data.nodes[int(node)].children:
                for child in gltf.data.nodes[int(node)].children:
                    doc.InsertObject(nodes[child], parent=nodes[node])

        for node in gltf.data.scenes[0].nodes:
            doc.InsertObject(nodes[node])


    @staticmethod
    def convert_mesh(gltf, mesh_index, c4d_object, materials):
        gltf_mesh = gltf.data.meshes[mesh_index]
        uvs = []
        # for prim in gltf_mesh.primitives:
        prim = gltf_mesh.primitives[0]
        vertex = BinaryData.get_data_from_accessor(gltf, prim.attributes['POSITION'])
        normal = BinaryData.get_data_from_accessor(gltf, prim.attributes['NORMAL'])
        if 'TEXCOORD_0' in prim.attributes:
            uvs = BinaryData.get_data_from_accessor(gltf, prim.attributes['TEXCOORD_0'])

        indices = BinaryData.get_data_from_accessor(gltf, prim.indices)
        # tx = BinaryData.get_data_from_accessor(gltf, prim.attributes['TEXCOORD_0'])
        # print('Nb tx {}'.format(len(vertex)))

        c4d_mesh = c4d.PolygonObject(len(vertex), len(indices))

        verts = []
        for i in range(len(vertex)):
            vect = c4d.Vector(vertex[i][0], vertex[i][1],vertex[i][2])
            verts.append(vect)

        c4d_mesh.SetAllPoints(verts)

        tris = []
        for i in range(0, len(indices), 3):
            poly = c4d.CPolygon(indices[i][0], indices[i+1][0], indices[i+2][0])
            c4d_mesh.SetPolygon(i, poly)

        # if normal:
        #     nb_poly = len(indices)
        #     normtag = c4d.NormalTag( nb_poly )
        #     normtag.__init__( nb_poly )
        #     for i in range(0, nb_poly):
        #         poly = c4d_mesh.GetPolygon(i)
        #         aa = (normal[poly.a][0], normal[poly.a][1], normal[poly.a][2])
        #         bb = (normal[poly.b][0], normal[poly.b][1], normal[poly.b][2])
        #         cc = (normal[poly.c][0], normal[poly.c][1], normal[poly.c][2])
        #         normtag.SetSlow(i, aa, bb, cc, (0.0, 0.0, 0.0))

        mat = materials[prim.material]
        mattag = c4d.TextureTag()
        mattag.SetParameter(c4d.TEXTURETAG_MATERIAL, mat, c4d.DESCFLAGS_SET_NONE)
        mattag.SetParameter(c4d.TEXTURETAG_PROJECTION, c4d.TEXTURETAG_PROJECTION_UVW, c4d.DESCFLAGS_GET_NONE)

        phong = c4d.BaseTag(5612)
        c4d_mesh.InsertTag(phong)
        c4d_mesh.InsertTag(mattag)

        if uvs:
            nb_poly = len(indices)
            uvtag = c4d.UVWTag( nb_poly )
            uvtag.__init__( nb_poly )
            for i in range(0, nb_poly):
                poly = c4d_mesh.GetPolygon(i)
                aa = (uvs[poly.a][0], uvs[poly.a][1], 0.0)
                bb = (uvs[poly.b][0], uvs[poly.b][1], 0.0)
                cc = (uvs[poly.c][0], uvs[poly.c][1], 0.0)
                uvtag.SetSlow(i, aa, bb, cc, (0.0, 0.0, 0.0))


            c4d_mesh.InsertTag(uvtag)


        return c4d_mesh

    @staticmethod
    def get_texture_path():
        return os.path.join(os.path.split(doc.GetParameter(c4d.DOCUMENT_FILEPATH, c4d.DESCFLAGS_GET_NONE))[0], 'tex')

    @staticmethod
    def makeTextureShader(path):
        shtex = c4d.BaseShader(5833)
        shtex[c4d.BITMAPSHADER_FILENAME] = path
        return shtex

    @staticmethod
    def setGradientBlackWhite(colorizer):
        gradient = colorizer.GetParameter(c4d.SLA_COLORIZER_GRADIENT, c4d.DESCFLAGS_SET_NONE)
        gradient.FlushKnots()
        gradient.InsertKnot(c4d.Vector(0.0, 0.0, 0.0), 1.0, 0, 0.5, 0)
        gradient.InsertKnot(c4d.Vector(1.0,1.0, 1.0), 1.0, 1, 0, 1)
        colorizer.SetParameter(c4d.SLA_COLORIZER_GRADIENT, gradient, c4d.DESCFLAGS_SET_NONE)

    @staticmethod
    def setGradientInvert(colorizer):
        gradient = colorizer.GetParameter(c4d.SLA_COLORIZER_GRADIENT, c4d.DESCFLAGS_SET_NONE)
        gradient.FlushKnots()
        gradient.InsertKnot(c4d.Vector(1.0, 1.0, 1.0), 1.0, 0, 0.5, 0)
        gradient.InsertKnot(c4d.Vector(0.0,0.0, 0.0), 1.0, 1, 0, 1)
        colorizer.SetParameter(c4d.SLA_COLORIZER_GRADIENT, gradient, c4d.DESCFLAGS_SET_NONE)

    @staticmethod
    def make_diffuse_layer(material, mat, imported_images):
        # Diffuse: set lambert + baseColor in color + inverted metal in LayerMask
        diffuse = mat.AddReflectionLayer()
        diffuse.SetName("BaseColor")
        diffuseid = diffuse.GetDataID()

        # To lambert
        refid = diffuseid + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
        mat.SetParameter(refid, c4d.REFLECTION_DISTRIBUTION_LAMBERTIAN, c4d.DESCFLAGS_SET_NONE)

        # Set base color texture
        basecolortexshader = ImportGLTF.makeTextureShader(imported_images[material.pbr_metallic_roughness.base_color_texture.index])
        mat.SetParameter(diffuseid + c4d.REFLECTION_LAYER_COLOR_TEXTURE, basecolortexshader, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(basecolortexshader)

        # Add inverter colorizer and set metalness texture
        metaltexshader = ImportGLTF.makeTextureShader(imported_images[material.pbr_metallic_roughness.metallic_roughness_texture.index])

        colorizer = c4d.BaseShader(c4d.Xcolorizer)
        colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, metaltexshader, c4d.DESCFLAGS_SET_NONE)
        colorizer.InsertShader(metaltexshader)
        colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_BLUE, c4d.DESCFLAGS_SET_NONE)
        ImportGLTF.setGradientInvert(colorizer)
        mat.SetParameter(diffuseid + c4d.REFLECTION_LAYER_TRANS_TEXTURE, colorizer, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(colorizer)

    @staticmethod
    def makeTextureShader(filepath):
        sha = c4d.BaseList2D(c4d.Xbitmap)
        sha[c4d.BITMAPSHADER_FILENAME] = filepath
        return sha

    @staticmethod
    def do_update(mat):
        mat.Message( c4d.MSG_UPDATE )
        mat.Update( True, True )
        c4d.EventAdd()

    @staticmethod
    def make_reflectance_layer(material, mat, imported_images):
        reflect = mat.AddReflectionLayer()
        reflect.SetName("Reflectance_metal")
        reflectid = reflect.GetDataID()

        basecolortexshader = ImportGLTF.makeTextureShader(imported_images[material.pbr_metallic_roughness.base_color_texture.index])
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION, c4d.REFLECTION_DISTRIBUTION_GGX, c4d.DESCFLAGS_SET_NONE)
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_COLOR_TEXTURE, basecolortexshader, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(basecolortexshader)

        # Roughness
        roughnesstexshader = ImportGLTF.makeTextureShader(imported_images[material.pbr_metallic_roughness.metallic_roughness_texture.index])
        rough_colorizer = c4d.BaseShader(c4d.Xcolorizer)
        rough_colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_GREEN, c4d.DESCFLAGS_SET_NONE)
        rough_colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, roughnesstexshader, c4d.DESCFLAGS_SET_NONE)
        rough_colorizer.InsertShader(roughnesstexshader)
        ImportGLTF.setGradientBlackWhite(rough_colorizer)
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS, rough_colorizer, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(rough_colorizer)

        # Metalness
        metalnesstexshader = ImportGLTF.makeTextureShader(imported_images[material.pbr_metallic_roughness.metallic_roughness_texture.index])
        metal_colorizer = c4d.BaseShader(c4d.Xcolorizer)
        metal_colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_BLUE, c4d.DESCFLAGS_SET_NONE)
        metal_colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, metalnesstexshader, c4d.DESCFLAGS_SET_NONE)
        metal_colorizer.InsertShader(metalnesstexshader)
        ImportGLTF.setGradientBlackWhite(metal_colorizer)
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_TRANS_TEXTURE, metal_colorizer, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(metal_colorizer)

        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_FRESNEL_MODE, c4d.REFLECTION_FRESNEL_CONDUCTOR, c4d.DESCFLAGS_SET_NONE)
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_TRANS_BRIGHTNESS, material.pbr_metallic_roughness.metallic_factor, c4d.DESCFLAGS_SET_NONE)
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS, material.pbr_metallic_roughness.roughness_factor, c4d.DESCFLAGS_SET_NONE)

    @staticmethod
    def make_dielectric_reflectance_layer(material, mat, imported_images):
        reflect = mat.AddReflectionLayer()
        reflect.SetName("Reflectance_dielectric")
        reflectid = reflect.GetDataID()

        basecolortexshader = ImportGLTF.makeTextureShader(imported_images[material.pbr_metallic_roughness.base_color_texture.index])
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION, c4d.REFLECTION_DISTRIBUTION_GGX, c4d.DESCFLAGS_SET_NONE)
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_COLOR_TEXTURE, basecolortexshader, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(basecolortexshader)

        # Roughness
        roughnesstexshader = ImportGLTF.makeTextureShader(imported_images[material.pbr_metallic_roughness.metallic_roughness_texture.index])
        rough_colorizer = c4d.BaseShader(c4d.Xcolorizer)
        rough_colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_GREEN, c4d.DESCFLAGS_SET_NONE)
        rough_colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, roughnesstexshader, c4d.DESCFLAGS_SET_NONE)
        rough_colorizer.InsertShader(roughnesstexshader)
        ImportGLTF.setGradientBlackWhite(rough_colorizer)
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_SHADER_ROUGHNESS, rough_colorizer, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(rough_colorizer)

        # Metalness
        metalnesstexshader = ImportGLTF.makeTextureShader(imported_images[material.pbr_metallic_roughness.metallic_roughness_texture.index])
        metal_colorizer = c4d.BaseShader(c4d.Xcolorizer)
        metal_colorizer.SetParameter(c4d.SLA_COLORIZER_INPUT, c4d.SLA_COLORIZER_INPUT_BLUE, c4d.DESCFLAGS_SET_NONE)
        metal_colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, metalnesstexshader, c4d.DESCFLAGS_SET_NONE)
        metal_colorizer.InsertShader(metalnesstexshader)
        ImportGLTF.setGradientInvert(metal_colorizer)
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_TRANS_TEXTURE, metal_colorizer, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(metal_colorizer)

        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_FRESNEL_MODE, c4d.REFLECTION_FRESNEL_DIELECTRIC, c4d.DESCFLAGS_SET_NONE)
        mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_MAIN_VALUE_ROUGHNESS, material.pbr_metallic_roughness.roughness_factor, c4d.DESCFLAGS_SET_NONE)

    @staticmethod
    def set_normal_map(material, mat, imported_images):
        mat[c4d.MATERIAL_USE_NORMAL] = 1
        normaltexshader = ImportGLTF.makeTextureShader(imported_images[material.normal_texture.index])
        mat.SetParameter(c4d.MATERIAL_NORMAL_SHADER, normaltexshader, c4d.DESCFLAGS_SET_NONE)
        mat.InsertShader(normaltexshader)
        # if need flipY normalmap: mat.SetParameter(c4d.MATERIAL_NORMAL_REVERSEY, 1,  c4d.DESCFLAGS_SET_NONE)

    @staticmethod
    def loadMaterials(gltf, imported_images):
        ''' Might be replaced by imported c4d mat'''
        # Following tricks from https://forum.allegorithmic.com/index.php?topic=9757.0#msg85512
        materials = gltf.data.materials
        imported_materials = {}
        for index, material in enumerate(materials):
            mat = c4d.Material()
            mat.SetName(material.name)

            # Turn off Color
            mat[c4d.MATERIAL_USE_COLOR] = 0
            mat.RemoveReflectionAllLayers()

            ImportGLTF.make_diffuse_layer(material, mat, imported_images)
            ImportGLTF.make_reflectance_layer(material, mat, imported_images)
            ImportGLTF.make_dielectric_reflectance_layer(material, mat, imported_images)
            ImportGLTF.set_normal_map(material, mat, imported_images)

            # masktexid = diffuseid  + c4d.REFLECTION_LAYER_COLOR_TEXTURE
            # img_shader = imported_images[material.normalTexture]

            # colorizer = c4d.BaseShader(c4d.Xcolorizer)
            # mat.SetParameter(c4d.SLA_COLORIZER_GRADIENT, colorizer, c4d.DESCFLAGS_SET_NONE)

            # mat.InsertShader(img_shader)
            # mat.SetParameter(coltexid, sha, c4d.DESCFLAGS_SET_NONE)

            # # ACCESS texture from color shader
            # mat[c4d.MATERIAL_COLOR_SHADER].GetNext()[c4d.BITMAPSHADER_FILENAME]

            # # Set as Metallic
            # fid = reflectid + c4d.REFLECTION_LAYER_FRESNEL_MODE
            # mat.SetParameter(reflectid + c4d.REFLECTION_LAYER_FRESNEL_MODE, c4d.REFLECTION_FRESNEL_CONDUCTOR, c4d.DESCFLAGS_SET_NONE)
            # # or mat.SetParameter(fid, c4d.REFLECTION_FRESNEL_DIELECTRIC, c4d.DESCFLAGS_SET_NONE)

            # distribID = reflectid + c4d.REFLECTION_LAYER_MAIN_DISTRIBUTION
            # mat.SetParameter(distribID, c4d.REFLECTION_DISTRIBUTION_GGX, c4d.DESCFLAGS_SET_NONE)
            imported_materials[index] = mat

        return imported_materials


    # Build an image shader for each image and add it to material channels by index
    @staticmethod
    def loadImages(gltf):
        dest_textures_path = ImportGLTF.get_texture_path()
        imported_images = {}
        for index, image in enumerate(gltf.data.images):
            fullpath = os.path.join(SAMPLE_PATH, image.uri)
            if not os.path.exists(fullpath):
                print('Texture not found')
                return

            final_texture_path = os.path.join(dest_textures_path, '{}_{}'.format(index, os.path.basename(fullpath)))

            # Copy texture to project textures directory
            shutil.copy(fullpath, final_texture_path)
            imported_images[index] = str(os.path.basename(final_texture_path))
            #c4d.documents.GetActiveDocument().InsertShader(sha)



        return imported_images

            # mat.InsertShader( sha )
            # mat[c4d.MATERIAL_COLOR_SHADER]  = sha

            # mat.Message( c4d.MSG_UPDATE )
            # mat.Update( True, True )

            # mat.Update( True, True )
            # tag     = c4d.BaseTag( c4d.Ttexture )
            # tag[c4d.TEXTURETAG_MATERIAL]    = mat
            # c4d.documents.GetActiveDocument().GetObjects().InsertTag(tag)

            # c4d.EventAdd()


    @staticmethod
    def convert_node(gltf, node_idx, materials):
        gltf_node = gltf.data.nodes[node_idx]
        c4d_object = None
        if gltf_node.mesh is not None:
               c4d_object = ImportGLTF.convert_mesh(gltf, gltf_node.mesh, c4d_object, materials)
        else:
            c4d_object = c4d.BaseObject(c4d.Onull)

        c4d_object.SetName(gltf_node.name if gltf_node.name else "GLTFObject")

        if gltf_node.translation:
            c4d_object.SetRelPos(gltf_node.translation)
        if gltf_node.rotation:
            c4d_object.SetRelRot(gltf_node.rotation)
        if gltf_node.scale:
            c4d_object.SetRelScale(gltf_node.scale)



        # pcnt = c4d_object.GetDataInstance().GetPointCount()
        # points = c4d_object.GetDataInstance().GetAllPoints()
        # print(pcnt)
        return c4d_object


    # # Helper method to set the local axis of the object.
    # @staticmethod
    # def SetAxis(op, axis):
    #     if axis is c4d.PRIM_AXIS_YP: return
    #     padr = op.GetAllPoints()
    #     if padr is None: return

    #     elif axis is c4d.PRIM_AXIS_XP:
    #         for i, p in enumerate(padr):
    #             op.SetPoint(i, c4d.Vector( p.y, -p.x, p.z))
    #     elif axis is c4d.PRIM_AXIS_XN:
    #         for i, p in enumerate(padr):
    #             op.SetPoint(i, c4d.Vector(-p.y, p.x, p.z))
    #     elif axis is c4d.PRIM_AXIS_YN:
    #         for i, p in enumerate(padr):
    #             op.SetPoint(i, c4d.Vector(-p.x, -p.y, p.z))
    #     elif axis is c4d.PRIM_AXIS_ZP:
    #         for i, p in enumerate(padr):
    #             op.SetPoint(i, c4d.Vector(p.x, -p.z, p.y))
    #     elif axis is c4d.PRIM_AXIS_ZN:
    #         for i, p in enumerate(padr):
    #             op.SetPoint(i, c4d.Vector(p.x, p.z, -p.y))

    #     op.Message(c4d.MSG_UPDATE)


    # # Helper method to determine how point should be swapped according to the local axis.
    # @staticmethod
    # def SwapPoint(p, axis):
    #     if axis is c4d.PRIM_AXIS_XP:
    #         return c4d.Vector(p.y, -p.x, p.z)
    #     elif axis is c4d.PRIM_AXIS_XN:
    #         return c4d.Vector(-p.y, p.x, p.z)
    #     elif axis is c4d.PRIM_AXIS_YN:
    #         return c4d.Vector(-p.x, -p.y, p.z)
    #     elif axis is c4d.PRIM_AXIS_ZP:
    #         return c4d.Vector(p.x, -p.z, p.y)
    #     elif axis is c4d.PRIM_AXIS_ZN:
    #         return c4d.Vector(p.x, p.z, -p.y)
    #     return p


    # # Override method, called when the object is initialized to set default values.
    # def Init(self, op):
    #     self.InitAttr(op, float, [c4d.PY_TUBEOBJECT_RAD])
    #     self.InitAttr(op, float, [c4d.PY_TUBEOBJECT_IRADX])
    #     self.InitAttr(op, float, [c4d.PY_TUBEOBJECT_IRADY])
    #     self.InitAttr(op, float, [c4d.PY_TUBEOBJECT_SUB])
    #     self.InitAttr(op, int, [c4d.PY_TUBEOBJECT_ROUNDSUB])
    #     self.InitAttr(op, float, [c4d.PY_TUBEOBJECT_ROUNDRAD])
    #     self.InitAttr(op, int, [c4d.PY_TUBEOBJECT_SEG])
    #     self.InitAttr(op, int, [c4d.PRIM_AXIS])

    #     op[c4d.PY_TUBEOBJECT_RAD]= 200.0
    #     op[c4d.PY_TUBEOBJECT_IRADX] = 50.0
    #     op[c4d.PY_TUBEOBJECT_IRADY] = 50.0
    #     op[c4d.PY_TUBEOBJECT_SUB] = 1
    #     op[c4d.PY_TUBEOBJECT_ROUNDSUB] = 8
    #     op[c4d.PY_TUBEOBJECT_ROUNDRAD] = 10.0
    #     op[c4d.PY_TUBEOBJECT_SEG] = 36
    #     op[c4d.PRIM_AXIS] = c4d.PRIM_AXIS_YP
    #     return True


    # # Override method, react to some messages received to react to some event.
    # def Message(self, node, type, data):

    #     # MSG_DESCRIPTION_VALIDATE is called after each parameter change. It allows checking of the input value to correct it if not.
    #     if type == c4d.MSG_DESCRIPTION_VALIDATE:
    #         node[c4d.PY_TUBEOBJECT_IRADX] = c4d.utils.ClampValue(node[c4d.PY_TUBEOBJECT_IRADX], 0.0, node[c4d.PY_TUBEOBJECT_RAD])
    #         node[c4d.PY_TUBEOBJECT_ROUNDRAD] = c4d.utils.ClampValue( node[c4d.PY_TUBEOBJECT_ROUNDRAD], 0.0, node[c4d.PY_TUBEOBJECT_IRADX])

    #     # MSH_MENUPREPARE is called when the user presses the Menu entry for this object. It allows to setup our object. In this case, it defines the Phong by adding a Phong Tag to the generator.
    #     elif type == c4d.MSG_MENUPREPARE:
    #         node.SetPhong(True, False, c4d.utils.DegToRad(40.0))

    #     return True


    # # Override method, should return the number of handle.
    # def GetHandleCount(self, op):
    #     return self.HANDLECOUNT


    # # Override method, called to know the position of a handle.
    # def GetHandle(self, op, i, info):

    #     rad = op[c4d.PY_TUBEOBJECT_RAD]
    #     if rad is None: rad = 200.0
    #     iradx = op[c4d.PY_TUBEOBJECT_IRADX]
    #     if iradx is None: iradx = 50.0
    #     irady = op[c4d.PY_TUBEOBJECT_IRADY]
    #     if irady is None: irady = 50.0
    #     rrad = op[c4d.PY_TUBEOBJECT_ROUNDRAD]
    #     if rrad is None: rrad = 10.0
    #     axis = op[c4d.PRIM_AXIS]
    #     if axis is None: return

    #     if i is 0:
    #         info.position = c4d.Vector(rad, 0.0, 0.0)
    #         info.direction = c4d.Vector(1.0, 0.0, 0.0)
    #     elif i is 1:
    #         info.position = c4d.Vector(rad+iradx, 0.0, 0.0)
    #         info.direction = c4d.Vector(1.0, 0.0, 0.0)
    #     elif i is 2:
    #         info.position = c4d.Vector(rad, irady, 0.0)
    #         info.direction = c4d.Vector(0.0, 1.0, 0.0)
    #     elif i is 3:
    #         info.position = c4d.Vector(rad+iradx, irady-rrad, 0.0)
    #         info.direction = c4d.Vector(0.0, -1.0, 0.0)
    #     elif i is 4:
    #         info.position = c4d.Vector(rad+iradx-rrad, irady, 0.0)
    #         info.direction = c4d.Vector(-1.0, 0.0, 0.0)

    #     info.position = RoundedTube.SwapPoint(info.position, axis)
    #     info.direction = RoundedTube.SwapPoint(info.direction, axis)
    #     info.type = c4d.HANDLECONSTRAINTTYPE_LINEAR


    # # Override method, called when the user moves a handle. This is the place to set parameters.
    # def SetHandle(self, op, i, p, info):
    #     data = op.GetDataInstance()
    #     if data is None: return

    #     tmp = c4d.HandleInfo()
    #     self.GetHandle(op, i, tmp)

    #     val = (p-tmp.position)*info.direction

    #     if i is 0:
    #         op[c4d.PY_TUBEOBJECT_RAD] = utils.FCut(op[c4d.PY_TUBEOBJECT_RAD]+val, op[c4d.PY_TUBEOBJECT_IRADX], sys.maxint)
    #     elif i is 1:
    #         op[c4d.PY_TUBEOBJECT_IRADX] = utils.FCut(op[c4d.PY_TUBEOBJECT_IRADX]+val, op[c4d.PY_TUBEOBJECT_ROUNDRAD], op[c4d.PY_TUBEOBJECT_RAD])
    #     elif i is 2:
    #         op[c4d.PY_TUBEOBJECT_IRADY] = utils.FCut(op[c4d.PY_TUBEOBJECT_IRADY]+val, op[c4d.PY_TUBEOBJECT_ROUNDRAD], sys.maxint)
    #     elif i is 3 or i is 4:
    #         op[c4d.PY_TUBEOBJECT_ROUNDRAD] = utils.FCut(op[c4d.PY_TUBEOBJECT_ROUNDRAD]+val, 0.0, min(op[c4d.PY_TUBEOBJECT_IRADX], op[c4d.PY_TUBEOBJECT_IRADY]))


    # # Override method, draw additional stuff in the viewport (e.g. the handles).
    # def Draw(self, op, drawpass, bd, bh):
    #     if drawpass!=c4d.DRAWPASS_HANDLES: return c4d.DRAWRESULT_SKIP

    #     rad = op[c4d.PY_TUBEOBJECT_RAD]
    #     iradx = op[c4d.PY_TUBEOBJECT_IRADX]
    #     irady = op[c4d.PY_TUBEOBJECT_IRADY]
    #     axis = op[c4d.PRIM_AXIS]

    #     bd.SetPen(c4d.GetViewColor(c4d.VIEWCOLOR_ACTIVEPOINT))

    #     hitid = op.GetHighlightHandle(bd)
    #     bd.SetMatrix_Matrix(op, bh.GetMg())

    #     for i in xrange(self.HANDLECOUNT):
    #         if i==hitid:
    #             bd.SetPen(c4d.GetViewColor(c4d.VIEWCOLOR_SELECTION_PREVIEW))
    #         else:
    #             bd.SetPen(c4d.GetViewColor(c4d.VIEWCOLOR_ACTIVEPOINT))

    #         info = c4d.HandleInfo()
    #         self.GetHandle(op, i, info)
    #         bd.DrawHandle(info.position, c4d.DRAWHANDLE_BIG, 0)

    #         bd.SetPen(c4d.GetViewColor(c4d.VIEWCOLOR_ACTIVEPOINT))

    #         if i is 0:
    #             info2 = c4d.HandleInfo()
    #             self.GetHandle(op, 1, info2)
    #             bd.DrawLine(info.position, info2.position, 0)
    #             self.GetHandle(op, 2, info2)
    #             bd.DrawLine(info.position, info2.position, 0)
    #         elif i is 3:
    #             bd.DrawLine(info.position, RoundedTube.SwapPoint(c4d.Vector(rad+iradx, irady, 0.0), axis), 0)
    #         elif i is 4:
    #             bd.DrawLine(info.position, RoundedTube.SwapPoint(c4d.Vector(rad+iradx, irady, 0.0), axis), 0)

    #     return c4d.DRAWRESULT_OK


    # # Helper method to generate a lathe over points.
    # def GenerateLathe(self, cpadr, cpcnt, sub):
    #     op = tag = padr = vadr = None
    #     i = j = pcnt = vcnt = a = b = c = d = 0
    #     length = sn = cs = v1 = v2 = 0.0

    #     pcnt = cpcnt * sub
    #     vcnt = cpcnt * sub

    #     op = c4d.PolygonObject(pcnt, vcnt)
    #     if op is None: return None

    #     uvadr = [0.0]*(cpcnt+1)
    #     for i in xrange(cpcnt):
    #         uvadr[i] = length
    #         length += (cpadr[ (i+1)%cpcnt ] - cpadr[i] ).GetLength()

    #     if length > 0.0: length = 1.0/length
    #     for i in xrange(cpcnt):
    #         uvadr[i] *= length

    #     uvadr[cpcnt] = 1.0
    #     vcnt = 0
    #     for i in xrange(sub):
    #         sn, cs = utils.SinCos(math.pi*2 * float(i) / float(sub))
    #         v1 = float(i) / float(sub)
    #         v2 = float(i+1) / float(sub)
    #         for j in xrange(cpcnt):
    #             a = cpcnt*i+j
    #             op.SetPoint(a, c4d.Vector(cpadr[j].x*cs,cpadr[j].y,cpadr[j].x*sn))
    #             if i < sub:
    #                 b = cpcnt*i          +((j+1)%cpcnt)
    #                 c = cpcnt*((i+1)%sub)+((j+1)%cpcnt)
    #                 d = cpcnt*((i+1)%sub)+j
    #                 pol = c4d.CPolygon(a,b,c,d)
    #                 op.SetPolygon(vcnt, pol)
    #                 vcnt += 1

    #     op.Message(c4d.MSG_UPDATE)
    #     op.SetPhong(True, 1, utils.Rad(80.0))

    #     return op


    # # Override method, should return the bounding box of the generated object.
    # def GetDimension(self, op, mp, rad):
    #     rado = op[c4d.PY_TUBEOBJECT_RAD]
    #     if rado is None: return
    #     radx = op[c4d.PY_TUBEOBJECT_IRADX]
    #     if radx is None: return
    #     rady = op[c4d.PY_TUBEOBJECT_IRADY]
    #     if rady is None: return

    #     axis = op[c4d.PRIM_AXIS]
    #     if axis is None: return

    #     mp = 0.0
    #     if axis is c4d.PRIM_AXIS_XP or axis is c4d.PRIM_AXIS_XN:
    #         rad.x = rady
    #         rad.y = rado+radx
    #         rad.z = rado+radx
    #     elif axis is c4d.PRIM_AXIS_YP or axis is c4d.PRIM_AXIS_YN:
    #         rad.x = rado+radx
    #         rad.y = rady
    #         rad.z = rado+radx
    #     elif axis is c4d.PRIM_AXIS_ZP or axis is c4d.PRIM_AXIS_ZN:
    #         rad.x = rado+radx
    #         rad.y = rado+radx
    #         rad.z = rady


    # # Override method, should generate and return the object.
    # def GetVirtualObjects(self, op, hierarchyhelp):

    #     # Disabled the following lines because cache flag was set
    #     # So the cache build is done before this method is called
    #     #dirty = op.CheckCache(hierarchyhelp) or op.IsDirty(c4d.DIRTY_DATA)
    #     #if dirty is False: return op.GetCache(hierarchyhelp)

    #     rad = op[c4d.PY_TUBEOBJECT_RAD]
    #     if rad is None: rad = 200.0
    #     iradx = op[c4d.PY_TUBEOBJECT_IRADX]
    #     if iradx is None: iradx = 50.0
    #     irady = op[c4d.PY_TUBEOBJECT_IRADY]
    #     if irady is None: irady = 50.0
    #     rrad = op[c4d.PY_TUBEOBJECT_ROUNDRAD]
    #     if rrad is None: rrad = 10.0

    #     num_sub = op[c4d.PY_TUBEOBJECT_SUB]
    #     if num_sub is None: num_sub = 1
    #     sub = utils.CalcLOD(num_sub, 1, 1, 1000)

    #     num_rsub = op[c4d.PY_TUBEOBJECT_ROUNDSUB]
    #     if num_rsub is None: num_rsub = 8
    #     rsub = utils.CalcLOD(num_rsub, 1, 1, 1000)

    #     num_seg = op[c4d.PY_TUBEOBJECT_SEG]
    #     if num_seg is None: num_seg = 36
    #     seg = utils.CalcLOD(num_seg, 1, 3, 1000)

    #     i = 0
    #     sn = 0.0
    #     cs = 0.0

    #     cpcnt = 4*(sub+rsub)
    #     cpadr = [c4d.Vector()]*cpcnt

    #     for i in xrange(sub):
    #         cpadr[i]                 = c4d.Vector(rad-iradx, (1.0 - float(i)/sub*2.0)*(irady-rrad), 0.0)
    #         cpadr[i+sub+rsub]        = c4d.Vector(rad+(float(i)/sub*2.0-1.0)*(iradx-rrad), -irady, 0.0)
    #         cpadr[i+2*(sub+rsub)]    = c4d.Vector(rad+iradx, (float(i)/float(sub)*2.0-1.0)*(irady-rrad), 0.0)
    #         cpadr[i+3*(sub+rsub)]    = c4d.Vector(rad+(1.0-float(i)/float(sub)*2.0)*(iradx-rrad), irady, 0.0)

    #     pi05 = 1.570796326
    #     for i in xrange(rsub):
    #         sn, cs = utils.SinCos(float(i)/rsub*pi05)
    #         cpadr[i+sub]              = c4d.Vector(rad-(iradx-rrad+cs*rrad), -(irady-rrad+sn*rrad), 0.0)
    #         cpadr[i+sub+(sub+rsub)]   = c4d.Vector(rad+(iradx-rrad+sn*rrad), -(irady-rrad+cs*rrad), 0.0)
    #         cpadr[i+sub+2*(sub+rsub)] = c4d.Vector(rad+(iradx-rrad+cs*rrad), +(irady-rrad+sn*rrad), 0.0)
    #         cpadr[i+sub+3*(sub+rsub)] = c4d.Vector(rad-(iradx-rrad+sn*rrad), +(irady-rrad+cs*rrad), 0.0)

    #     ret = self.GenerateLathe(cpadr, cpcnt, seg)
    #     if ret is None: return None

    #     axis = op[c4d.PRIM_AXIS]
    #     if axis is None: return None

    #     RoundedTube.SetAxis(ret, axis)
    #     ret.SetName(op.GetName())

    #     return ret


# This code is called at the startup, it register the class RoundedTube as a plugin to be used later in Cinema 4D. It have to be done only once.
if __name__ == "__main__":
    disr, file = os.path.split(__file__)

    icon = bitmaps.BaseBitmap()
    icon.InitWith(os.path.join(disr, "res", "oroundedtube.tif"))
    # Register the class RoundedTube as a Object Plugin to be used later in Cinema 4D.
    plugins.RegisterObjectPlugin(id=PLUGIN_ID, str="Import glTF", g=ImportGLTF, icon=icon,
                                description="roundedtube2", info=c4d.OBJECT_GENERATOR)
