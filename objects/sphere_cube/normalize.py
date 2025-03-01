import os
import numpy as np
import igl

def normalize_obj(input_path, output_path=None):
    """
    Load an OBJ file using libigl, normalize it so the longest axis has length 1,
    center it at the origin, and save it back.
    
    Args:
        input_path (str): Path to the input OBJ file
        output_path (str, optional): Path to save the normalized OBJ file.
                                    If None, overwrites the input file.
    """
    if output_path is None:
        output_path = input_path
    
    # Load the mesh using libigl
    v, f = igl.read_triangle_mesh(input_path)
    
    # Get the bounding box dimensions and center
    min_corner = np.min(v, axis=0)
    max_corner = np.max(v, axis=0)
    extents = max_corner - min_corner
    center = (min_corner + max_corner) / 2.0
    
    # Find the longest axis
    max_dimension = np.max(extents)
    
    # Apply the transformations: center and scale
    v_normalized = (v - center) / max_dimension
    
    # Save the normalized mesh
    igl.write_triangle_mesh(output_path, v_normalized, f)
    
    print(f"Normalized OBJ saved to {output_path}")
    print(f"Original dimensions: {extents}")
    print(f"Original center: {center}")
    print(f"Scale factor: {1.0 / max_dimension}")

if __name__ == "__main__":
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the path to sphere_cube.obj
    input_obj = os.path.join(script_dir, "sphere_cube.obj")
    
    # Normalize the OBJ file
    normalize_obj(input_obj)

