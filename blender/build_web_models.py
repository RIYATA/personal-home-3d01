import math
import os

import bpy
from mathutils import Vector


ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
MODEL_DIR = os.path.join(PROJECT_ROOT, "public", "models")
BLEND_PATH = os.path.join(ROOT, "snowline_web_models.blend")
PREVIEW_PATH = os.path.join(ROOT, "snowline_web_models_preview.png")
WIZARD_PREVIEW_PATH = os.path.join(ROOT, "wizard_climber_preview.png")

ROUTE_POINTS = [
    (-5.8, -1.1, 0.4),
    (-4.4, 0.15, -0.55),
    (-3.1, 1.25, -0.95),
    (-1.85, 2.25, -0.72),
    (-0.72, 3.4, -0.95),
    (0.25, 4.72, -0.5),
]

CABLE_POINTS = [
    (0.25, 4.72, -0.5),
    (1.8, 4.98, -1.35),
    (3.55, 4.1, -2.15),
    (4.82, 3.08, -2.92),
]

MEADOW_CENTER = (5.05, 2.36, -1.3)
CAMP_POS = (4.7, -1.08, 3.4)


def p(x, y, z):
    """Map Three.js coordinates (Y up) to Blender coordinates (Z up)."""
    return (x, -z, y)


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
        bpy.data.collections,
    ):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def collection(name):
    result = bpy.data.collections.get(name)
    if result is None:
        result = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(result)
    return result


def move_to_collection(obj, target):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    target.objects.link(obj)
    return obj


def material(name, color, roughness=0.82, metallic=0.0, emission=None, alpha=1.0):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat

    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, alpha)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, alpha)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.blend_method = "BLEND"
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 1.6
    return mat


def assign(obj, mat):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    return obj


def shade_flat(obj):
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = False
    return obj


def triangulate(obj):
    if obj.type != "MESH":
        return obj
    mod = obj.modifiers.new("LowPoly_Triangulate", "TRIANGULATE")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)
    return obj


def empty(name, location, target):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_size = 0.18
    obj.location = location
    target.objects.link(obj)
    return obj


def parent(child, root):
    child.parent = root
    child.matrix_parent_inverse = root.matrix_world.inverted()
    return child


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return obj


def cube(name, location, scale, mat, target, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    shade_flat(obj)
    triangulate(obj)
    return move_to_collection(obj, target)


def cylinder(name, location, radius, depth, vertices, mat, target, rotation=(0, 0, 0), fill="NGON"):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location,
        rotation=rotation,
        end_fill_type=fill,
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    shade_flat(obj)
    triangulate(obj)
    return move_to_collection(obj, target)


def cone(name, location, radius1, radius2, depth, vertices, mat, target, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    shade_flat(obj)
    triangulate(obj)
    return move_to_collection(obj, target)


def sphere(name, location, radius, mat, target, scale=(1, 1, 1), subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=subdivisions,
        radius=radius,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    shade_flat(obj)
    return move_to_collection(obj, target)


def torus(name, location, major_radius, minor_radius, mat, target, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=16,
        minor_segments=4,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    shade_flat(obj)
    triangulate(obj)
    return move_to_collection(obj, target)


def cylinder_between(name, start, end, radius, mat, target, vertices=8):
    a = Vector(start)
    b = Vector(end)
    mid = (a + b) * 0.5
    direction = b - a
    length = direction.length
    if length < 0.0001:
        return None
    rotation = direction.to_track_quat("Z", "Y").to_euler()
    return cylinder(name, mid, radius, length, vertices, mat, target, rotation=rotation)


def create_star(name, location, mat, target, scale=1.0):
    root = empty(name, location, target)
    for index, rot in enumerate((0, math.pi / 2)):
        arm = cube(
            f"{name}_Spark_{index}",
            (0, 0, 0),
            (0.025 * scale, 0.025 * scale, 0.12 * scale),
            mat,
            target,
            rotation=(0, rot, math.pi / 4),
        )
        parent(arm, root)
    return root


def create_crescent(name, center, mat, target, scale=1.0):
    location = Vector(center)
    outer = []
    inner = []
    for step in range(12):
        angle = math.radians(112 + step * 19)
        outer.append((math.cos(angle) * 0.13 * scale, math.sin(angle) * 0.13 * scale))
    for step in range(11, -1, -1):
        angle = math.radians(112 + step * 19)
        inner.append((0.055 * scale + math.cos(angle) * 0.09 * scale, math.sin(angle) * 0.09 * scale))
    outline = outer + inner
    depth = 0.014 * scale
    verts = []
    for y_offset in (-depth, depth):
        for x, z in outline:
            verts.append((location.x + x, location.y + y_offset, location.z + z))

    count = len(outline)
    faces = [tuple(range(count)), tuple(range(count, count * 2))]
    for index in range(count):
        faces.append((index, (index + 1) % count, count + (index + 1) % count, count + index))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = False
    target.objects.link(obj)
    return obj


def create_five_point_star(name, center, mat, target, scale=1.0):
    location = Vector(center)
    points = []
    for index in range(10):
        radius = 0.16 * scale if index % 2 == 0 else 0.07 * scale
        angle = math.radians(90 + index * 36)
        points.append((math.cos(angle) * radius, math.sin(angle) * radius))

    depth = 0.018 * scale
    verts = []
    for y_offset in (-depth, depth):
        for x, z in points:
            verts.append((location.x + x, location.y + y_offset, location.z + z))

    count = len(points)
    faces = [tuple(range(count)), tuple(range(count, count * 2))]
    for index in range(count):
        faces.append((index, (index + 1) % count, count + (index + 1) % count, count + index))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = False
    target.objects.link(obj)
    return obj


def create_cloud(name, center, target, mat_cloud, mat_shadow, scale=1.0):
    root = empty(name, p(*center), target)
    pieces = [
        (-0.55, 0.0, -0.03, 0.36),
        (-0.18, 0.04, 0.06, 0.48),
        (0.2, 0.02, 0.04, 0.42),
        (0.56, -0.02, -0.02, 0.34),
        (0.03, -0.05, -0.22, 0.33),
    ]
    for index, (x, z, y, radius) in enumerate(pieces):
        mat = mat_shadow if index in (3, 4) else mat_cloud
        part = sphere(
            f"{name}_Piece_{index}",
            p(center[0] + x * scale, center[1] + y * scale, center[2] + z * scale),
            radius * scale,
            mat,
            target,
            scale=(1.25, 0.78, 0.75),
            subdivisions=2,
        )
        parent(part, root)
    return root


def create_peak(name, position, scale, mat_body, mat_side, mat_snow, target):
    root = empty(name, p(*position), target)
    segment_count = 10
    ring_specs = [
        (2.9 * scale[0], 2.35 * scale[2], 0.0 * scale[1], 0.0),
        (2.05 * scale[0], 1.56 * scale[2], 2.05 * scale[1], 0.18),
        (1.12 * scale[0], 0.84 * scale[2], 4.08 * scale[1], -0.08),
    ]
    jitters = [0.08, -0.05, 0.03, -0.08, 0.11, -0.02, 0.07, -0.06, 0.04, -0.03]
    verts = []
    for radius_x, radius_z, height, offset in ring_specs:
        for index in range(segment_count):
            angle = (index / segment_count) * math.tau + offset
            jitter = 1 + jitters[index]
            verts.append(
                p(
                    position[0] + math.cos(angle) * radius_x * jitter,
                    position[1] + height,
                    position[2] + math.sin(angle) * radius_z * (1 - jitters[-index - 1] * 0.45),
                )
            )

    apex_index = len(verts)
    verts.append(p(position[0] + 0.08 * scale[0], position[1] + 6.34 * scale[1], position[2] - 0.06 * scale[2]))
    bottom_index = len(verts)
    verts.append(p(position[0], position[1] - 0.04 * scale[1], position[2]))

    faces = []
    for ring in range(len(ring_specs) - 1):
        current = ring * segment_count
        next_ring = (ring + 1) * segment_count
        for index in range(segment_count):
            a = current + index
            b = current + (index + 1) % segment_count
            c = next_ring + index
            d = next_ring + (index + 1) % segment_count
            faces.append((a, b, c))
            faces.append((c, b, d))

    top = (len(ring_specs) - 1) * segment_count
    for index in range(segment_count):
        faces.append((top + index, top + (index + 1) % segment_count, apex_index))
        faces.append((bottom_index, (index + 1) % segment_count, index))

    mesh = bpy.data.meshes.new(f"{name}_BodyMesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    body = bpy.data.objects.new(f"{name}_FacetedBody", mesh)
    body.data.materials.append(mat_body)
    body.data.materials.append(mat_side)
    body.data.materials.append(mat_snow)
    for index, polygon in enumerate(body.data.polygons):
        polygon.use_smooth = False
        if index % 6 == 2:
            polygon.material_index = 1
        if index >= len(faces) - segment_count * 2 and index % 3 == 0:
            polygon.material_index = 2
    target.objects.link(body)
    parent(body, root)
    return root


def create_flower(name, center, color_mat, target, scale=1.0):
    root = empty(name, p(*center), target)
    stem = cylinder(
        f"{name}_Stem",
        p(center[0], center[1] + 0.16 * scale, center[2]),
        0.014 * scale,
        0.32 * scale,
        5,
        mats["grass_dark"],
        target,
    )
    parent(stem, root)
    for index, (dx, dz) in enumerate(((0.06, 0), (-0.06, 0), (0, 0.06), (0, -0.06), (0, 0))):
        petal = sphere(
            f"{name}_Petal_{index}",
            p(center[0] + dx * scale, center[1] + 0.34 * scale, center[2] + dz * scale),
            0.05 * scale,
            color_mat if index < 4 else mats["flower_center"],
            target,
            scale=(1.0, 0.5, 1.0),
            subdivisions=1,
        )
        parent(petal, root)
    return root


def create_grass(name, center, target, scale=1.0):
    root = empty(name, p(*center), target)
    for index, dx in enumerate((-0.08, 0, 0.08)):
        blade = cone(
            f"{name}_Blade_{index}",
            p(center[0] + dx * scale, center[1] + 0.16 * scale, center[2]),
            0.026 * scale,
            0.0,
            0.32 * scale,
            4,
            mats["grass_light" if index == 1 else "grass"],
            target,
            rotation=(0.18 * (index - 1), 0, -0.45 * (index - 1)),
        )
        parent(blade, root)
    return root


reset_scene()
os.makedirs(MODEL_DIR, exist_ok=True)

environment = collection("environment")
meadow = collection("meadow")
climber = collection("climber")
sheep = collection("sheep")
cable_car = collection("cable-car")
camp = collection("camp")
lights = collection("lights")

mats = {
    "ground": material("M_Ground_Night", (0.025, 0.075, 0.18), 0.94),
    "ice": material("M_Ice_Main", (0.12, 0.55, 0.86), 0.86),
    "ice_light": material("M_Ice_Light", (0.36, 0.78, 0.96), 0.78),
    "ice_side": material("M_Ice_Side", (0.03, 0.31, 0.66), 0.9),
    "snow": material("M_Soft_Snow", (0.93, 0.98, 1.0), 0.72),
    "cloud": material("M_Cloud", (0.96, 0.98, 1.0), 0.82),
    "cloud_shadow": material("M_Cloud_Shadow", (0.72, 0.84, 1.0), 0.86),
    "route": material("M_Route_Rope", (0.82, 0.72, 0.56), 0.66),
    "peg": material("M_Route_Peg", (0.58, 0.86, 0.22), 0.64),
    "wood": material("M_Wood_Platform", (0.56, 0.34, 0.17), 0.82),
    "wood_dark": material("M_Wood_Dark", (0.24, 0.13, 0.07), 0.86),
    "metal": material("M_Metal", (0.82, 0.88, 0.88), 0.42, metallic=0.2),
    "green": material("M_Flag_Green", (0.58, 0.9, 0.15), 0.7),
    "meadow_wall": material("M_Crater_Wall_Blue", (0.08, 0.45, 0.77), 0.9),
    "meadow_rim": material("M_Crater_Rim_Ice", (0.44, 0.86, 0.98), 0.82),
    "grass": material("M_Grass", (0.44, 0.76, 0.25), 0.94),
    "grass_light": material("M_Grass_Light", (0.64, 0.92, 0.32), 0.94),
    "grass_dark": material("M_Grass_Dark", (0.22, 0.5, 0.14), 0.96),
    "flower_yellow": material("M_Flower_Yellow", (1.0, 0.78, 0.12), 0.78),
    "flower_pink": material("M_Flower_Pink", (1.0, 0.34, 0.62), 0.78),
    "flower_blue": material("M_Flower_Blue", (0.38, 0.82, 1.0), 0.78),
    "flower_center": material("M_Flower_Center", (1.0, 0.95, 0.55), 0.72),
    "skin": material("M_Wizard_Skin", (1.0, 0.72, 0.52), 0.58),
    "blush": material("M_Wizard_Blush", (1.0, 0.46, 0.48), 0.64),
    "hair": material("M_Wizard_Hair_Cream", (0.93, 0.82, 0.65), 0.78),
    "hair_shadow": material("M_Wizard_Hair_Shadow", (0.74, 0.61, 0.45), 0.82),
    "hat": material("M_Wizard_Hat_Blue", (0.08, 0.34, 0.88), 0.74),
    "hat_side": material("M_Wizard_Hat_Shade", (0.03, 0.15, 0.52), 0.82),
    "hat_speck": material("M_Wizard_Hat_Specks", (0.84, 0.78, 0.62), 0.68, emission=(0.22, 0.18, 0.08)),
    "coat": material("M_Wizard_Cape_Gold", (1.0, 0.68, 0.13), 0.72),
    "coat_shadow": material("M_Wizard_Cape_Shadow", (0.82, 0.44, 0.08), 0.8),
    "dress": material("M_Wizard_Dress_Blue", (0.03, 0.34, 0.82), 0.78),
    "dress_light": material("M_Wizard_Dress_Light", (0.12, 0.48, 0.96), 0.72),
    "white": material("M_Wizard_White_Frill", (0.98, 0.94, 0.84), 0.78),
    "boot": material("M_Wizard_Boots", (0.42, 0.2, 0.08), 0.82),
    "boot_dark": material("M_Wizard_Boot_Dark", (0.22, 0.1, 0.04), 0.86),
    "staff": material("M_Wizard_Staff", (0.42, 0.24, 0.12), 0.74),
    "gold": material("M_Wizard_Gold", (1.0, 0.74, 0.12), 0.62, emission=(0.45, 0.28, 0.04)),
    "eye": material("M_Eye", (0.03, 0.03, 0.05), 0.58),
    "moon": material("M_Moon", (1.0, 0.82, 0.1), 0.62, emission=(0.8, 0.48, 0.06)),
    "cabin_red": material("M_Cabin_Red", (0.92, 0.1, 0.07), 0.58),
    "cabin_dark": material("M_Cabin_Base", (0.08, 0.08, 0.1), 0.62),
    "window": material("M_Window_Cyan", (0.1, 0.88, 0.98), 0.45, emission=(0.04, 0.45, 0.65), alpha=0.82),
    "wool": material("M_Sheep_Wool", (0.94, 0.96, 0.96), 0.86),
    "sheep_face": material("M_Sheep_Face", (0.16, 0.18, 0.2), 0.78),
    "log": material("M_Log", (0.42, 0.18, 0.08), 0.86),
    "fire": material("M_Fire", (1.0, 0.28, 0.02), 0.42, emission=(1.0, 0.15, 0.02)),
    "fire_core": material("M_Fire_Core", (1.0, 0.78, 0.18), 0.38, emission=(1.0, 0.48, 0.04)),
    "star": material("M_Star", (1.0, 0.98, 0.88), 0.5, emission=(0.9, 0.84, 0.62)),
}

# Environment model
cube("ENV_Ground", p(0, -1.48, 0), (15.5, 11.5, 0.18), mats["ground"], environment)
create_peak("ENV_MainPeak", (-1.8, -1.08, -1.2), (1.18, 1.08, 1.12), mats["ice"], mats["ice_side"], mats["snow"], environment)
create_peak("ENV_BackPeak", (1.2, -0.86, -2.62), (0.9, 0.86, 0.86), mats["ice"], mats["ice_side"], mats["snow"], environment)
create_peak("ENV_SidePeak", (-5.7, -1.14, -1.15), (0.56, 0.55, 0.54), mats["ice_light"], mats["ice_side"], mats["snow"], environment)

create_cloud("ENV_Cloud_Large", (-3.8, 5.6, -4.1), environment, mats["cloud"], mats["cloud_shadow"], scale=1.35)
create_cloud("ENV_Cloud_Top", (1.2, 6.6, -4.2), environment, mats["cloud"], mats["cloud_shadow"], scale=0.95)
create_cloud("ENV_Cloud_Small", (-6.0, 2.1, -2.9), environment, mats["cloud"], mats["cloud_shadow"], scale=0.62)
create_cloud("ENV_Cloud_Meadow", (6.0, 4.2, -3.5), environment, mats["cloud"], mats["cloud_shadow"], scale=0.78)

for index, point in enumerate(ROUTE_POINTS):
    sphere(f"ENV_RoutePeg_{index}", p(*point), 0.13 if index in (0, len(ROUTE_POINTS) - 1) else 0.105, mats["peg"], environment, subdivisions=2)

for index, (start, end) in enumerate(zip(ROUTE_POINTS, ROUTE_POINTS[1:])):
    cylinder_between(f"ENV_RouteRope_{index}", p(*start), p(*end), 0.018, mats["route"], environment, vertices=6)

for index, (start, end) in enumerate(zip(CABLE_POINTS, CABLE_POINTS[1:])):
    cylinder_between(f"ENV_Cable_{index}", p(*start), p(*end), 0.018, mats["metal"], environment, vertices=8)

summit = ROUTE_POINTS[-1]
cube("ENV_SummitDeck", p(summit[0], summit[1] + 0.08, summit[2]), (0.86, 0.64, 0.08), mats["wood"], environment, rotation=(0, 0, 0.15))
for x in (-0.42, 0.42):
    for z in (-0.28, 0.28):
        cube("ENV_SummitLeg", p(summit[0] + x, summit[1] - 0.28, summit[2] + z), (0.07, 0.07, 0.38), mats["wood_dark"], environment)
cylinder("ENV_SummitPole", p(summit[0] + 0.05, summit[1] + 0.62, summit[2] - 0.08), 0.04, 1.1, 8, mats["metal"], environment)
cube("ENV_SummitFlag", p(summit[0] + 0.26, summit[1] + 1.06, summit[2] - 0.08), (0.34, 0.03, 0.16), mats["green"], environment)
torus("ENV_SummitPulley", p(summit[0] + 0.38, summit[1] + 0.68, summit[2] - 0.02), 0.17, 0.035, mats["metal"], environment, rotation=(math.pi / 2, 0, 0))
cylinder("ENV_MeadowTower", p(4.82, 2.72, -2.92), 0.045, 1.4, 8, mats["metal"], environment)
cube("ENV_MeadowTowerCrossbar", p(4.82, 3.38, -2.92), (0.42, 0.05, 0.05), mats["metal"], environment)

for index, pos in enumerate(((-7, 5.4, -5.4), (-1.0, 6.8, -5.6), (3.6, 5.7, -5.0), (7.2, 4.6, -5.8), (6.4, 1.6, -4.4))):
    create_star(f"ENV_Star_{index}", p(*pos), mats["star"], environment, scale=1.0 + index * 0.12)

# Meadow model
rim_center = MEADOW_CENTER
cylinder("MEADOW_CraterWall", p(rim_center[0], rim_center[1] - 0.82, rim_center[2]), 2.25, 1.85, 18, mats["meadow_wall"], meadow, fill="NOTHING")
torus("MEADOW_IceRim", p(rim_center[0], rim_center[1] + 0.05, rim_center[2]), 1.52, 0.32, mats["meadow_rim"], meadow)
cylinder("MEADOW_GrassFloor", p(rim_center[0], rim_center[1] - 0.18, rim_center[2]), 1.32, 0.08, 16, mats["grass"], meadow)
cylinder("MEADOW_InnerGrassPatch", p(rim_center[0] - 0.2, rim_center[1] - 0.12, rim_center[2] + 0.12), 0.52, 0.06, 9, mats["grass_light"], meadow)
for index, (x, z) in enumerate(((-0.9, -0.55), (-0.45, 0.62), (0.15, -0.7), (0.52, 0.55), (0.92, -0.15), (-0.08, 0.28))):
    create_grass(f"MEADOW_Grass_{index}", (rim_center[0] + x, rim_center[1] - 0.05, rim_center[2] + z), meadow, scale=1.0)
for index, (x, z, mat_key) in enumerate(((-0.72, -0.48, "flower_yellow"), (-0.42, 0.52, "flower_pink"), (0.08, -0.72, "flower_blue"), (0.45, 0.48, "flower_yellow"), (0.82, -0.2, "flower_pink"))):
    create_flower(f"MEADOW_Flower_{index}", (rim_center[0] + x, rim_center[1] - 0.02, rim_center[2] + z), mats[mat_key], meadow, scale=1.0)
for step in range(3):
    cube(
        f"MEADOW_Step_{step}",
        p(rim_center[0] - 0.2, rim_center[1] + 0.06 - step * 0.13, rim_center[2] - 1.7 + step * 0.26),
        (0.42, 0.18, 0.08),
        mats["meadow_rim" if step < 2 else "grass_light"],
        meadow,
    )

# Wizard climber model
char_root = empty("Climber_Model_Root", p(0, 0, 0), climber)

# Dress, skirt, frills, and cape.
torso = cylinder("Climber_BlueCoat_Torso", p(0, 0.46, 0.02), 0.28, 0.56, 9, mats["dress"], climber)
skirt = cone("Climber_BlueSkirt", p(0, 0.08, 0.02), 0.48, 0.31, 0.5, 10, mats["dress_light"], climber)
white_skirt = cone("Climber_WhiteSkirtFrill", p(0, -0.06, 0.02), 0.5, 0.4, 0.16, 10, mats["white"], climber)
belt = cylinder("Climber_BrownBelt", p(0, 0.31, 0.02), 0.315, 0.045, 10, mats["boot_dark"], climber)
for obj in (torso, skirt, white_skirt, belt):
    parent(obj, char_root)

for index, x in enumerate((-0.22, 0.0, 0.22)):
    pleat = cube(
        f"Climber_SkirtPleat_{index}",
        p(x, 0.08, 0.34),
        (0.06, 0.018, 0.26),
        mats["dress"],
        climber,
        rotation=(0, 0, 0.12 * (index - 1)),
    )
    parent(pleat, char_root)

for index, y in enumerate((0.52, 0.34)):
    button = sphere(
        f"Climber_GoldButton_{index}",
        p(0, y, 0.305),
        0.045,
        mats["gold"],
        climber,
        scale=(0.8, 0.8, 0.5),
        subdivisions=1,
    )
    parent(button, char_root)

cape_back = cone("Climber_Cape_Back", p(0, 0.36, -0.22), 0.62, 0.28, 0.9, 8, mats["coat"], climber, rotation=(0.2, 0, 0))
cape_shadow = cone("Climber_Cape_InnerShadow", p(0, 0.25, -0.25), 0.52, 0.22, 0.7, 8, mats["coat_shadow"], climber, rotation=(0.2, 0, 0))
cape_left = cube("Climber_Cape_LeftFold", p(-0.34, 0.42, -0.08), (0.1, 0.08, 0.52), mats["coat"], climber, rotation=(0.25, 0.08, -0.35))
cape_right = cube("Climber_Cape_RightFold", p(0.34, 0.42, -0.08), (0.1, 0.08, 0.52), mats["coat"], climber, rotation=(-0.25, -0.08, 0.35))
collar = torus("Climber_Cape_Collar", p(0, 0.68, 0.0), 0.24, 0.035, mats["coat"], climber, rotation=(math.pi / 2, 0, 0))
for obj in (cape_back, cape_shadow, cape_left, cape_right, collar):
    parent(obj, char_root)

for index, x in enumerate((-0.055, 0.055)):
    bow = cone(
        f"Climber_Cape_Bow_{index}",
        p(x, 0.67, 0.28),
        0.055,
        0.0,
        0.14,
        4,
        mats["gold"],
        climber,
        rotation=(0, 0, math.pi / 2 if x < 0 else -math.pi / 2),
    )
    parent(bow, char_root)

# Head, cream bob hair, face, and expression.
head = sphere("Climber_Head", p(0, 0.92, 0.06), 0.35, mats["skin"], climber, scale=(0.88, 0.88, 1.0), subdivisions=3)
parent(head, char_root)

hair_cap = sphere("Climber_Hair_Cap", p(0, 0.97, -0.01), 0.36, mats["hair"], climber, scale=(0.96, 0.58, 0.82), subdivisions=2)
parent(hair_cap, char_root)
for index, (x, y, z, rot, length) in enumerate(
    (
        (-0.28, 0.84, 0.06, -0.52, 0.24),
        (-0.17, 0.88, 0.24, -0.26, 0.22),
        (-0.05, 0.89, 0.31, -0.08, 0.2),
        (0.08, 0.89, 0.3, 0.12, 0.2),
        (0.2, 0.87, 0.2, 0.32, 0.22),
        (0.31, 0.83, 0.04, 0.52, 0.24),
        (-0.34, 0.74, -0.1, -0.18, 0.3),
        (0.34, 0.74, -0.1, 0.18, 0.3),
    )
):
    mat_key = "hair_shadow" if index in (6, 7) else "hair"
    strand = cone(
        f"Climber_Hair_Lock_{index}",
        p(x, y, z),
        0.09,
        0.025,
        length,
        5,
        mats[mat_key],
        climber,
        rotation=(0.5, 0, rot),
    )
    parent(strand, char_root)

for index, x in enumerate((-0.12, 0.12)):
    eye = sphere(f"Climber_Eye_{index}", p(x, 0.94, 0.365), 0.055, mats["eye"], climber, scale=(0.58, 0.88, 0.34), subdivisions=2)
    highlight = sphere(f"Climber_EyeHighlight_{index}", p(x - 0.012, 0.96, 0.392), 0.014, mats["white"], climber, scale=(0.6, 0.6, 0.22), subdivisions=1)
    parent(eye, char_root)
    parent(highlight, char_root)

for index, x in enumerate((-0.19, 0.19)):
    cheek = sphere(f"Climber_Cheek_{index}", p(x, 0.84, 0.36), 0.03, mats["blush"], climber, scale=(1.2, 0.55, 0.2), subdivisions=1)
    parent(cheek, char_root)

smile = cylinder_between("Climber_Smile", p(-0.055, 0.82, 0.372), p(0.06, 0.82, 0.372), 0.006, mats["boot_dark"], climber, vertices=5)
parent(smile, char_root)

# Oversized blue wizard hat with a bent tip, specks, and crescent charm.
hat_under = cylinder("Climber_HatBrim_Underside", p(0, 1.15, 0.0), 0.68, 0.045, 18, mats["hat_side"], climber)
hat_brim = cylinder("Climber_HatBrim", p(0, 1.18, 0.02), 0.72, 0.075, 18, mats["hat"], climber)
hat_cone = cone("Climber_HatCone", p(0.02, 1.55, -0.02), 0.43, 0.13, 0.76, 10, mats["hat"], climber, rotation=(0.1, 0, -0.08))
hat_mid = cone("Climber_HatBentMid", p(-0.12, 1.86, -0.02), 0.22, 0.08, 0.48, 8, mats["hat"], climber, rotation=(0.4, -0.05, 0.28))
hat_tip = cone("Climber_HatBentTip", p(-0.27, 2.08, -0.01), 0.12, 0.035, 0.34, 7, mats["hat"], climber, rotation=(0.62, -0.04, 0.62))
hat_knob = sphere("Climber_HatTipBall", p(-0.36, 2.18, -0.01), 0.055, mats["hat"], climber, subdivisions=2)
for obj in (hat_under, hat_brim, hat_cone, hat_mid, hat_tip, hat_knob):
    parent(obj, char_root)

for index, (x, y, z, size) in enumerate(
    (
        (-0.32, 1.22, 0.32, 0.016),
        (-0.1, 1.25, 0.43, 0.012),
        (0.18, 1.2, 0.38, 0.014),
        (0.36, 1.2, 0.08, 0.011),
        (-0.22, 1.48, 0.21, 0.013),
        (0.08, 1.62, 0.23, 0.012),
        (-0.08, 1.82, 0.12, 0.01),
        (-0.28, 1.98, 0.05, 0.01),
    )
):
    speck = sphere(f"Climber_HatSpeck_{index}", p(x, y, z), size, mats["hat_speck"], climber, scale=(1, 1, 0.25), subdivisions=1)
    parent(speck, char_root)

charm_link = cylinder_between("Climber_MoonCharm_Link", p(-0.37, 2.09, 0.0), p(-0.45, 1.92, 0.02), 0.009, mats["gold"], climber, vertices=5)
moon = create_crescent("Climber_MoonCharm", p(-0.47, 1.83, 0.03), mats["gold"], climber, scale=0.86)
parent(charm_link, char_root)
parent(moon, char_root)

# Arms include blue sleeves and a right-hand star wand. Named joints keep the Three.js pose animation working.
for name, x, is_wand_arm in (
    ("LeftArm", 0.37, False),
    ("RightArm", -0.37, True),
):
    joint = empty(f"ANIM_{name}", p(x, 0.58, 0.1), climber)
    parent(joint, char_root)
    sleeve = cylinder(
        f"Climber_{name}_Sleeve",
        p(x, 0.38, 0.14),
        0.08,
        0.42,
        7,
        mats["dress"],
        climber,
        rotation=(0.22, 0.0, 0.08 if x > 0 else -0.08),
    )
    cuff = cylinder(f"Climber_{name}_WhiteCuff", p(x, 0.17, 0.17), 0.085, 0.07, 7, mats["white"], climber)
    hand = sphere(f"Climber_{name}_Hand", p(x, 0.08, 0.19), 0.075, mats["skin"], climber, scale=(0.8, 0.8, 1.0), subdivisions=2)
    parent(sleeve, joint)
    parent(cuff, joint)
    parent(hand, joint)
    if is_wand_arm:
        wand_start = p(x - 0.02, 0.15, 0.22)
        wand_end = p(x - 0.46, 1.18, 0.45)
        wand = cylinder_between("Climber_StarWand_Staff", wand_start, wand_end, 0.018, mats["staff"], climber, vertices=6)
        star = create_five_point_star("Climber_StarWand_Star", wand_end, mats["gold"], climber, scale=0.92)
        parent(wand, joint)
        parent(star, joint)

# Legs, fluffy sock cuffs, and brown boots.
for name, x in (("LeftLeg", -0.15), ("RightLeg", 0.15)):
    joint = empty(f"ANIM_{name}", p(x, -0.1, 0), climber)
    parent(joint, char_root)
    leg = cylinder(f"Climber_{name}_Leg", p(x, -0.24, 0.02), 0.065, 0.3, 7, mats["skin"], climber)
    sock = cylinder(f"Climber_{name}_SockFur", p(x, -0.38, 0.02), 0.09, 0.1, 8, mats["white"], climber)
    boot = cube(f"Climber_{name}_Boot", p(x, -0.55, 0.07), (0.11, 0.17, 0.14), mats["boot"], climber)
    boot_toe = cube(f"Climber_{name}_BootToe", p(x, -0.6, 0.18), (0.12, 0.18, 0.055), mats["boot_dark"], climber)
    parent(leg, joint)
    parent(sock, joint)
    parent(boot, joint)
    parent(boot_toe, joint)

# Sheep model
sheep_root = empty("Sheep_Model_Root", p(0, 0, 0), sheep)
wool = sphere("Sheep_WoolBody", p(0, 0.35, 0), 0.55, mats["wool"], sheep, scale=(1.18, 0.88, 0.92), subdivisions=3)
parent(wool, sheep_root)
head_joint = empty("ANIM_Head", p(-0.52, 0.42, 0.08), sheep)
parent(head_joint, sheep_root)
face = sphere("Sheep_Face", p(-0.58, 0.42, 0.1), 0.25, mats["sheep_face"], sheep, scale=(1.0, 0.86, 0.82), subdivisions=2)
parent(face, head_joint)
for index, z in enumerate((-0.18, 0.26)):
    ear = cone(f"Sheep_Ear_{index}", p(-0.48, 0.5, z), 0.07, 0.02, 0.24, 5, mats["sheep_face"], sheep, rotation=(0.4, 0, 0.4 if z < 0 else -0.4))
    parent(ear, head_joint)
eye = sphere("Sheep_Eye", p(-0.78, 0.47, 0.21), 0.036, mats["eye"], sheep, scale=(0.6, 0.8, 1.0), subdivisions=1)
parent(eye, head_joint)
for index, (x, z) in enumerate(((-0.28, -0.22), (-0.28, 0.24), (0.28, -0.22), (0.28, 0.24))):
    leg = cube(f"Sheep_Leg_{index}", p(x, -0.08, z), (0.07, 0.08, 0.28), mats["sheep_face"], sheep)
    parent(leg, sheep_root)
    hoof = cube(f"Sheep_Hoof_{index}", p(x, -0.32, z), (0.09, 0.1, 0.06), mats["eye"], sheep)
    parent(hoof, sheep_root)
grass_bunch = empty("ANIM_GrassBunch", p(-0.76, 0.04, 0.4), sheep)
parent(grass_bunch, sheep_root)
for index, dx in enumerate((-0.08, 0, 0.08)):
    blade = cone(f"Sheep_GrassBlade_{index}", p(-0.76 + dx, 0.18 + index * 0.02, 0.4), 0.04, 0.0, 0.42, 4, mats["grass_light"], sheep, rotation=(0, 0, dx * -3))
    parent(blade, grass_bunch)

# Cable car model
cable_root = empty("CableCar_Model_Root", p(0, 0, 0), cable_car)
base = cube("CableCar_Base", p(0, -0.55, 0), (0.52, 0.35, 0.35), mats["cabin_red"], cable_car)
bottom = cube("CableCar_Bottom", p(0, -0.82, 0), (0.58, 0.39, 0.08), mats["cabin_dark"], cable_car)
for obj in (base, bottom):
    parent(obj, cable_root)
for index, (z, name) in enumerate(((0.36, "Front"), (-0.36, "Back"))):
    window = cube(f"CableCar_Window_{name}", p(0, -0.52, z), (0.34, 0.035, 0.2), mats["window"], cable_car)
    parent(window, cable_root)
ring_stem = cylinder("CableCar_RingStem", p(0, -0.02, 0), 0.035, 0.72, 8, mats["metal"], cable_car)
ring = torus("CableCar_Ring", p(0, 0.38, 0), 0.16, 0.03, mats["metal"], cable_car, rotation=(math.pi / 2, 0, 0))
for obj in (ring_stem, ring):
    parent(obj, cable_root)
for index, (x, z) in enumerate(((-0.36, 0.25), (0.36, 0.25), (-0.36, -0.25), (0.36, -0.25))):
    bolt = sphere(f"CableCar_Bolt_{index}", p(x, -0.18, z), 0.055, mats["metal"], cable_car, subdivisions=1)
    parent(bolt, cable_root)

# Camp model
camp_root = empty("Camp_Model_Root", p(*CAMP_POS), camp)
for index, rot in enumerate((math.pi / 2, -math.pi / 2, 0.45, -0.45)):
    log = cylinder(
        f"Camp_Log_{index}",
        p(CAMP_POS[0], CAMP_POS[1] + 0.03, CAMP_POS[2]),
        0.07,
        0.72,
        8,
        mats["log"],
        camp,
        rotation=(math.pi / 2, 0, rot),
    )
    parent(log, camp_root)
flame_group = empty("ANIM_FlameGroup", p(CAMP_POS[0], CAMP_POS[1] + 0.35, CAMP_POS[2]), camp)
parent(flame_group, camp_root)
outer = cone("Camp_FlameOuter", p(CAMP_POS[0], CAMP_POS[1] + 0.48, CAMP_POS[2]), 0.24, 0.02, 0.72, 6, mats["fire"], camp)
inner = cone("Camp_FlameInner", p(CAMP_POS[0], CAMP_POS[1] + 0.52, CAMP_POS[2]), 0.13, 0.01, 0.45, 6, mats["fire_core"], camp)
parent(outer, flame_group)
parent(inner, flame_group)
for index, pos in enumerate(((CAMP_POS[0] - 0.45, CAMP_POS[1] - 0.02, CAMP_POS[2] + 0.18), (CAMP_POS[0] + 0.32, CAMP_POS[1] - 0.02, CAMP_POS[2] - 0.18))):
    rock = sphere(f"Camp_Stone_{index}", p(*pos), 0.12, mats["meadow_rim"], camp, subdivisions=1)
    parent(rock, camp_root)

# Lights and preview camera for editing in Blender.
sun_data = bpy.data.lights.new("Preview_Key", "AREA")
sun_data.energy = 450
sun_data.size = 7
sun = bpy.data.objects.new("Preview_Key", sun_data)
sun.location = (-5, -6, 8)
lights.objects.link(sun)

fill_data = bpy.data.lights.new("Preview_Fill", "POINT")
fill_data.energy = 120
fill = bpy.data.objects.new("Preview_Fill", fill_data)
fill.location = (5, 4, 4)
lights.objects.link(fill)

camera_data = bpy.data.cameras.new("Preview_Camera")
camera = bpy.data.objects.new("Preview_Camera", camera_data)
camera.location = (-6.6, -8.2, 5.2)
camera.rotation_euler = (math.radians(62), 0, math.radians(-38))
camera_data.lens = 24
lights.objects.link(camera)
bpy.context.scene.camera = camera


def export_collection(collection_name, filename):
    target = bpy.data.collections[collection_name]
    bpy.ops.object.select_all(action="DESELECT")
    selected = list(target.all_objects)
    for obj in selected:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = selected[0]
    filepath = os.path.join(MODEL_DIR, filename)
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_materials="EXPORT",
    )
    return filepath


exports = {
    "environment": export_collection("environment", "environment.glb"),
    "meadow": export_collection("meadow", "meadow.glb"),
    "climber": export_collection("climber", "climber.glb"),
    "sheep": export_collection("sheep", "sheep.glb"),
    "cable-car": export_collection("cable-car", "cable-car.glb"),
    "camp": export_collection("camp", "camp.glb"),
}

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
bpy.context.scene.eevee.taa_render_samples = 64
bpy.context.scene.render.resolution_x = 1600
bpy.context.scene.render.resolution_y = 1000
bpy.context.scene.view_settings.view_transform = "Standard"
bpy.context.scene.view_settings.look = "Medium High Contrast"
bpy.ops.render.render(write_still=True)
bpy.data.images["Render Result"].save_render(filepath=PREVIEW_PATH)

for obj in bpy.data.objects:
    collection_names = {collection.name for collection in obj.users_collection}
    if collection_names & {"lights"}:
        obj.hide_render = False
    else:
        obj.hide_render = "climber" not in collection_names

camera.location = (0.0, -4.0, 1.05)
look_at(camera, (0.0, 0.0, 0.85))
camera_data.lens = 58
sun.location = (-3.0, -4.0, 5.0)
fill.location = (3.0, -3.0, 2.0)
bpy.context.scene.render.resolution_x = 1200
bpy.context.scene.render.resolution_y = 1200
bpy.ops.render.render(write_still=True)
bpy.data.images["Render Result"].save_render(filepath=WIZARD_PREVIEW_PATH)

print("Generated web GLB models:")
for key, path in exports.items():
    print(f"- {key}: {path}")
print(f"Blend: {BLEND_PATH}")
print(f"Preview: {PREVIEW_PATH}")
print(f"Wizard preview: {WIZARD_PREVIEW_PATH}")
