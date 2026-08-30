# Blender scene

Files generated from the React Three Fiber scene:

- `snowline_full_scene.blend`: editable Blender project.
- `snowline_full_scene.glb`: full-scene GLB export.
- `snowline_full_scene_preview.png`: rendered overview.
- `build_full_scene.py`: rebuild script.

## Collections

- `00_Environment`: ground, mountains, snow particles.
- `01_Route`: climbing path, route pegs, signs.
- `02_Cable`: cable curve, towers, cable car.
- `03_Meadow`: crater, grass, flowers, stairs.
- `04_Characters`: climber variants and sheep.
- `05_Camp`: logs and fire geometry.
- `06_Lights_Camera`: editable lights and overview camera.

Objects use descriptive prefixes such as `PEAK_`, `MEADOW_`, `CHAR_`,
`CABLE_`, and `CAMP_`. Use Blender's Outliner search to isolate a system.

The source website uses Three.js coordinates `(x, y, z)`. The Blender scene
maps them to `(x, -z, y)` so both projects keep the same spatial arrangement.
