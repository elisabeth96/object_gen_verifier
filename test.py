# 3D Coordinate Axes with Rectangular Frames
from manifold3d import *
import numpy as np
import polyscope as ps
import render_image
import os
def create_object():
    # Set parameters for smoother circles
    set_circular_segments(32)
    
    # Create vertical axis (blue/green in images)
    vertical_axis = Manifold.cylinder(0.05, 8).translate([0, 0, -4])
    
    # Create horizontal axis (green in images)
    horizontal_axis = Manifold.cylinder(0.05, 8).rotate([0, 0, 90]).translate([0, 0, 0])
    
    # Create the red segment that extends from the horizontal axis
    red_segment = Manifold.cylinder(0.05, 2).rotate([0, 0, 90]).translate([4, 0, 0])
    
    # Create rectangular frames
    # Bottom row frames (3 frames)
    frame1 = create_rounded_frame(1.5, 2.2, 0.1, 0.2).translate([-2.5, 0, -2])
    frame2 = create_rounded_frame(1.2, 2.0, 0.1, 0.2).translate([0, 0, -2])
    frame3 = create_rounded_frame(1.5, 2.2, 0.1, 0.2).translate([2.5, 0, -2])
    
    # Top row frames (2 frames)
    frame4 = create_rounded_frame(1.2, 0.8, 0.1, 0.1).translate([-1.5, 0, 1])
    frame5 = create_rounded_frame(1.2, 0.8, 0.1, 0.1).translate([1.5, 0, 1])
    
    # Combine all objects
    result = vertical_axis + horizontal_axis + red_segment + frame1 + frame2 + frame3 + frame4 + frame5
    
    return result

def create_rounded_frame(width, height, thickness, corner_radius):
    # Create outer and inner rounded rectangles
    outer = create_rounded_rectangle(width, height, corner_radius)
    inner = create_rounded_rectangle(width - 2*thickness, height - 2*thickness, max(0.01, corner_radius - thickness))
    
    # Extrude and subtract to create the frame
    outer_3d = Manifold.extrude(outer, thickness)
    inner_3d = Manifold.extrude(inner, thickness * 1.1).translate([0, 0, -thickness * 0.05])
    
    # Create the frame by subtracting the inner volume from the outer
    frame = outer_3d - inner_3d
    
    return frame

def create_rounded_rectangle(width, height, radius):
    # Create a rounded rectangle as a cross-section
    rect = CrossSection.square([width - 2*radius, height - 2*radius])
    
    # Add rounded corners by adding circles at the corners
    circles = CrossSection()
    for x in [-width/2 + radius, width/2 - radius]:
        for y in [-height/2 + radius, height/2 - radius]:
            circles = circles + CrossSection.circle(radius).translate([x, y])
    
    # Add rectangles to connect the circles
    rect_h = CrossSection.square([width - 2*radius, 2*radius]).translate([0, -height/2 + radius])
    rect_h2 = CrossSection.square([width - 2*radius, 2*radius]).translate([0, height/2 - radius])
    rect_v = CrossSection.square([2*radius, height - 2*radius]).translate([-width/2 + radius, 0])
    rect_v2 = CrossSection.square([2*radius, height - 2*radius]).translate([width/2 - radius, 0])
    
    # Combine all shapes
    rounded_rect = rect + circles + rect_h + rect_h2 + rect_v + rect_v2
    
    # Center the rectangle
    return rounded_rect.translate([-width/2, -height/2])

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_to_obj():
    
    # Create the 3D object
    obj = create_object()
    
    # Get mesh data from the manifold object
    mesh = obj.to_mesh()
    vertices = np.array(mesh.vert_properties)
    faces = np.array(mesh.tri_verts)
    
    # Write to OBJ file
    ensure_dir('objects/temp')
    with open('objects/temp/output.obj', 'w') as f:
        # Write vertices
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        
        # Write faces (OBJ uses 1-indexed vertices)
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
    
    print(f"Mesh written to output.obj with {len(vertices)} vertices and {len(faces)} faces")
    ps.init()
    images = render_image.render_mesh_views_from_arrays(vertices, faces, "temp")

if __name__ == "__main__":
    write_to_obj()