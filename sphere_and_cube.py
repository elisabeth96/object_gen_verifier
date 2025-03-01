from manifold3d import *
import numpy as np
import render_image
import polyscope as ps
import os
def create_sphere_and_cube():
    # Create a sphere with radius 1
    sphere = Manifold.sphere(1)
    
    # Create a cube with dimensions 2x2x2
    cube = Manifold.cube((2, 2, 2))
    
    # Position the cube next to the sphere (3 units away on x-axis)
    # This ensures they don't overlap and are clearly separated
    cube = cube.translate((4, 0, 0))
    
    # Combine the two shapes into a single manifold
    result = Manifold.compose([sphere, cube])
    
    # Export to a mesh for visualization
    mesh = result.to_mesh()
    
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
    # Create the shapes
    result = create_sphere_and_cube()
    

    # Get mesh data from the manifold object
    mesh = result.to_mesh()
    vertices = np.array(mesh.vert_properties)
    faces = np.array(mesh.tri_verts)
    
    # Write to OBJ file
    ensure_dir('objects/sphere_cube')
    with open('objects/sphere_cube/output.obj', 'w') as f:
        # Write vertices
        for v in vertices:
            f.write(f"v {v[0]} {v[1]} {v[2]}\n")
        
        # Write faces (OBJ uses 1-indexed vertices)
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
    ps.init()
    render_image.create_coordinate_axes()
    images = render_image.render_mesh_views_from_arrays(vertices, faces, "sphere_cube")
    # You can export the result to a file format of your choice
    # or use it for further operations
    print("Created a sphere and cube positioned next to each other") 