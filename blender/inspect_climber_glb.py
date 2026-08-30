import math
import os

import bpy
from mathutils import Vector


ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ROOT)
GLB_PATH = os.path.join(PROJECT_ROOT, "public", "models", "climber.glb")
BLEND_PATH = os.path.join(ROOT, "climber_glb_inspection.blend")
PREVIEW_PATH = os.path.join(ROOT, "climber_glb_inspection.png")


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def scene_bounds(objects):
    mins = Vector((float("inf"), float("inf"), float("inf")))
    maxs = Vector((float("-inf"), float("-inf"), float("-inf")))
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            mins.x = min(mins.x, world.x)
            mins.y = min(mins.y, world.y)
            mins.z = min(mins.z, world.z)
            maxs.x = max(maxs.x, world.x)
            maxs.y = max(maxs.y, world.y)
            maxs.z = max(maxs.z, world.z)
    return mins, maxs


reset_scene()
bpy.ops.import_scene.gltf(filepath=GLB_PATH)

objects = list(bpy.context.scene.objects)
meshes = [obj for obj in objects if obj.type == "MESH"]
mins, maxs = scene_bounds(objects)
center = (mins + maxs) * 0.5
height = maxs.z - mins.z

area_data = bpy.data.lights.new("Inspection_Key_Light", "AREA")
area_data.energy = 520
area_data.size = 4.8
area = bpy.data.objects.new("Inspection_Key_Light", area_data)
area.location = (-2.8, -3.6, 4.2)
bpy.context.collection.objects.link(area)

fill_data = bpy.data.lights.new("Inspection_Fill_Light", "POINT")
fill_data.energy = 80
fill = bpy.data.objects.new("Inspection_Fill_Light", fill_data)
fill.location = (2.8, -2.4, 1.8)
bpy.context.collection.objects.link(fill)

camera_data = bpy.data.cameras.new("Inspection_Camera")
camera = bpy.data.objects.new("Inspection_Camera", camera_data)
camera.location = (center.x, center.y - max(3.6, height * 2.25), center.z + height * 0.12)
look_at(camera, (center.x, center.y, center.z + height * 0.08))
camera_data.lens = 58
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera

bpy.context.scene.render.engine = "BLENDER_WORKBENCH"
bpy.context.scene.display.shading.light = "STUDIO"
bpy.context.scene.display.shading.color_type = "MATERIAL"
bpy.context.scene.render.resolution_x = 1200
bpy.context.scene.render.resolution_y = 1200
bpy.context.scene.view_settings.view_transform = "Standard"
bpy.context.scene.view_settings.look = "Medium High Contrast"

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
bpy.ops.render.render(write_still=True)
bpy.data.images["Render Result"].save_render(filepath=PREVIEW_PATH)

print(f"Imported: {GLB_PATH}")
print(f"Saved inspection blend: {BLEND_PATH}")
print(f"Saved preview: {PREVIEW_PATH}")
print(f"Objects: {len(objects)}")
print(f"Meshes: {len(meshes)}")
print("Mesh names:")
for obj in meshes:
    print(f"- {obj.name}")
