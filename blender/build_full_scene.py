import bpy
import math
import os
from mathutils import Vector


ROOT = os.path.dirname(os.path.abspath(__file__))
BLEND_PATH = os.path.join(ROOT, "snowline_full_scene.blend")
GLB_PATH = os.path.join(ROOT, "snowline_full_scene.glb")
PREVIEW_PATH = os.path.join(ROOT, "snowline_full_scene_preview.png")


def p(x, y, z):
    """Map Three.js coordinates (Y up) to Blender coordinates (Z up)."""
    return (x, -z, y)


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
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


def material(name, color, roughness=0.8, metallic=0.0, emission=None):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.diffuse_color = (*color, 1.0)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission:
            bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 1.8
    return mat


def assign(obj, mat):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    return obj


def smooth(obj, enabled=False):
    if obj.type != "MESH":
        return obj
    for polygon in obj.data.polygons:
        polygon.use_smooth = enabled
    return obj


def empty(name, location, target):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    target.objects.link(obj)
    return obj


def cube(name, location, scale, mat, target, rotation=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        modifier = obj.modifiers.new("Editable_Bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    assign(obj, mat)
    return move_to_collection(obj, target)


def cylinder(name, location, radius, depth, vertices, mat, target, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    smooth(obj, False)
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
    smooth(obj, False)
    return move_to_collection(obj, target)


def sphere(name, location, radius, mat, target, segments=16, rings=10, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        radius=radius,
        location=location,
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    smooth(obj, False)
    return move_to_collection(obj, target)


def torus(name, location, major_radius, minor_radius, major_segments, minor_segments, mat, target, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=major_segments,
        minor_segments=minor_segments,
        location=location,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, mat)
    smooth(obj, False)
    return move_to_collection(obj, target)


def curve_object(name, points, bevel, mat, target, cyclic=False):
    curve_data = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 2
    curve_data.bevel_depth = bevel
    curve_data.bevel_resolution = 1
    spline = curve_data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for spline_point, point in zip(spline.points, points):
        spline_point.co = (*point, 1.0)
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve_data)
    target.objects.link(obj)
    assign(obj, mat)
    return obj


def parent(child, root):
    child.parent = root
    return child


reset_scene()

environment = collection("00_Environment")
route_collection = collection("01_Route")
cable_collection = collection("02_Cable")
meadow_collection = collection("03_Meadow")
characters = collection("04_Characters")
camp_collection = collection("05_Camp")
lights_collection = collection("06_Lights_Camera")

# Materials
mat_ground = material("M_Ground", (0.055, 0.15, 0.29), 0.96)
mat_ice_blue = material("M_Ice_Blue", (0.19, 0.52, 0.72), 0.84)
mat_ice_light = material("M_Ice_Light", (0.62, 0.86, 0.94), 0.78)
mat_snow = material("M_Snow", (0.88, 0.98, 1.0), 0.7)
mat_route = material("M_Route", (0.72, 0.96, 1.0), 0.45, emission=(0.25, 0.65, 0.72))
mat_dark = material("M_Dark", (0.055, 0.035, 0.11), 0.72)
mat_red = material("M_Red", (0.86, 0.13, 0.24), 0.58)
mat_skin = material("M_Skin", (1.0, 0.56, 0.37), 0.58)
mat_cyan = material("M_Cyan", (0.2, 0.75, 0.88), 0.56)
mat_backpack = material("M_Backpack", (0.12, 0.07, 0.33), 0.72)
mat_white = material("M_Sheep_Wool", (0.92, 0.96, 1.0), 0.86)
mat_sheep_face = material("M_Sheep_Face", (0.72, 0.53, 0.38), 0.72)
mat_grass = material("M_Grass", (0.34, 0.68, 0.22), 0.96)
mat_grass_light = material("M_Grass_Light", (0.5, 0.82, 0.28), 0.94)
mat_rock = material("M_Crater_Rock", (0.35, 0.65, 0.72), 0.9)
mat_rock_dark = material("M_Crater_Wall", (0.12, 0.39, 0.58), 0.94)
mat_log = material("M_Log", (0.38, 0.16, 0.08), 0.86)
mat_fire = material("M_Fire", (1.0, 0.3, 0.04), 0.4, emission=(1.0, 0.12, 0.01))
mat_fire_core = material("M_Fire_Core", (1.0, 0.82, 0.22), 0.36, emission=(1.0, 0.55, 0.04))
mat_metal = material("M_Cable_Metal", (0.76, 0.86, 0.9), 0.42, metallic=0.25)
mat_pink = material("M_Flower_Pink", (1.0, 0.26, 0.55), 0.76)
mat_yellow = material("M_Flower_Yellow", (1.0, 0.82, 0.16), 0.76)
mat_purple = material("M_Flower_Purple", (0.56, 0.31, 1.0), 0.76)
mat_flower_center = material("M_Flower_Center", (1.0, 0.92, 0.48), 0.72)


# Ground
cube("ENV_Ground", p(0, -1.5, 0), (16, 16, 0.25), mat_ground, environment)


def create_peak(name, position, scale, color_mat):
    root = empty(name, p(*position), environment)
    peak = cone(
        name + "_Body",
        (0, 0, 1.7),
        2.8,
        0,
        6.4,
        5,
        color_mat,
        environment,
        rotation=(0.0, 0.05, 0.38),
    )
    peak.scale = scale
    parent(peak, root)
    snow = cone(
        name + "_Snowcap",
        (-0.58 * scale[0], -0.14 * scale[2], 4.55 * scale[1]),
        1.08,
        0,
        1.85,
        5,
        mat_snow,
        environment,
        rotation=(0.0, 0.1, 0.38),
    )
    snow.scale = scale
    parent(snow, root)
    return root


create_peak("PEAK_Main", (-1.5, 1.45, -1.35), (1.25, 1.25, 1.05), mat_ice_blue)
create_peak("PEAK_Back", (1.15, 1.1, -2.75), (0.95, 0.95, 0.8), mat_ice_blue)
create_peak("PEAK_Start", (-5.7, -0.15, -1.2), (0.54, 0.54, 0.48), mat_ice_light)


# Route and markers
route_points_three = [
    (-5.8, -1.1, 0.4),
    (-4.4, 0.15, -0.55),
    (-3.1, 1.25, -0.95),
    (-1.85, 2.25, -0.72),
    (-0.72, 3.4, -0.95),
    (0.25, 4.72, -0.5),
]
route_points = [p(*point) for point in route_points_three]
curve_object("ROUTE_Climb_Path", route_points, 0.035, mat_route, route_collection)
for index, point in enumerate(route_points):
    sphere(
        f"ROUTE_Peg_{index:02d}",
        Vector(point) + Vector((0, 0, 0.13)),
        0.14 if index in (0, len(route_points) - 1) else 0.08,
        mat_grass_light if index in (0, len(route_points) - 1) else mat_snow,
        route_collection,
        segments=10,
        rings=6,
    )


def sign(name, location, color_mat):
    root = empty(name, p(*location), route_collection)
    parent(cube(name + "_Post", (0, 0, 0.32), (0.04, 0.04, 0.36), mat_dark, route_collection), root)
    parent(cube(name + "_Board", (0.24, 0, 0.62), (0.24, 0.04, 0.11), color_mat, route_collection), root)


sign("SIGN_Works", (-4.1, 0.22, -0.15), mat_yellow)
sign("SIGN_About", (-2.25, 2.18, -0.32), mat_pink)
sign("SIGN_Summit", (0.28, 4.65, -0.12), mat_grass_light)
sign("SIGN_Meadow", (6.72, 2.46, -1.3), mat_cyan)


# Cable system
cable_points_three = [
    (0.25, 4.72, -0.5),
    (1.8, 4.98, -1.35),
    (3.55, 4.1, -2.15),
    (4.82, 3.08, -2.92),
]
cable_points = [p(*point) for point in cable_points_three]
curve_object("CABLE_Main_Line", cable_points, 0.025, mat_metal, cable_collection)


def cable_tower(name, location):
    root = empty(name, p(*location), cable_collection)
    parent(cube(name + "_Pole", (0, 0, -0.75), (0.06, 0.06, 0.75), mat_metal, cable_collection), root)
    parent(cube(name + "_Crossbar", (0, 0, -0.05), (0.41, 0.05, 0.05), mat_metal, cable_collection), root)
    return root


cable_tower("CABLE_Tower_Start", cable_points_three[0])
cable_tower("CABLE_Tower_End", cable_points_three[-1])

cable_root = empty("CABLE_Car", p(2.8, 4.45, -1.85), cable_collection)
parent(cube("CABLE_Car_Body", (0, 0, -0.34), (0.38, 0.26, 0.27), mat_red, cable_collection, bevel=0.04), cable_root)
parent(cube("CABLE_Car_Base", (0, 0, -0.65), (0.44, 0.28, 0.04), mat_dark, cable_collection), cable_root)
parent(cube("CABLE_Car_Window", (0, -0.28, -0.2), (0.12, 0.02, 0.1), mat_cyan, cable_collection), cable_root)
parent(cylinder("CABLE_Car_Hanger", (0, 0, 0.16), 0.025, 0.48, 8, mat_metal, cable_collection), cable_root)
parent(torus("CABLE_Car_Wheel", (0, 0, 0.46), 0.12, 0.03, 18, 8, mat_metal, cable_collection, rotation=(math.pi / 2, 0, 0)), cable_root)


# Meadow crater
meadow_center = p(5.05, 2.36, -1.3)
meadow_root = empty("MEADOW_Crater", meadow_center, meadow_collection)

outer_wall = cone(
    "MEADOW_Outer_Wall",
    (0, 0, -0.9),
    2.68,
    1.82,
    1.9,
    10,
    mat_rock_dark,
    meadow_collection,
)
parent(outer_wall, meadow_root)

rim = torus("MEADOW_Rim", (0, 0, 0.1), 1.55, 0.34, 10, 4, mat_rock, meadow_collection)
parent(rim, meadow_root)

grass_floor = cylinder("MEADOW_Grass_Floor", (0, 0, -0.17), 1.34, 0.08, 12, mat_grass, meadow_collection)
parent(grass_floor, meadow_root)

grass_ring = torus("MEADOW_Grass_Ring", (0, 0, -0.12), 0.99, 0.31, 12, 4, mat_grass_light, meadow_collection)
grass_ring.scale.z = 0.18
parent(grass_ring, meadow_root)

grass_patch = cylinder("MEADOW_Dark_Grass_Patch", (-0.2, -0.12, -0.11), 0.42, 0.035, 9, mat_grass, meadow_collection)
parent(grass_patch, meadow_root)

for step in range(3):
    stair = cube(
        f"MEADOW_Stair_{step:02d}",
        (-0.2, 1.72 - step * 0.28, 0.18 - step * 0.13),
        (0.37, 0.18, 0.08),
        mat_ice_light if step < 2 else mat_grass_light,
        meadow_collection,
    )
    parent(stair, meadow_root)


def create_grass_tuft(name, location, rotation=0.0):
    root = empty(name, location, meadow_collection)
    root.rotation_euler.z = rotation
    for index, x in enumerate((-0.1, 0.0, 0.1)):
        blade = cone(
            f"{name}_Blade_{index}",
            (x, 0, 0.14 + index * 0.03),
            0.045,
            0,
            0.36,
            4,
            mat_grass_light if index == 1 else mat_grass,
            meadow_collection,
            rotation=(0, x * -2.1, 0),
        )
        parent(blade, root)
    return root


grass_tufts = [
    (-1.02, 0.08, 0.2),
    (-0.72, -0.8, -0.12),
    (-0.48, 0.44, 0.08),
    (0.02, -0.48, -0.18),
    (0.34, 0.42, 0.16),
    (0.75, -0.1, -0.08),
    (1.02, 0.24, 0.12),
]
for index, (x, z, rotation) in enumerate(grass_tufts):
    tuft = create_grass_tuft(f"MEADOW_Grass_{index:02d}", (x, -z, -0.02), rotation)
    parent(tuft, meadow_root)


def create_flower(name, location, petal_mat):
    root = empty(name, location, meadow_collection)
    parent(cylinder(name + "_Stem", (0, 0, 0.14), 0.02, 0.28, 5, mat_grass, meadow_collection), root)
    parent(sphere(name + "_Center", (0, 0, 0.31), 0.05, mat_flower_center, meadow_collection, 8, 6), root)
    for index, (x, y) in enumerate(((0.07, 0), (-0.07, 0), (0, 0.07), (0, -0.07))):
        parent(sphere(f"{name}_Petal_{index}", (x, y, 0.31), 0.055, petal_mat, meadow_collection, 8, 6), root)
    return root


flowers = [
    (-0.92, -0.62, mat_pink),
    (-0.62, 0.72, mat_yellow),
    (-0.2, -0.88, mat_purple),
    (0.18, 0.78, mat_pink),
    (0.72, 0.58, mat_yellow),
    (0.9, -0.52, mat_purple),
    (0.42, -0.64, mat_pink),
]
for index, (x, z, petal_mat) in enumerate(flowers):
    flower = create_flower(f"MEADOW_Flower_{index:02d}", (x, -z, 0.0), petal_mat)
    parent(flower, meadow_root)


def create_climber(name, location, pose="standing"):
    root = empty(name, location, characters)
    body = cylinder(name + "_Body", (0, 0, 0.42), 0.28, 0.52, 12, mat_red, characters)
    parent(body, root)
    head = sphere(name + "_Head", (0, 0, 0.82), 0.32, mat_skin, characters, 18, 12)
    parent(head, root)
    backpack = cube(name + "_Backpack", (0, 0.25, 0.36), (0.22, 0.09, 0.24), mat_backpack, characters, bevel=0.04)
    parent(backpack, root)

    limb_data = [
        ("LeftArm", (-0.34, 0, 0.28), mat_skin),
        ("RightArm", (0.34, 0, 0.28), mat_skin),
        ("LeftLeg", (-0.13, 0, -0.22), mat_cyan),
        ("RightLeg", (0.13, 0, -0.22), mat_ice_blue),
    ]
    for limb_name, limb_location, limb_mat in limb_data:
        limb = cylinder(name + "_" + limb_name, limb_location, 0.065, 0.56, 8, limb_mat, characters)
        parent(limb, root)

    if pose == "camp":
        root.rotation_euler.y = math.radians(78)
    elif pose == "climbing":
        root.rotation_euler.z = math.radians(-8)
    return root


create_climber("CHAR_Climber_Route", p(-4.4, 0.15, -0.55), "climbing")
create_climber("CHAR_Climber_Meadow", Vector(meadow_center) + Vector((-0.46, 0.42, 0.12)), "standing")
create_climber("CHAR_Climber_Camp", p(4.05, -1.13, 3.58), "camp")


def create_sheep(name, location):
    root = empty(name, location, characters)
    parent(sphere(name + "_Body", (0, 0, 0.28), 0.54, mat_white, characters, 16, 10, scale=(1.0, 0.82, 0.85)), root)
    parent(sphere(name + "_Head", (-0.48, -0.04, 0.34), 0.28, mat_sheep_face, characters, 14, 10), root)
    for index, (x, y) in enumerate(((-0.28, -0.2), (-0.28, 0.22), (0.28, -0.2), (0.28, 0.22))):
        leg = cylinder(f"{name}_Leg_{index}", (x, y, -0.24), 0.045, 0.34, 8, mat_dark, characters)
        parent(leg, root)
    return root


sheep_location = Vector(meadow_center) + Vector((0.36, -0.02, 0.26))
create_sheep("CHAR_Sheep", sheep_location)


# Campfire
camp_position = p(4.7, -1.08, 3.4)
camp_root = empty("CAMP_Fire_Set", camp_position, camp_collection)
log_a = cylinder("CAMP_Log_A", (-0.12, 0, 0.02), 0.07, 0.72, 8, mat_log, camp_collection, rotation=(0, math.pi / 2, 0))
log_a.rotation_euler.z = math.radians(30)
parent(log_a, camp_root)
log_b = cylinder("CAMP_Log_B", (0.12, 0, 0.02), 0.07, 0.72, 8, mat_log, camp_collection, rotation=(0, math.pi / 2, 0))
log_b.rotation_euler.z = math.radians(-30)
parent(log_b, camp_root)
parent(cone("CAMP_Flame_Outer", (0, 0, 0.38), 0.22, 0, 0.72, 6, mat_fire, camp_collection), camp_root)
parent(cone("CAMP_Flame_Core", (0, 0, 0.49), 0.12, 0, 0.46, 6, mat_fire_core, camp_collection), camp_root)


# Snow particles as editable ico spheres
snow_root = empty("ENV_Snow_Particles", (0, 0, 0), environment)
for index in range(90):
    x = ((index * 37) % 101) / 100.0 * 22 - 11
    y = ((index * 53) % 97) / 96.0 * 16 - 8
    z = ((index * 29) % 89) / 88.0 * 9
    size = 0.018 + (index % 4) * 0.009
    flake = sphere(f"ENV_Snow_{index:03d}", (x, y, z), size, mat_snow, environment, 6, 4)
    parent(flake, snow_root)


# Camera and lighting
bpy.ops.object.light_add(type="AREA", location=(-6, -4, 11))
key = bpy.context.object
key.name = "LIGHT_Key"
key.data.energy = 1400
key.data.shape = "DISK"
key.data.size = 8
key.rotation_euler = (math.radians(24), 0, math.radians(-35))
move_to_collection(key, lights_collection)

bpy.ops.object.light_add(type="AREA", location=(7, 4, 7))
fill = bpy.context.object
fill.name = "LIGHT_Fill"
fill.data.energy = 850
fill.data.color = (0.28, 0.66, 1.0)
fill.data.size = 7
move_to_collection(fill, lights_collection)

bpy.ops.object.light_add(type="POINT", location=Vector(camp_position) + Vector((0, 0, 1.2)))
fire_light = bpy.context.object
fire_light.name = "LIGHT_Campfire"
fire_light.data.energy = 600
fire_light.data.color = (1.0, 0.28, 0.06)
fire_light.data.shadow_soft_size = 2.0
move_to_collection(fire_light, lights_collection)

bpy.ops.object.camera_add(location=(13.8, -17.5, 12.5))
camera = bpy.context.object
camera.name = "CAMERA_Full_Scene"
camera.data.lens = 48
move_to_collection(camera, lights_collection)

target = Vector((0, 0, 2.0))
direction = target - camera.location
camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = camera


# World and render settings
world = bpy.context.scene.world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.028, 0.09, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.3

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = PREVIEW_PATH
scene.render.film_transparent = False
scene.view_settings.look = "AgX - Medium High Contrast"

scene["README"] = "Collections mirror the React Three Fiber project. Edit materials, object transforms, and named asset groups."
scene["SOURCE_FILE"] = "personal-home-3d/src/App.jsx"
scene["COORDINATE_NOTE"] = "Three.js (x,y,z) mapped to Blender (x,-z,y)."

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
bpy.ops.export_scene.gltf(
    filepath=GLB_PATH,
    export_format="GLB",
    use_selection=False,
    export_apply=True,
)
bpy.ops.render.render(write_still=True)

print("BLEND:", BLEND_PATH)
print("GLB:", GLB_PATH)
print("PREVIEW:", PREVIEW_PATH)
