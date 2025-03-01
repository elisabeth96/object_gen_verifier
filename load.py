import thingi10k
import trimesh
import os

thingi10k.init() # Download the dataset and update cache

# Loop through the first 10 entries in the dataset
for i, entry in enumerate(thingi10k.dataset()):
    if i >= 10:  # Only process the first 10 meshes
        break
        
    file_id = entry['file_id']
    author = entry['author']
    vertices, facets = thingi10k.load_file(entry['file_path'])
    
    # Create a trimesh mesh from vertices and facets
    mesh = trimesh.Trimesh(vertices=vertices, faces=facets)
    
    # Create directory structure: objects/name/mesh/
    object_dir = f'objects/{file_id}/mesh'
    os.makedirs(object_dir, exist_ok=True)
    
    # Save the mesh as STL
    mesh_path = f'{object_dir}/{file_id}.stl'
    mesh.export(mesh_path)
    
    print(f"Saved mesh {i+1}/10: {mesh_path}")

# help(thingi10k) # for more information