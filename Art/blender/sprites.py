"""Turn a rigged Blender character into pixel-art sprite sheets.

Each frame is rendered at its exact pixel size with no anti-aliasing: flat vertex colours,
three hue-shifted light bands from the upper left, bronze glints and unshaded fire. A second
render stores part ids and depth, so post-processing can draw the dark silhouette outline and
the inner contour lines a pixel artist would draw (arm over chest, blade over body...).
"""
import os
import sys
import json
import math
import bpy
import numpy as np
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wf

PX_PER_M = 16.0
ELEV = 30.0
LIGHT_CAM = Vector((-0.55, 0.68, 0.48)).normalized()   # camera space: right, up, towards viewer


def part_ids(mesh_ob):
    """Store each vertex's bone group index as a 'pid' attribute (1..n)."""
    me = mesh_ob.data
    names = [g.name for g in mesh_ob.vertex_groups]
    vals = np.zeros(len(me.vertices), dtype=np.float32)
    for v in me.vertices:
        if v.groups:
            vals[v.index] = v.groups[0].group + 1
    attr = me.attributes.get("pid") or me.attributes.new("pid", 'FLOAT', 'POINT')
    attr.data.foreach_set("value", vals)
    return names


def toon_material(light_world):
    m = bpy.data.materials.new("Toon")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    out = N('ShaderNodeOutputMaterial')
    emit = N('ShaderNodeEmission')
    vc = N('ShaderNodeVertexColor'); vc.layer_name = "Col"
    geo = N('ShaderNodeNewGeometry')
    L = N('ShaderNodeCombineXYZ')
    L.inputs[0].default_value, L.inputs[1].default_value, L.inputs[2].default_value = light_world
    dot = N('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    nt.links.new(geo.outputs['Normal'], dot.inputs[0]); nt.links.new(L.outputs[0], dot.inputs[1])
    ramp = N('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.interpolation = 'CONSTANT'
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.62, 0.58, 0.78, 1)        # shadow, pushed towards violet
    cr.elements[1].position = 0.56
    cr.elements[1].color = (1.06, 1.02, 0.92, 1)         # lit, slightly warm
    e = cr.elements.new(0.40)
    e.color = (0.86, 0.84, 0.90, 1)                     # mid tone
    remap = N('ShaderNodeMapRange')
    remap.inputs['From Min'].default_value = -1.0
    remap.inputs['From Max'].default_value = 1.0
    nt.links.new(dot.outputs['Value'], remap.inputs['Value'])
    nt.links.new(remap.outputs['Result'], ramp.inputs['Fac'])
    mul = N('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    nt.links.new(vc.outputs['Color'], mul.inputs[6]); nt.links.new(ramp.outputs['Color'], mul.inputs[7])
    # bronze glint: metal (alpha ~0.6) facing the light gets a bright band
    a_lo = N('ShaderNodeMath'); a_lo.operation = 'GREATER_THAN'; a_lo.inputs[1].default_value = 0.4
    a_hi = N('ShaderNodeMath'); a_hi.operation = 'LESS_THAN'; a_hi.inputs[1].default_value = 0.8
    nt.links.new(vc.outputs['Alpha'], a_lo.inputs[0]); nt.links.new(vc.outputs['Alpha'], a_hi.inputs[0])
    is_metal = N('ShaderNodeMath'); is_metal.operation = 'MULTIPLY'
    nt.links.new(a_lo.outputs[0], is_metal.inputs[0]); nt.links.new(a_hi.outputs[0], is_metal.inputs[1])
    facing = N('ShaderNodeMath'); facing.operation = 'GREATER_THAN'; facing.inputs[1].default_value = 0.78
    nt.links.new(dot.outputs['Value'], facing.inputs[0])
    glint = N('ShaderNodeMath'); glint.operation = 'MULTIPLY'
    nt.links.new(is_metal.outputs[0], glint.inputs[0]); nt.links.new(facing.outputs[0], glint.inputs[1])
    bright = N('ShaderNodeMix'); bright.data_type = 'RGBA'; bright.blend_type = 'SCREEN'
    nt.links.new(glint.outputs[0], bright.inputs['Factor'])
    nt.links.new(mul.outputs[2], bright.inputs[6])
    bright.inputs[7].default_value = (0.55, 0.45, 0.25, 1)
    # fire and glass (alpha ~0) are not shaded
    is_glow = N('ShaderNodeMath'); is_glow.operation = 'LESS_THAN'; is_glow.inputs[1].default_value = 0.15
    nt.links.new(vc.outputs['Alpha'], is_glow.inputs[0])
    glow = N('ShaderNodeMix'); glow.data_type = 'RGBA'; glow.blend_type = 'MIX'
    nt.links.new(is_glow.outputs[0], glow.inputs['Factor'])
    nt.links.new(bright.outputs[2], glow.inputs[6]); nt.links.new(vc.outputs['Color'], glow.inputs[7])
    nt.links.new(glow.outputs[2], emit.inputs['Color'])
    emit.inputs['Strength'].default_value = 1.0
    nt.links.new(emit.outputs[0], out.inputs['Surface'])
    return m


def id_material(dmin, dmax):
    m = bpy.data.materials.new("Ids")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N = nt.nodes.new
    out = N('ShaderNodeOutputMaterial')
    emit = N('ShaderNodeEmission')
    pid = N('ShaderNodeAttribute'); pid.attribute_name = "pid"; pid.attribute_type = 'GEOMETRY'
    scale = N('ShaderNodeMath'); scale.operation = 'DIVIDE'; scale.inputs[1].default_value = 255.0
    nt.links.new(pid.outputs['Fac'], scale.inputs[0])
    cam = N('ShaderNodeCameraData')
    rng = N('ShaderNodeMapRange')
    rng.inputs['From Min'].default_value = dmin
    rng.inputs['From Max'].default_value = dmax
    nt.links.new(cam.outputs['View Z Depth'], rng.inputs['Value'])
    comb = N('ShaderNodeCombineColor')
    nt.links.new(scale.outputs[0], comb.inputs[0]); nt.links.new(rng.outputs['Result'], comb.inputs[1])
    nt.links.new(comb.outputs[0], emit.inputs['Color'])
    nt.links.new(emit.outputs[0], out.inputs['Surface'])
    return m


class SpriteRig:
    def __init__(self, ao, meshes, size=48, target=(0, 0, 0.9), px_per_m=PX_PER_M, elev=ELEV, scales=None, dist=10.0):
        self.ao = ao
        self.meshes = meshes
        self.size = size
        self.target = Vector(target)
        s = bpy.context.scene
        s.render.engine = 'CYCLES'
        s.cycles.device = 'CPU'
        s.cycles.samples = 1
        s.cycles.use_denoising = False
        s.cycles.pixel_filter_type = 'BOX'
        s.cycles.filter_width = 0.01
        s.cycles.max_bounces = 0
        s.render.resolution_x = size
        s.render.resolution_y = size
        s.render.resolution_percentage = 100
        s.render.film_transparent = True
        s.render.image_settings.file_format = 'PNG'
        s.render.image_settings.color_mode = 'RGBA'
        s.render.image_settings.color_depth = '8'
        s.render.dither_intensity = 0.0
        if s.world is None:
            s.world = bpy.data.worlds.new("W")
        cam = bpy.data.objects.new("SpriteCam", bpy.data.cameras.new("SpriteCam"))
        s.collection.objects.link(cam)
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = size / px_per_m
        el = elev * wf.D2R
        cam.location = self.target + Vector((0, -math.cos(el), math.sin(el))) * dist
        cam.rotation_euler = (Vector((0, math.cos(el), -math.sin(el)))).to_track_quat('-Z', 'Y').to_euler()
        cam.data.clip_start = dist * 0.5
        cam.data.clip_end = dist * 1.5
        s.camera = cam
        self.cam = cam
        R = cam.matrix_world.to_3x3()
        lw = (R @ LIGHT_CAM).normalized()
        self.toon = toon_material(tuple(lw))
        self.ids = id_material(dist * 0.75, dist * 1.25)
        for mo in meshes:
            part_ids(mo)
        for pb in ao.pose.bones:
            pb.scale = (1, 1, 1)
        for b, k in (scales or {}).items():
            if b in ao.pose.bones:
                ao.pose.bones[b].scale = (k, k, k)
                for c in ao.data.bones[b].children:
                    c.inherit_scale = 'NONE' if c.name.startswith(('hand', 'foot')) else c.inherit_scale

    def _assign(self, mat):
        for mo in self.meshes:
            mo.data.materials.clear()
            mo.data.materials.append(mat)

    def pivot(self):
        """Pixel position of the character's root (feet) in the frame, from the top-left."""
        s = bpy.context.scene
        p = world_to_camera_view(s, self.cam, self.ao.matrix_world.translation)
        return (p.x * self.size, (1 - p.y) * self.size)

    def render(self, action, frame, yaw_deg, path_color, path_ids):
        s = bpy.context.scene
        self.ao.rotation_euler = (0, 0, yaw_deg * wf.D2R)
        self.ao.animation_data.action = bpy.data.actions[action] if action else None
        if action:
            act = bpy.data.actions[action]
            slots = getattr(act, 'slots', None)
            if slots and len(slots):
                try:
                    self.ao.animation_data.action_slot = slots[0]
                except Exception:
                    pass
        s.frame_set(int(frame))
        s.view_settings.view_transform = 'Standard'
        s.view_settings.look = 'None'
        self._assign(self.toon)
        s.render.filepath = path_color
        bpy.ops.render.render(write_still=True)
        s.view_settings.view_transform = 'Raw'
        self._assign(self.ids)
        s.render.filepath = path_ids
        bpy.ops.render.render(write_still=True)


# ------------------------------------------------------------------ post-processing (numpy)
OUTLINE = np.array([20, 12, 26], dtype=np.uint8)


def outline(color_png, ids_png, inner=True):
    from PIL import Image
    c = np.array(Image.open(color_png).convert('RGBA'))
    d = np.array(Image.open(ids_png).convert('RGBA'))
    alpha = c[:, :, 3] > 127
    c[~alpha] = 0
    c[alpha, 3] = 255
    pid = d[:, :, 0].astype(np.int32)
    depth = d[:, :, 1].astype(np.int32)
    H, W = alpha.shape
    out = c.copy()
    edge = np.zeros_like(alpha)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sa = np.zeros_like(alpha)
        ys = slice(max(dy, 0), H + min(dy, 0)); yd = slice(max(-dy, 0), H + min(-dy, 0))
        xs = slice(max(dx, 0), W + min(dx, 0)); xd = slice(max(-dx, 0), W + min(-dx, 0))
        sa[yd, xd] = alpha[ys, xs]
        edge |= alpha & ~sa
        if inner:
            sp = np.zeros_like(pid); sp[yd, xd] = pid[ys, xs]
            sd = np.zeros_like(depth); sd[yd, xd] = depth[ys, xs]
            # this pixel belongs to a part that sits in front of a different part
            front = alpha & sa & (sp != pid) & (sd > depth + 14)
            edge |= front
    out[edge, 0:3] = OUTLINE
    # tidy: lone pixels that disagree with every neighbour take the majority colour
    rgb = out[:, :, 0:3].astype(np.int32)
    key = rgb[:, :, 0] * 65536 + rgb[:, :, 1] * 256 + rgb[:, :, 2]
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if not alpha[y, x] or edge[y, x]:
                continue
            nb = [key[y + a, x + b] for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if alpha[y + a, x + b]]
            if len(nb) == 4 and all(n != key[y, x] for n in nb):
                vals, counts = np.unique(nb, return_counts=True)
                if counts.max() >= 3:
                    k = vals[counts.argmax()]
                    out[y, x, 0:3] = (k >> 16, (k >> 8) & 255, k & 255)
    return out
