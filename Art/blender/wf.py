"""Wakefire Blender kit: build low-poly, vertex-coloured, rigidly skinned models (the way 32-bit
era characters were built), rig them, key animations in body axes and export FBX for Unity.

Conventions: metres, Z up, characters face -Y. Body axes for animation:
  +X rotation on a bone hanging DOWN (legs, arms)  -> swings it BACK   (use -X to swing forward)
  +X rotation on a bone pointing UP (spine, neck)  -> leans it FORWARD
  +Y rotation on the right arm (at -X)             -> raises it out sideways (left arm: -Y)
  +Z rotation                                       -> turns to the character's left (yaw)
Vertex colour alpha = material: 1 matte, 0.6 metal (bronze highlights), 0 emissive (fire).
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler, Quaternion

D2R = math.pi / 180.0


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.fps = 30
    s.unit_settings.system = 'METRIC'
    s.unit_settings.scale_length = 1.0


def hexc(h, a=1.0):
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0, a)


METAL = 0.6
GLOW = 0.0


class Builder:
    """Accumulates parts into one mesh: vertices, faces with colour, smooth flag and bone group."""

    def __init__(self):
        self.v = []
        self.f = []  # (indices, rgba, smooth, group)

    # ---------------------------------------------------------------- primitives
    def _add(self, verts, faces, color, smooth, group, xf=None):
        base = len(self.v)
        for p in verts:
            p = Vector(p)
            if xf is not None:
                p = xf @ p
            self.v.append(p)
        for f in faces:
            self.f.append(([base + i for i in f], color, smooth, group))
        return base

    def loft(self, rings, seg=10, color=(1, 1, 1, 1), smooth=True, group='root', cap0=True, cap1=True,
             arc=(0.0, 360.0), xf=None, double=False, color_in=None):
        """rings: list of (center Vector, rx, ry) in the XY plane at each centre's z (local frame).
        arc: degrees of the ring to build (open sheets for capes); 0 deg points to -Y (front)."""
        full = abs(arc[1] - arc[0]) >= 359.9
        n = seg if full else seg + 1
        verts = []
        for (c, rx, ry) in rings:
            c = Vector(c)
            for k in range(n):
                t = arc[0] + (arc[1] - arc[0]) * (k / seg)
                a = t * D2R
                verts.append((c.x + math.sin(a) * rx, c.y - math.cos(a) * ry, c.z))
        faces = []
        for r in range(len(rings) - 1):
            for k in range(seg):
                a0 = r * n + k
                a1 = r * n + (k + 1) % n
                b0 = (r + 1) * n + k
                b1 = (r + 1) * n + (k + 1) % n
                faces.append((a0, a1, b1, b0))
        if full:
            if cap0:
                faces.append(tuple(reversed(range(0, n))))
            if cap1:
                last = (len(rings) - 1) * n
                faces.append(tuple(range(last, last + n)))
        base = self._add(verts, faces, color, smooth, group, xf)
        if double:
            inner = [(tuple(reversed(f))) for f in faces]
            for f in inner:
                self.f.append(([base + i for i in f], color_in or color, smooth, group))
        return base

    def limb(self, p0, p1, radii, seg=8, color=(1, 1, 1, 1), smooth=True, group='root', squash=1.0):
        """Tapered tube from p0 to p1; radii = list of radius at evenly spaced stations."""
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        z = d.normalized()
        up = Vector((0, 1, 0)) if abs(z.y) < 0.9 else Vector((1, 0, 0))
        x = up.cross(z).normalized()
        y = z.cross(x).normalized()
        M = Matrix((x, y, z)).transposed().to_4x4()
        M.translation = p0
        rings = []
        for i, r in enumerate(radii):
            t = i / (len(radii) - 1)
            rings.append(((0, 0, L * t), r, r * squash))
        return self.loft(rings, seg, color, smooth, group, xf=M)

    def ellipsoid(self, c, r, seg=10, rings=7, color=(1, 1, 1, 1), smooth=True, group='root', xf=None):
        c = Vector(c)
        verts = [(c.x, c.y, c.z - r[2])]
        for i in range(1, rings):
            phi = math.pi * i / rings
            z = -math.cos(phi)
            s = math.sin(phi)
            for k in range(seg):
                a = 2 * math.pi * k / seg
                verts.append((c.x + math.sin(a) * s * r[0], c.y - math.cos(a) * s * r[1], c.z + z * r[2]))
        verts.append((c.x, c.y, c.z + r[2]))
        top = len(verts) - 1
        faces = []
        for k in range(seg):
            faces.append((0, 1 + (k + 1) % seg, 1 + k))
        for i in range(rings - 2):
            for k in range(seg):
                a0 = 1 + i * seg + k
                a1 = 1 + i * seg + (k + 1) % seg
                b0 = 1 + (i + 1) * seg + k
                b1 = 1 + (i + 1) * seg + (k + 1) % seg
                faces.append((a0, a1, b1, b0))
        lastring = 1 + (rings - 2) * seg
        for k in range(seg):
            faces.append((lastring + k, lastring + (k + 1) % seg, top))
        return self._add(verts, faces, color, smooth, group, xf)

    def box(self, c, size, color=(1, 1, 1, 1), group='root', rot=(0, 0, 0), smooth=False, taper=1.0):
        """Axis box (optionally rotated, degrees XYZ); taper scales the top face."""
        sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        t = taper
        verts = [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
                 (-sx * t, -sy * t, sz), (sx * t, -sy * t, sz), (sx * t, sy * t, sz), (-sx * t, sy * t, sz)]
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        M = Euler((rot[0] * D2R, rot[1] * D2R, rot[2] * D2R), 'XYZ').to_matrix().to_4x4()
        M.translation = Vector(c)
        return self._add(verts, faces, color, smooth, group, M)

    def prism(self, pts, thickness, M, color=(1, 1, 1, 1), group='root', smooth=False, color_edge=None):
        """Extrude a 2D polygon (u, v) along local Z by thickness, placed with matrix M."""
        n = len(pts)
        h = thickness / 2
        verts = [(u, v, -h) for (u, v) in pts] + [(u, v, h) for (u, v) in pts]
        faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
        side = []
        for i in range(n):
            j = (i + 1) % n
            side.append((i, j, n + j, n + i))
        base = self._add(verts, faces, color, smooth, group, M)
        for f in side:
            self.f.append(([base + k for k in f], color_edge or color, smooth, group))
        return base

    # ---------------------------------------------------------------- output
    def mesh_object(self, name):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        bv = [bm.verts.new(p) for p in self.v]
        groups = {}
        face_meta = []
        for (idx, col, smooth, grp) in self.f:
            try:
                f = bm.faces.new([bv[i] for i in idx])
            except ValueError:
                continue
            f.smooth = smooth
            face_meta.append((f, col, grp))
        bm.normal_update()
        cl = bm.loops.layers.color.new("Col")
        for (f, col, grp) in face_meta:
            for loop in f.loops:
                loop[cl] = col
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        # vertex groups: each vertex goes to the bone of the face that used it
        vg_of = {}
        for (idx, col, smooth, grp) in self.f:
            for i in idx:
                vg_of.setdefault(i, grp)
        for i, g in vg_of.items():
            groups.setdefault(g, []).append(i)
        for g, idx in groups.items():
            vg = ob.vertex_groups.new(name=g)
            vg.add(idx, 1.0, 'REPLACE')
        for p in me.polygons:
            pass
        return ob


def armature(name, bones):
    """bones: list of (name, head, tail, parent or None)."""
    arm = bpy.data.armatures.new(name)
    ao = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ao)
    bpy.context.view_layer.objects.active = ao
    bpy.ops.object.mode_set(mode='EDIT')
    eb = {}
    for (n, h, t, p) in bones:
        b = arm.edit_bones.new(n)
        b.head = Vector(h)
        b.tail = Vector(t)
        b.roll = 0
        if p:
            b.parent = eb[p]
        eb[n] = b
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in ao.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    return ao


def bind(mesh_ob, arm_ob):
    mesh_ob.parent = arm_ob
    m = mesh_ob.modifiers.new("Armature", 'ARMATURE')
    m.object = arm_ob


class Anim:
    """Keys in body axes: key(frame, bone=(x, y, z) degrees, ..., loc={bone: (x, y, z)}).
    Bones not mentioned at a key hold rest pose there."""

    def __init__(self, name, length, loop=False):
        self.name = name
        self.length = length
        self.loop = loop
        self.keys = []  # (frame, {bone: euler}, {bone: loc})

    def key(self, frame, loc=None, **rot):
        rot = {k.replace('_L', '.L').replace('_R', '.R'): v for k, v in rot.items()}
        loc = {k.replace('_L', '.L').replace('_R', '.R'): v for k, v in (loc or {}).items()}
        self.keys.append((frame, rot, loc))
        return self

    def mirrored(self, frame_offset, src_frames):
        """Append mirrored copies (left/right swapped) of earlier keys, shifted in time."""
        out = []
        for (f, rot, loc) in self.keys:
            if f not in src_frames:
                continue
            r2 = {}
            for b, (x, y, z) in rot.items():
                b2 = b.replace('.L', '.TMP').replace('.R', '.L').replace('.TMP', '.R')
                r2[b2] = (x, -y, -z)
            l2 = {}
            for b, (x, y, z) in loc.items():
                b2 = b.replace('.L', '.TMP').replace('.R', '.L').replace('.TMP', '.R')
                l2[b2] = (-x, y, z)
            out.append((f + frame_offset, r2, l2))
        self.keys.extend(out)
        return self


def apply_anims(ao, anims, interpolation='BEZIER'):
    ao.animation_data_create()
    bones = [pb.name for pb in ao.pose.bones]
    rest = {pb.name: pb.bone.matrix_local.to_3x3() for pb in ao.pose.bones}
    for A in anims:
        act = bpy.data.actions.new(A.name)
        act.use_fake_user = True
        ao.animation_data.action = act
        keys = sorted(A.keys, key=lambda k: k[0])
        prevq = {}
        if A.loop and keys and keys[-1][0] != A.length:
            f0, r0, l0 = keys[0]
            keys.append((A.length, r0, l0))
        for (frame, rot, loc) in keys:
            for b in bones:
                pb = ao.pose.bones[b]
                R0 = rest[b]
                e = rot.get(b, (0, 0, 0))
                Q = Euler((e[0] * D2R, e[1] * D2R, e[2] * D2R), 'XYZ').to_matrix()
                local = (R0.inverted() @ Q @ R0).to_quaternion()
                if b in prevq and prevq[b].dot(local) < 0:
                    local = -local
                prevq[b] = local.copy()
                pb.rotation_quaternion = local
                pb.keyframe_insert('rotation_quaternion', frame=frame)
                lv = Vector(loc.get(b, (0, 0, 0)))
                pb.location = R0.inverted() @ lv
                pb.keyframe_insert('location', frame=frame)
        # interpolation
        try:
            fcs = act.fcurves
        except AttributeError:
            fcs = []
            for layer in act.layers:
                for strip in layer.strips:
                    for cb in strip.channelbags:
                        fcs.extend(cb.fcurves)
        for fc in fcs:
            for kp in fc.keyframe_points:
                kp.interpolation = interpolation
    ao.animation_data.action = None
    for pb in ao.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)


def export_fbx(path, objects=None):
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=False,
        object_types={'ARMATURE', 'MESH'},
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z', axis_up='Y',
        add_leaf_bones=False,
        primary_bone_axis='Y', secondary_bone_axis='X',
        use_armature_deform_only=False,
        bake_anim=True,
        bake_anim_use_all_actions=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_bones=True,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0,
        mesh_smooth_type='OFF',
        colors_type='SRGB',
        use_mesh_modifiers=False,
    )


def check_render(path, size=320, angle=(48, 0, 30), frame=None, action=None, ao=None, dist=4.5, target=(0, 0, 0.9)):
    """Quick Cycles render of the scene with vertex colours, for checking shapes."""
    s = bpy.context.scene
    s.render.engine = 'CYCLES'
    s.cycles.samples = 16
    s.cycles.device = 'CPU'
    s.render.resolution_x = size
    s.render.resolution_y = size
    s.render.film_transparent = False
    if s.world is None:
        s.world = bpy.data.worlds.new("W")
    s.world.use_nodes = True
    bg = s.world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = (0.08, 0.08, 0.12, 1)
    bg.inputs[1].default_value = 1.0
    mat = bpy.data.materials.get("VC") or bpy.data.materials.new("VC")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    attr = nt.nodes.new('ShaderNodeVertexColor')
    attr.layer_name = "Col"
    nt.links.new(attr.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    for ob in s.objects:
        if ob.type == 'MESH':
            ob.data.materials.clear()
            ob.data.materials.append(mat)
    cam = bpy.data.objects.get("CheckCam")
    if not cam:
        cam = bpy.data.objects.new("CheckCam", bpy.data.cameras.new("CheckCam"))
        s.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = dist / 2.2
    tgt = Vector(target)
    el, _, az = angle
    d = Vector((math.sin(az * D2R) * math.cos(el * D2R), -math.cos(az * D2R) * math.cos(el * D2R), math.sin(el * D2R)))
    cam.location = tgt + d * 10
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    s.camera = cam
    sun = bpy.data.objects.get("CheckSun")
    if not sun:
        sun = bpy.data.objects.new("CheckSun", bpy.data.lights.new("CheckSun", 'SUN'))
        s.collection.objects.link(sun)
    sun.data.energy = 3.5
    sun.rotation_euler = (40 * D2R, 10 * D2R, 30 * D2R)
    if ao is not None and action is not None:
        ao.animation_data.action = bpy.data.actions[action]
    if frame is not None:
        s.frame_set(frame)
    s.render.filepath = path
    bpy.ops.render.render(write_still=True)
