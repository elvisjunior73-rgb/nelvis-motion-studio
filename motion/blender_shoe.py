"""Build the fictitious VOLT sneaker and render studio angles."""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

out = Path(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 42
scene.cycles.use_denoising = False
scene.render.resolution_x = 840
scene.render.resolution_y = 660
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.color_mode = "RGBA"
scene.render.threads_mode = "FIXED"
scene.render.threads = 4
scene.world = bpy.data.worlds.new("Studio")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (.25,.29,.43,1)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = .35
scene.view_settings.view_transform = "AgX"

def material(name, color, rough=.42, textile=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    shader = tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = rough
    if textile:
        tex = tree.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 205
        bump = tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = .35
        bump.inputs["Distance"].default_value = .027
        tree.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        tree.links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat

rubber = material("Rubber / graphite", (.018,.023,.027))
foam = material("Midsole / ice", (.72,.80,.83), .36)
ink = material("Knit / midnight blue", (.028,.065,.12), .62, True)
panels = material("Welded overlays", (.079,.18,.29), .35, True)
acid = material("Acid lime", (.55,.91,.035), .30)
laces = material("Laces / cloud", (.76,.84,.81), .56)
inside = material("Collar / charcoal", (.013,.02,.033), .66, True)
sections = [
    (-2.18,.09,.49),(-2.02,.48,1.17),(-1.73,.62,1.58),
    (-1.34,.64,1.48),(-.90,.65,1.37),(-.47,.69,1.52),
    (0,.75,1.28),(.53,.83,.96),(1.05,.85,.76),
    (1.53,.74,.63),(1.91,.49,.53),(2.08,.05,.37),
]

def mesh(name, verts, faces, mat, subdivision=0):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for face in data.polygons:
        face.use_smooth = True
    if subdivision:
        mod = obj.modifiers.new("Smooth sculpt", "SUBSURF")
        mod.levels = subdivision
    return obj

def loft(name, levels, mat, upper=False):
    verts = []
    count = 24
    for x, width, height in sections:
        for j in range(count):
            angle = 2 * math.pi * j / count
            y = math.cos(angle) * width
            z = math.sin(angle)
            lift = .19 * (max(0, x - 1.1) / .98) ** 2 + .045 * max(0, -x - 1.6)
            if upper:
                z = .34 + (height - .34) * max(0,z) ** .79 + .11 * min(0,z)
                y *= .97
            else:
                low, high, widen = levels
                y *= widen
                z = (high + low) / 2 + (high - low) / 2 * math.copysign(abs(z) ** .36, z)
            verts.append((x,y,z + lift))
    faces = [(i*count+j,i*count+(j+1)%count,(i+1)*count+(j+1)%count,(i+1)*count+j)
             for i in range(len(sections)-1) for j in range(count)]
    faces.extend([tuple(reversed(range(count))),tuple(range(len(verts)-count,len(verts)))])
    return mesh(name, verts, faces, mat, 2)

def tube(name, points, mat, radius=.026):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 12
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points)-1)
    for p, xyz in zip(spline.bezier_points, points):
        p.co = xyz
        p.handle_left_type = p.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj

def ellipsoid(name, location, scale, mat, angle=0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=12, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler.y = angle
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj

loft("Outsole", (.02,.20,1.06), rubber)
loft("Sculpted midsole", (.12,.43,1.055), foam)
loft("Upper / woven mesh", (), ink, True)
ellipsoid("Sock collar", (-1.38,0,1.44), (.60,.43,.14), inside, -.08)
for side in (-1,1):
    tube("Collar binding", [(-1.95,0,1.36),(-1.73,.30*side,1.53),(-1.34,.37*side,1.46),
                            (-.94,.26*side,1.48),(-.83,0,1.50)], panels, .041)
    tube("Heel counter piping", [(-2.08,.22*side,.46),(-1.80,.51*side,.61),(-1.52,.56*side,.93),
                                 (-1.21,.53*side,1.04),(-.92,.56*side,.94),(-.55,.66*side,.64)], panels,.065)
    tube("Toe cap stitching", [(.33,.74*side,.54),(.91,.79*side,.48),(1.48,.65*side,.54),
                               (1.88,.32*side,.59),(2.00,0,.61)], panels,.038)
    tube("VOLT side mark", [(-1.10,.602*side,.96),(-.75,.654*side,.73),(-.52,.679*side,.76),
                            (-.08,.732*side,.99),(.20,.765*side,.96)], acid,.075)
    tube("Side mark trace", [(-.63,.69*side,.62),(-.26,.73*side,.65),(.09,.78*side,.78)], acid,.020)
    for i in range(7):
        x = -.62 + i*.192
        z = 1.51 - (x+.62)*.47
        w = .25 + i*.021
        ellipsoid("Eyelet", (x,w*side,z-.045),(.085,.061,.044),panels)
        if side == 1:
            tube("Lace", [(x,-w,z-.015),(x+.041,0,z+.058),(x+.077,w,z-.062)], laces,.027)
    for i in range(12):
        x = -1.72 + .29*i
        w = .60 + .14*math.exp(-((x-.55)/.85)**2)
        ellipsoid("Tread", (x,w*side,.095 + .14*max(0,x-1)**2),(.106,.076,.062),
                  acid if i in (0,1,9,10,11) else rubber)
tube("Pull tab", [(-2.03,-.15,.98),(-2.08,-.11,1.42),(-2.05,0,1.57),
                  (-2.08,.11,1.42),(-2.03,.15,.98)], acid,.039)

def look(obj, target):
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

for name, location, energy, size, color in [
    ("Key", (2,-4,6),610,4,(.83,.92,1)),("Rim",(-3,3,4),800,3,(.42,.58,1)),
    ("Fill", (1,2,1),190,3,(.89,1,.66)),("Front", (4,-1,2),240,3,(1,1,1)),
]:
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
    lamp = bpy.data.objects.new(name,data)
    scene.collection.objects.link(lamp)
    lamp.location = location
    look(lamp,(0,0,.6))

camera = bpy.data.objects.new("Camera",bpy.data.cameras.new("Camera"))
scene.collection.objects.link(camera)
scene.camera = camera
camera.data.type = "ORTHO"
views = [
    ("hero", (3,-8,3.0), (0,0,.79), 5.05, .15),
    ("detail",(-2.5,-8,4.4),(-.42,0,.97),3.95,-.22),
    ("final", (5,-7,3.4),(0,0,.82),4.9,.23),
]
for label, location, target, scale, roll in views:
    camera.location = location
    look(camera,target)
    camera.rotation_euler.rotate_axis("Z",roll)
    camera.data.ortho_scale = scale
    scene.render.filepath = str(out / (label+".png"))
    if label == "hero":
        bpy.ops.wm.save_as_mainfile(filepath=str(out/"VOLT.blend"))
    bpy.ops.render.render(write_still=True)

if "--orbit" in sys.argv:
    orbit = out / "turn"
    orbit.mkdir(exist_ok=True)
    scene.cycles.samples = 18
    scene.render.resolution_percentage = 67
    for index in range(36):
        turn = -.47 + 1.25 * index/35
        camera.location = (8*math.sin(turn),-8*math.cos(turn),3.3)
        look(camera,(0,0,.81))
        camera.rotation_euler.rotate_axis("Z",.09+index/500)
        camera.data.ortho_scale = 5.15
        scene.render.filepath = str(orbit / f"{index:02d}.png")
        bpy.ops.render.render(write_still=True)
