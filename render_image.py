import os
import sys
import numpy as np
import trimesh
import polyscope as ps
import polyscope.imgui as imgui

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def render_mesh_views_from_arrays(vertices, faces, object_name):
    output_dir = os.path.join("objects", object_name, "images")
    ensure_dir(output_dir)
    ps.init()
    
    # Convert arrays to the right types if needed
    vertices = np.array(vertices, dtype=np.float64)
    faces = np.array(faces, dtype=np.int32)

    # Register the mesh
    mesh = ps.register_surface_mesh("mesh", vertices, faces)
    mesh.set_color((0.5, 0.5, 0.5))
    
    # Set default view options
    ps.set_ground_plane_mode("none")
    ps.set_screenshot_extension(".jpg")
    
    # Define all 6 camera views (positive and negative directions along each axis)
    views = {
        "pos_x": ([3.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]),  # right view
        "neg_x": ([-3.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]),  # left view
        "pos_y": ([0.0, 3.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]),  # top view
        "neg_y": ([0.0, -3.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0]),  # bottom view
        "pos_z": ([0.0, 0.0, 3.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]),   # front view
        "neg_z": ([0.0, 0.0, -3.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0])   # back view
    }
    
    # Render and save images for each view
    saved_paths = []
    for view_name, (camera_pos, camera_target, up_dir) in views.items():
        # Set camera position
        ps.look_at_dir(camera_pos, camera_target, up_dir)
        
        # Render and save the image
        output_path = os.path.join(output_dir, f"{view_name}.jpeg")
        ps.screenshot(output_path)
        saved_paths.append(output_path)
        print(f"Saved view {view_name} to {output_path}")
    
    print(f"All 6 views of {object_name} have been rendered and saved to {output_dir}")
    return output_dir

def render_mesh_views(mesh_path, object_name):
    # Create output directory
    output_dir = os.path.join("objects", object_name, "images")
    ensure_dir(output_dir)
    
    # Load mesh using trimesh
    mesh_trimesh = trimesh.load(mesh_path)
    vertices = np.array(mesh_trimesh.vertices, dtype=np.float64)
    faces = np.array(mesh_trimesh.faces, dtype=np.int32)

    # Use the new function to render the views
    return render_mesh_views_from_arrays(vertices, faces, object_name, output_dir)

def create_coordinate_axes():
    # X axis (red)
    x_nodes = np.array([[0, 0, 0], [1, 0, 0]])
    x_edges = np.array([[0, 1]])
    x_network = ps.register_curve_network("x_axis", x_nodes, x_edges)
    x_network.set_color((1, 0, 0))  # Red
    
    # Y axis (green) 
    y_nodes = np.array([[0, 0, 0], [0, 1, 0]])
    y_edges = np.array([[0, 1]])
    y_network = ps.register_curve_network("y_axis", y_nodes, y_edges)
    y_network.set_color((0, 1, 0))  # Green
    
    # Z axis (blue)
    z_nodes = np.array([[0, 0, 0], [0, 0, 1]])
    z_edges = np.array([[0, 1]])
    z_network = ps.register_curve_network("z_axis", z_nodes, z_edges)
    z_network.set_color((0, 0, 1))  # Blue

def process_object():
    ps.init()
    ps.set_window_size(256, 256)

    create_coordinate_axes()

    objects_dir = "objects"
    object_name = "complex_composition"
    
    mesh_dir = os.path.join(objects_dir, object_name, "mesh")
    if not os.path.exists(mesh_dir):
        print(f"{object_name}: No mesh directory found")
        return
    
    # Find the mesh file (check for both .stl and .obj extensions)
    stl_path = os.path.join(mesh_dir, f"{object_name}.stl")
    obj_path = os.path.join(mesh_dir, f"{object_name}.obj")
    
    if os.path.exists(stl_path):
        mesh_path = stl_path
    elif os.path.exists(obj_path):
        mesh_path = obj_path
    else:
        print(f"{object_name}: No mesh file found (checked for both .stl and .obj)")
        return
        
    print(f"Processing {object_name}...")
    render_mesh_views(mesh_path, object_name)

def main():
    process_object()

if __name__ == "__main__":
    main()
