#!/usr/bin/env python3
import os
import json
import time
import argparse
import base64
from typing import List, Dict, Any, Optional
import anthropic
import manifold
import numpy as np
from manifold.mesh import Mesh
from manifold.manifold import Manifold
from PIL import Image

# Read API key from file
try:
    with open("api_key.txt", "r") as f:
        ANTHROPIC_API_KEY = f.read().strip()
    if not ANTHROPIC_API_KEY:
        raise ValueError("API key file is empty")
except FileNotFoundError:
    raise ValueError("api_key.txt file not found")
except Exception as e:
    raise ValueError(f"Error reading API key: {e}")

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image to base64.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_object_from_images(image_paths: List[str], labels: List[str]) -> Dict[str, Any]:
    """
    Use Claude Sonnet to generate a 3D object description based on 6 images from different sides.
    
    Args:
        image_paths: List of paths to the 6 images (front, back, left, right, top, bottom)
        labels: List of labels for each image (e.g., "front", "back", etc.)
        
    Returns:
        Dictionary containing the object description with vertices and faces
    """
    if len(image_paths) != 6 or len(labels) != 6:
        raise ValueError("Exactly 6 images and 6 labels are required")
    
    system_prompt = """
    You are an expert in 3D modeling and 3d understanding. You will be given 6 images showing different sides 
    (front, back, left, right, top, bottom) of an object. Your task is to generate a python script that recreates
    the object using the manifold csg library.
    
    Return ONLY a JSON object with the following structure:
    {
        "vertices": [[x1, y1, z1], [x2, y2, z2], ...],  # List of 3D coordinates for vertices
        "faces": [[v1, v2, v3], ...],  # List of vertex indices forming triangular faces
        "name": "object_name",  # A simple name for the object
        "description": "brief description"  # A brief description of what was generated
    }
    
    Keep the mesh relatively simple (20-100 vertices) but recognizable.
    Ensure all faces are triangles and use proper indexing (0-based).
    Carefully analyze all 6 images to create an accurate 3D representation.
    """
    
    # Prepare the message content with all images
    message_content = []
    
    for i, (image_path, label) in enumerate(zip(image_paths, labels)):
        # Add image description
        message_content.append({
            "type": "text", 
            "text": f"Image {i+1} ({label}):"
        })
        
        # Add the image
        message_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": f"image/{image_path.split('.')[-1].lower()}",
                "data": encode_image_to_base64(image_path)
            }
        })
    
    # Add final instruction
    message_content.append({
        "type": "text",
        "text": "Based on these 6 images, generate a 3D mesh representation of the object."
    })
    
    try:
        message = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            system=system_prompt,
            max_tokens=4000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": message_content}
            ]
        )
        
        # Extract the JSON from the response
        response_text = message.content[0].text
        # Find JSON content (assuming it's the only JSON in the response)
        try:
            # Try to parse the entire response as JSON first
            mesh_data = json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the text
            import re
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                mesh_data = json.loads(json_match.group(1))
            else:
                # Last resort: find anything that looks like JSON
                json_match = re.search(r'{.*}', response_text, re.DOTALL)
                if json_match:
                    mesh_data = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not extract JSON from the response")
        
        # Validate the mesh data
        if not all(key in mesh_data for key in ["vertices", "faces", "name", "description"]):
            raise ValueError("Missing required fields in the generated mesh data")
        
        return mesh_data
    
    except Exception as e:
        print(f"Error generating object description: {e}")
        raise

def create_manifold_object(mesh_data: Dict[str, Any]) -> Manifold:
    """
    Create a Manifold object from the mesh data.
    
    Args:
        mesh_data: Dictionary containing vertices and faces
        
    Returns:
        Manifold object
    """
    try:
        # Convert the mesh data to numpy arrays
        vertices = np.array(mesh_data["vertices"], dtype=np.float32)
        faces = np.array(mesh_data["faces"], dtype=np.int32)
        
        # Create a Mesh object
        mesh = Mesh(vertices, faces)
        
        # Create a Manifold object from the mesh
        manifold_obj = Manifold(mesh)
        
        # Ensure the manifold is valid
        if not manifold_obj.is_empty():
            # Fix any issues with the manifold
            manifold_obj = manifold_obj.fix()
        
        return manifold_obj
    
    except Exception as e:
        print(f"Error creating Manifold object: {e}")
        raise

def save_object(manifold_obj: Manifold, mesh_data: Dict[str, Any], output_dir: str) -> str:
    """
    Save the Manifold object to a file.
    
    Args:
        manifold_obj: Manifold object to save
        mesh_data: Dictionary containing object metadata
        output_dir: Directory to save the object to
        
    Returns:
        Path to the saved file
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a filename from the object name
        filename = f"{mesh_data['name'].replace(' ', '_').lower()}_{int(time.time())}"
        
        # Save as OBJ
        obj_path = os.path.join(output_dir, f"{filename}.obj")
        manifold_obj.export_mesh().write_obj(obj_path)
        
        # Save as STL
        stl_path = os.path.join(output_dir, f"{filename}.stl")
        manifold_obj.export_mesh().write_stl(stl_path)
        
        # Save metadata
        metadata_path = os.path.join(output_dir, f"{filename}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump({
                "name": mesh_data["name"],
                "description": mesh_data["description"],
                "vertex_count": len(mesh_data["vertices"]),
                "face_count": len(mesh_data["faces"]),
                "timestamp": time.time()
            }, f, indent=2)
        
        return obj_path
    
    except Exception as e:
        print(f"Error saving object: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Generate 3D objects from 6 images using Claude Sonnet and Manifold")
    parser.add_argument("--front", type=str, required=True, help="Path to the front view image")
    parser.add_argument("--back", type=str, required=True, help="Path to the back view image")
    parser.add_argument("--left", type=str, required=True, help="Path to the left view image")
    parser.add_argument("--right", type=str, required=True, help="Path to the right view image")
    parser.add_argument("--top", type=str, required=True, help="Path to the top view image")
    parser.add_argument("--bottom", type=str, required=True, help="Path to the bottom view image")
    parser.add_argument("--output-dir", type=str, default="generated_objects", 
                        help="Directory to save the generated objects")
    
    args = parser.parse_args()
    
    try:
        print("Generating 3D object from 6 images...")
        
        # Collect all image paths and labels
        image_paths = [args.front, args.back, args.left, args.right, args.top, args.bottom]
        labels = ["front", "back", "left", "right", "top", "bottom"]
        
        # Verify all images exist
        for path in image_paths:
            if not os.path.exists(path):
                raise ValueError(f"Image file not found: {path}")
        
        # Generate the object description from images
        mesh_data = generate_object_from_images(image_paths, labels)
        print(f"Generated description for: {mesh_data['name']}")
        
        # Create the Manifold object
        manifold_obj = create_manifold_object(mesh_data)
        print(f"Created Manifold object with {manifold_obj.genus()} genus")
        
        # Save the object
        output_path = save_object(manifold_obj, mesh_data, args.output_dir)
        print(f"Saved object to: {output_path}")
        print(f"Object description: {mesh_data['description']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
