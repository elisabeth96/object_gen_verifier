# 3D Coordinate Axes with Rectangular Frames
from manifold3d import *
import numpy as np
import polyscope as ps
import render_image
import os
from code import create_object

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