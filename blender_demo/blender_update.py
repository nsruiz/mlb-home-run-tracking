import bpy
import json
import os
import urllib.request
import math
import time
from datetime import datetime

with open('../../data/output/blender_payload.json') as f:
    data = json.load(f)

# This function is used as part of the rendering process to ensure looped renders happen appropriately.
render_complete = False
def render_complete_handler(scene):
    global render_complete
    render_complete = True

bpy.app.handlers.render_complete.append(render_complete_handler)

# Loop through home runs in the data, assigning data points to relevant variables.
for idx, play_id in enumerate(data):
    render_complete = False
    play = data[play_id]
    hitterFirstName = play['Hitter first name'].upper()
    hitterLastName = play['Hitter last name'].upper()
    hitterBatSide = play['Hitter bat side']
    hitterHeadshotUrl = play['Hitter headshot']
    team = play['Team']
    teamLocation = play['Team location'].upper()
    teamName = play['Team name'].upper()
    teamPrimaryColor = play['Team primary color']
    teamSecondaryColor = play['Team secondary color']
    distance = play['Distance']
    exitVelo = play['Exit velo']
    launchAngle = play['Launch angle']
    hangTime = play['Hang time']
    maxHeight = play['Max height']
    batSpeed = play['Bat speed']
    attackAngle = play['Attack angle']
    contactTime = play['Contact time']
    contactDT = datetime.strptime(contactTime, "%Y-%m-%dT%H:%M:%S.%fZ")
    contactTime = contactDT.time()
    batHeadCoordinates = play['Bat head coordinates']
    batHandleCoordinates = play['Bat handle coordinates']
    headshot_url = play['Hitter headshot']
    highlight_url = play['Highlight URL']
    sideview_url = play['Sideview URL']
    # NOTE: Certain elements are pulled from AWS S3 before being transformed in the world. They are omitted here to keep the repo lightweight.

    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # Import batter headshot, assign as material
    headshot_path = bpy.app.tempdir + f"{hitterFirstName}_{hitterLastName}_headshot.png"
    urllib.request.urlretrieve(headshot_url, headshot_path)
    img = bpy.data.images.load(headshot_path)
    mat = bpy.data.materials.new(name=f"{hitterFirstName}_{hitterLastName}_headshot")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex_image.image = img
    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
    bpy.data.objects["MLB Profile Player Image"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["MLB Profile Player Image"]
    bpy.context.active_object.data.materials[0] = mat
    bpy.ops.object.select_all(action='DESELECT')

    # Import sideview, assign as material
    sideview_path = os.path.join(bpy.app.tempdir, f"{hitterFirstName}_{hitterLastName}_sideview.mp4")
    urllib.request.urlretrieve(sideview_url, sideview_path)
    bpy.data.objects["Dugout Sideview Video"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Dugout Sideview Video"]
    obj = bpy.context.active_object

    mat = bpy.data.materials.new(name=f"{hitterFirstName}_{hitterLastName}_sideview")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    texture_node = mat.node_tree.nodes.new('ShaderNodeTexImage')

    image = bpy.data.images.load(sideview_path)
    texture_node.image = image
    texture_node.image.source = 'MOVIE'

    bsdf_node = nodes.get('Principled BSDF')
    if bsdf_node:
        mat.node_tree.links.new(texture_node.outputs['Color'], bsdf_node.inputs['Base Color'])

    # Assign the material to the object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    texture_node.image_user.frame_start = 1
    texture_node.image_user.frame_duration = 360
    texture_node.image_user.frame_offset = 1
    texture_node.image_user.use_auto_refresh = True
    texture_node.image_user.use_cyclic = True
    print("Sideview assigned")
    bpy.ops.object.select_all(action='DESELECT')

    # Update MLB team location
    bpy.data.objects["MLB City/State Name"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['MLB City/State Name']
    bpy.context.object.data.body = teamLocation
    bpy.ops.object.select_all(action='DESELECT')

    # Update MLB team name
    bpy.data.objects["MLB Team Name"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['MLB Team Name']
    bpy.context.object.data.body = teamName
    bpy.ops.object.select_all(action='DESELECT')

    # Import highlight, assign as material
    highlight_path = bpy.app.tempdir + f"{hitterFirstName}_{hitterLastName}_highlight.mp4"
    urllib.request.urlretrieve(highlight_url, highlight_path)
    bpy.data.objects["Broadcast View Horizontal"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Broadcast View Horizontal"]
    obj = bpy.context.active_object

    mat = bpy.data.materials.new(name=f"{hitterFirstName}_{hitterLastName}_highlight")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    texture_node = mat.node_tree.nodes.new('ShaderNodeTexImage')

    image = bpy.data.images.load(highlight_path)
    texture_node.image = image
    texture_node.image.source = 'MOVIE'

    bsdf_node = nodes.get('Principled BSDF')
    if bsdf_node:
        mat.node_tree.links.new(texture_node.outputs['Color'], bsdf_node.inputs['Base Color'])

    # Assign the material to the object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

    texture_node.image_user.frame_start = 1
    texture_node.image_user.frame_duration = 1500
    texture_node.image_user.frame_offset = 1
    print("Highlight assigned")
    bpy.ops.object.select_all(action='DESELECT')

    # Add audio from highlight video to the scene
    scene = bpy.context.scene
    if not scene.sequence_editor:
        scene.sequence_editor_create()
    sequence = scene.sequence_editor
    for strip in sequence.sequences_all:
        if strip.type == 'SOUND' and strip.channel == 1:
            sequence.sequences.remove(strip)
            break
    soundstrip = sequence.sequences.new_sound("broadcast_audio", filepath=highlight_path, channel=1, frame_start=1)

    # Update MLB team location
    bpy.data.objects["MLB City/State Name"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['MLB City/State Name']
    bpy.context.object.data.body = teamLocation
    bpy.ops.object.select_all(action='DESELECT')

    # Update MLB team name
    bpy.data.objects["MLB Team Name"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['MLB Team Name']
    bpy.context.object.data.body = teamName
    bpy.ops.object.select_all(action='DESELECT')

    # Update player first name
    bpy.data.objects["Player First Name"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Player First Name']
    bpy.context.object.data.body = hitterFirstName
    bpy.ops.object.select_all(action='DESELECT')

    # Update player last name
    bpy.data.objects["Player Last Name"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Player Last Name']
    bpy.context.object.data.body = hitterLastName
    bpy.ops.object.select_all(action='DESELECT')

    # Update player full name
    bpy.data.objects["Player Name"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Player Name']
    bpy.context.object.data.body = hitterFirstName + " " + hitterLastName
    bpy.ops.object.select_all(action='DESELECT')

    # Update bat speed
    bpy.data.objects["# Barrel Speed"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['# Barrel Speed']
    bpy.context.object.data.body = str(int(round(batSpeed)))
    bpy.ops.object.select_all(action='DESELECT')

    # Update attack angle
    bpy.data.objects["# Attack Angle"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['# Attack Angle']
    bpy.context.object.data.body = str(int(round(attackAngle))) + "°"
    bpy.ops.object.select_all(action='DESELECT')

    # Update launch angle
    bpy.data.objects["# Games Played"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["# Games Played"]
    bpy.context.object.data.body = str(int(round(launchAngle))) + "°"
    bpy.ops.object.select_all(action='DESELECT')

    # Update exit velo
    bpy.data.objects["# Batting Avg"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["# Batting Avg"]
    bpy.context.object.data.body = str(round(exitVelo, 1))
    bpy.ops.object.select_all(action='DESELECT')

    # Change logos to batter's team
    # First, hide all 30
    logos_collection = bpy.data.collections.get("MLB Logos")
    for logo in logos_collection.children:
        logo.hide_viewport = True
        logo.hide_render = True

    typed_logos_collection = bpy.data.collections.get("MLB Typed Logos")
    for typed_logo in typed_logos_collection.children:
        typed_logo.hide_viewport = True
        typed_logo.hide_render = True

    # Make appropriate team logos visible
    team_logo = team + " Logo"
    team_typed_logo = team + " Type Logo"
    if team == "Athletics":
        team_logo = "Oakland A's Logo"
        team_typed_logo = "Oakland A's Type Logo"
    elif team == "St. Louis Cardinals":
        team_logo = "St Louis Cardinals Logo"
        team_typed_logo = "St Louis Cardinals Type Logo"

    team_logo_collection = bpy.data.collections[team_logo]
    team_logo_collection.hide_viewport = False
    team_logo_collection.hide_render = False

    team_typed_logo_collection = bpy.data.collections[team_typed_logo]
    team_typed_logo_collection.hide_viewport = False
    team_typed_logo_collection.hide_render = False

    # Update colors throughout scene to team colors
    primary = bpy.data.materials.get(teamPrimaryColor)
    secondary = bpy.data.materials.get(teamSecondaryColor)

    if primary is None:
        for material in bpy.data.materials:
            if material.name.startswith(teamPrimaryColor):
                primary = bpy.data.materials.get(material.name)
                break

    if secondary is None:
        for material in bpy.data.materials:
            if material.name.startswith(teamSecondaryColor):
                secondary = bpy.data.materials.get(material.name)
                break

    bpy.data.objects["Low Poly Surface"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Low Poly Surface']
    bpy.context.active_object.data.materials[0] = primary
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["Game On"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Game On']
    bpy.context.active_object.data.materials[0] = primary
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["Rectangle 1"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Rectangle 1']
    bpy.context.active_object.data.materials[0] = primary
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["Rectangle 2"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Rectangle 2']
    bpy.context.active_object.data.materials[0] = primary
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["App Logo Middle"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['App Logo Middle']
    bpy.context.active_object.data.materials[0] = secondary
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["Barrel Speed.001"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Barrel Speed.001']
    bpy.context.active_object.data.materials[0] = secondary
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["Attack Angle"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Attack Angle']
    bpy.context.active_object.data.materials[0] = secondary
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["DK"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['DK']
    bpy.context.active_object.data.materials[0] = secondary
    bpy.ops.object.select_all(action='DESELECT')

    # DK Sensor
    bpy.data.objects["Atomic DK Logo.002"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Atomic DK Logo.002"]
    bpy.context.active_object.data.materials[0] = secondary
    bpy.ops.object.select_all(action='DESELECT')

    # Tape Measure
    bpy.data.objects["Cylinder.004"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Cylinder.004"]
    bpy.context.active_object.data.materials[0] = primary
    bpy.context.active_object.data.materials[2] = secondary
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["DK Logo.002"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["DK Logo.002"]
    bpy.context.active_object.data.materials[0] = primary
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["Picture Frame"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Picture Frame"]
    bpy.context.active_object.data.materials[0] = secondary
    bpy.context.active_object.data.materials[1] = primary
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["Player Name"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["Player Name"]
    if team == "Los Angeles Dodgers":
        bpy.context.active_object.data.materials[0] = primary
    else:
        bpy.context.active_object.data.materials[0] = bpy.data.materials.get("Baltimore Orioles White")
    bpy.ops.object.select_all(action='DESELECT')

    bpy.data.objects["MLB Logo.001"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["MLB Logo.001"]
    bpy.context.active_object.data.materials[1] = secondary
    bpy.context.active_object.data.materials[2] = primary
    bpy.ops.object.select_all(action='DESELECT')

    # Update displayed distance value countdown
    keyframe = 976
    node_group = bpy.data.node_groups["Geometry Nodes.001"]
    integer_node = node_group.nodes["Value to String"]
    integer_node.inputs['Value'].default_value = int(distance)
    integer_node.inputs['Value'].keyframe_insert(data_path="default_value", frame=keyframe)
    # break

    # Update bat path image based on bat head/handle coordinates
    # Use home plate orientation to determine whether previous hitter was LHH or RHH and update accordingly
    bpy.data.objects["Homeplate"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Homeplate']
    obj = bpy.context.active_object
    if abs(round(obj.rotation_euler[2], 2)) == 3.14:
        prevHitterBatSide = 'R'
    elif round(obj.rotation_euler[2]) == 0:
        prevHitterBatSide = 'L'
    else:
        print("Home error")
        print(obj.rotation_euler[2])
        break

    # Update HP orientation for current batter
    if hitterBatSide == 'R':
        obj.rotation_euler[2] = math.radians(180)
    else:
        obj.rotation_euler[2] = math.radians(0)

    # Loop through bat objects to update swing visual to match bat tracking, highlighting point of contact
    bat_path_collection = bpy.data.collections.get("Baseball Bat Path Mesh")

    for idex, obj in enumerate(bat_path_collection.objects):
        if idex >= 1 and idex < len(batHeadCoordinates):
            obj.data.materials[0] = bpy.data.materials.get("Baltimore Orioles White")
            pos1 = batHeadCoordinates[idex - 1]
            pos2 = batHandleCoordinates[idex - 1]
            x1, y1, z1, timeStamp = pos1['x'], pos1['y'], pos1['z'], pos1['timeStamp']
            timeStampDT = datetime.strptime(timeStamp, "%Y-%m-%dT%H:%M:%S.%fZ")
            timeStamp = timeStampDT.time()
            if idex > 3:
                prevTS = batHeadCoordinates[idex - 2]['timeStamp']
                prevTSDT = datetime.strptime(prevTS, "%Y-%m-%dT%H:%M:%S.%fZ")
                prevTS = prevTSDT.time()
                if contactTime >= prevTS and contactTime <= timeStamp:
                    if team == "Los Angeles Dodgers":
                        obj.data.materials[0] = primary
                    else:
                        obj.data.materials[0] = secondary
            x2, y2, z2 = pos2['x'], pos2['y'], pos2['z']
            dx = x2 - x1
            dy = y2 - y1
            dz = z2 - z1
            dist = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
            location = (dx / 2 + x1 + 10.2, dy / 2 + y1 + 22.4, dz / 2 + z1 + 16.85)
            obj.location = location
            z_axis = obj.rotation_euler[2]
            if prevHitterBatSide != hitterBatSide:
                obj.rotation_euler[2] = -z_axis  # Reverse z-axis of bats if previous hitter not the same handedness
        else:
            # Hide extra bats
            obj.hide_viewport = True
            obj.hide_render = True
            if obj.animation_data:
                obj.animation_data_clear()

    # Render scene
    bpy.context.scene.frame_start = 1
    end_frame = 1340
    bpy.context.scene.frame_end = end_frame
    print("Loop complete")

    output_dir = os.path.join(os.path.dirname(__file__), "media_output_samples")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"blender_demo_{idx}.mp4")
    bpy.context.scene.render.filepath = output_path
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    bpy.context.view_layer.update()
    bpy.context.scene.eevee.taa_samples = 32
    bpy.context.scene.render.use_persistent_data = True
    bpy.context.scene.render.use_overwrite = False
    bpy.context.scene.eevee.use_gtao = False
    bpy.context.view_layer.objects.active = None

    bpy.ops.render.render(animation=True, write_still=False, use_viewport=True)
    while not render_complete:
        time.sleep(20)

bpy.app.handlers.render_complete.remove(render_complete_handler)
