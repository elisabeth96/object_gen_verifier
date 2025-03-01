from manifold3d import *
import numpy as np
import render_image
import polyscope as ps
import os

def create_complex_composition():
    # Create 3 spheres with similar radii
    sphere1 = Manifold.sphere(1.0).translate((-4, 0, 0))
    sphere2 = Manifold.sphere(1.0).translate((0, 3, 0))
    sphere3 = Manifold.sphere(1.0).translate((4, -2, 0))
    
    # Create 2 cubes with dimensions that give them similar volume to the spheres
    # Sphere volume = 4/3 * π * r³ ≈ 4.19 for r=1
    # Cube with side 1.6 has volume = 1.6³ ≈ 4.1
    cube1 = Manifold.cube((1.6, 1.6, 1.6)).translate((-2, -2, 0))
    cube2 = Manifold.cube((1.6, 1.6, 1.6)).translate((2, 1, 0))
    
    # Create 2 cylinders with consistent radius
    # Cylinder 1: connecting sphere1 and cube1
    cylinder1 = Manifold.cylinder(0.5, 2.0, 32).rotate([0, 0, 45]).translate((-3, -1, 0))
    
    # Cylinder 2: connecting cube2 and sphere3
    cylinder2 = Manifold.cylinder(0.5, 2.5, 32).rotate([0, 0, -30]).translate((3, -0.5, 0))
    
    # Combine all shapes into a single manifold
    result = Manifold.compose([sphere1, sphere2, sphere3, cube1, cube2, cylinder1, cylinder2])
    
    # Print some information about the combined shape
    print(f"Number of vertices: {result.num_vert()}")
    print(f"Number of triangles: {result.num_tri()}")
    print(f"Volume: {result.volume()}")
    
    return result

def ensure_dir(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

if __name__ == "__main__":
    # Create the complex composition
    result = create_complex_composition()
    
    # Get mesh data from the manifold object
    mesh = result.to_mesh()
    vertices = np.array(mesh.vert_properties)
    faces = np.array(mesh.tri_verts)
    
    # Write to OBJ file
    ensure_dir('objects/complex_composition')
    with open('objects/complex_composition/output.obj', 'w') as f:
        # Write vertices
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        
        # Write faces (OBJ uses 1-indexed vertices)
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
    
    ps.init()
    render_image.create_coordinate_axes()
    images = render_image.render_mesh_views_from_arrays(vertices, faces, "complex_composition")
    
    print("Created a complex composition of 3 spheres, 2 cubes, and 2 cylinders") 