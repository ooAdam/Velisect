"""Tile PNGs into one sheet in a headless Blender: VS_GRID="out.png|cols|a.png|b.png|..." node tools/unreal.mjs blender tools/pipeline/tile.py"""
import bpy, os, numpy as np
spec = os.environ["VS_GRID"].split("|")
out, cols, paths = spec[0], int(spec[1]), spec[2:]
imgs = [bpy.data.images.load(p) for p in paths]
w, h = imgs[0].size; rows = (len(imgs) + cols - 1) // cols
canvas = np.zeros((rows * h, cols * w, 4), np.float32)
for i, im in enumerate(imgs):
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px)
    r, c = divmod(i, cols)
    canvas[(rows - 1 - r) * h:(rows - r) * h, c * w:(c + 1) * w] = px.reshape(h, w, 4)
img = bpy.data.images.new("sheet", cols * w, rows * h, alpha=True)
img.pixels.foreach_set(canvas.ravel()); img.filepath_raw = out; img.file_format = 'PNG'; img.save()
