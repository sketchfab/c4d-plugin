def getd():
    mat = doc.GetMaterials()[0]
    red = mat.GetReflectionLayerIndex(0).GetDataID()
    dif = mat.GetReflectionLayerIndex(1).GetDataID()
    return red, dif


def makecolorizer(filepath):
    colorizer = c4d.BaseShader(c4d.Xcolorizer)
    sha = c4d.BaseList2D(c4d.Xbitmap)
    sha[c4d.BITMAPSHADER_FILENAME] = filepath
    colorizer.SetParameter(c4d.SLA_COLORIZER_TEXTURE, sha, c4d.DESCFLAGS_SET_NONE)
    colorizer.InsertShader(sha)
    return colorizer

def getmrtexpath():
    return os.path.join(os.path.join(os.path.split(doc.GetParameter(c4d.DOCUMENT_FILEPATH, c4d.DESCFLAGS_GET_NONE))[0], 'tex'), 'mr.png')