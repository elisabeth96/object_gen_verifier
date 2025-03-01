import os
import sys
import numpy as np
import trimesh
import polyscope as ps
import polyscope.imgui as imgui

def ensure_dir(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def render_mesh_views(mesh_path, object_name):
    """
    Load a mesh and render 6 views from different perspectives.
    
    Args:
        mesh_path: Path to the mesh file
        object_name: Name of the object (used for output directory)
    """
    # Create output directory
    output_dir = os.path.join("objects", object_name, "images")
    ensure_dir(output_dir)
    
    # Load mesh using trimesh
    mesh_trimesh = trimesh.load(mesh_path)
    vertices = np.array(mesh_trimesh.vertices, dtype=np.float64)
    faces = np.array(mesh_trimesh.faces, dtype=np.int32)

    # Center the mesh at origin
    center = np.mean(vertices, axis=0)
    vertices = vertices - center

    # Scale to unit size
    max_dim = np.max(vertices.max(axis=0) - vertices.min(axis=0))
    vertices = vertices / max_dim
    
    # Register the mesh
    mesh = ps.register_surface_mesh("mesh", vertices, faces)
    #mesh.set_material("clay")
    
    # Set default view options
    ps.set_ground_plane_mode("none")
    ps.set_screenshot_extension(".jpg")
    
    # Define the 6 camera views (positive and negative directions along each axis)
    views = {
        "pos_x": ([3.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]),
        "neg_x": ([-3.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]), 
        "pos_y": ([0.0, 3.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]),
        "neg_y": ([0.0, -3.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]),
        "pos_z": ([0.0, 0.0, 3.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]),
        "neg_z": ([0.0, 0.0, -3.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0])
    }
    
    # Render and save images for each view
    for view_name, (camera_pos, camera_target, up_dir) in views.items():
        # Set camera position
        ps.look_at_dir(camera_pos, camera_target, up_dir)
        #ps.set_up_dir(up_dir)
        
        # Center and scale the view
        #ps.reset_camera_to_home_view()
        
        # Render and save the image
        output_path = os.path.join(output_dir, f"{view_name}.jpg")
        ps.screenshot(output_path)
        print(f"Saved view {view_name} to {output_path}")
    
    print(f"All 6 views of {object_name} have been rendered and saved to {output_dir}")

def process_all_objects():
    """
    Iterate over all objects in the 'objects' directory and render views for each mesh.
    """
    ps.init()

    # Create coordinate axes as curve networks
    # X axis (red)
    x_nodes = np.array([[0, 0, 0], [1, 0, 0]])
    x_edges = np.array([[0, 1]])
    x_network = ps.register_curve_network("x_axis", x_nodes, x_edges)
    x_network.set_color((1, 0, 0)) # Red
    
    # Y axis (green) 
    y_nodes = np.array([[0, 0, 0], [0, 1, 0]])
    y_edges = np.array([[0, 1]])
    y_network = ps.register_curve_network("y_axis", y_nodes, y_edges)
    y_network.set_color((0, 1, 0)) # Green
    
    # Z axis (blue)
    z_nodes = np.array([[0, 0, 0], [0, 0, 1]])
    z_edges = np.array([[0, 1]])
    z_network = ps.register_curve_network("z_axis", z_nodes, z_edges)
    z_network.set_color((0, 0, 1)) # Blue

    objects_dir = "objects"
    
    # Get all object directories
    object_dirs = [d for d in os.listdir(objects_dir) 
                  if os.path.isdir(os.path.join(objects_dir, d)) and not d.startswith('.')]
    
    print(f"Found {len(object_dirs)} objects to process")
    
    for object_name in object_dirs:
        mesh_dir = os.path.join(objects_dir, object_name, "mesh")
        if not os.path.exists(mesh_dir):
            print(f"Skipping {object_name}: No mesh directory found")
            continue
        
        # Find the mesh file (should be named object_name.stl)
        mesh_path = os.path.join(mesh_dir, f"{object_name}.stl")
        if not os.path.exists(mesh_path):
            print(f"Skipping {object_name}: No mesh file found at {mesh_path}")
            continue
        
        print(f"Processing {object_name}...")
        render_mesh_views(mesh_path, object_name)
        break

def main():
    process_all_objects()

if __name__ == "__main__":
    main()
