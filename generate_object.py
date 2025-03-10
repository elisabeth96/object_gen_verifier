import os
import json
import time
import argparse
import base64
from typing import List, Dict, Any, Optional
import anthropic
import manifold3d
from manifold3d import *
import numpy as np
from PIL import Image
import re
import render_image
import execute_code
import polyscope as ps
import trimesh
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

def clean_code_from_markdown(text: str) -> str:
    """
    Remove markdown code block formatting from the text if present.
    
    Args:
        text: The text that might contain markdown code blocks
        
    Returns:
        Cleaned code without markdown formatting
    """
    # Check if the text is wrapped in markdown code blocks
    code_block_pattern = r'^```(?:python)?\s*([\s\S]*?)```\s*$'
    match = re.match(code_block_pattern, text.strip())
    
    if match:
        # Return just the code inside the code block
        return match.group(1).strip()
    
    # If no markdown formatting detected, return the original text
    return text

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def make_code_edit(input_code, target_dir, current_dir) -> str:
    # Read Manifold documentation from docs.txt
    try:
        with open("example.txt", "r") as f:
            manifold_example = f.read().strip()
    except FileNotFoundError:
        raise ValueError("example.txt file not found")
    except Exception as e:
        raise ValueError(f"Error reading documentation: {e}")

    
    system_prompt = f"""
    You are an expert in 3D modeling and 3D understanding. You will be given 6 images:
    - 3 images showing the target object from different views (front, top, right)
    - 3 images showing the current result of running the existing code from the same views
    All images contain the coordinate axes for reference. The coordinate axes
    are not part of the target or current result, they are only provided for context.
    
    You will also be given the current Python code that attempts to create this 3D object.
    
    Your task is to suggest an edit to the existing code to make the result closer to the target object shown in the images. 
    
    The edit should be a change such as:
    - Scaling an existing primitive
    - Rotating an existing primitive
    - Moving an existing primitive
    - Adding a new primitive and unioning it with the current result
    - Subtracting a primitive from the current result
    - Modifying parameters of an existing primitive
    - Changing a CSG operation
    
    Return ONLY the complete, updated Python code. Do not include any JSON, markdown formatting, or explanations.
    
    The code should:
    1. Define a function named 'create_object()' that returns the final Manifold object
    2. Use Manifold CSG operations (not raw mesh data with vertices and faces)
    
    Here's an example of how to use the Manifold library. Only use the functions and operations that appear in this example, and only use them in the exact form as they are used in the example. You can change the parameters of the functions, but don't add additional arguments when calling the function.
    In particular make sure to use the correct arguments for the functions, don't assume that you can add additional arguments when calling the function.
    
    {manifold_example}
    
    Focus on making specific improvements to bring the current result closer to the target object. Use all of the provided images to make the best possible edit. Also make sure the scaling and the positioning relative to the coordinate axes is correct.
    """
    
    # Get the mapping of view names to filenames
    _, label_to_filename = load_images_from_directory(target_dir)
    
    # Prepare the message content with all images
    message_content = []
    
    # Add all target images
    message_content.append({
        "type": "text", 
        "text": f"Target object images (from 3 different views):"
    })
    
    view_labels = ["front", "top", "right"]
    
    for view in view_labels:
        # Add view description
        message_content.append({
            "type": "text", 
            "text": f"Target {view} view:"
        })
        
        # Add the image
        filename = label_to_filename[view]
        image_path = os.path.join(target_dir, filename)
        message_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": f"image/{image_path.split('.')[-1].lower()}",
                "data": encode_image_to_base64(image_path)
            }
        })

    # Add all current result images
    message_content.append({
        "type": "text", 
        "text": f"Current result images (from 3 different views):"
    })
    
    for view in view_labels:
        # Add view description
        message_content.append({
            "type": "text", 
            "text": f"Current {view} view:"
        })
        
        # Add the image
        filename = label_to_filename[view]
        image_path = os.path.join(current_dir, filename)
        message_content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": f"image/{image_path.split('.')[-1].lower()}",
                "data": encode_image_to_base64(image_path)
            }
        })
    
    # Add instruction
    message_content.append({
        "type": "text",
        "text": f"Current code:\n{input_code}"
    })
    
    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            system=system_prompt,
            max_tokens=4000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": message_content}
            ]
        )
        
        response_text = message.content[0].text
        
        # Clean the response to remove any markdown formatting
        cleaned_code = clean_code_from_markdown(response_text)
        
        return cleaned_code
    
    except Exception as e:
        print(f"Error generating object code: {e}")
        raise

def load_images_from_directory(directory_path: str = "objects/100032/images") -> tuple:
    """
    Load images from a directory with standardized naming convention.
    
    Args:
        directory_path: Path to the directory containing the images
        
    Returns:
        Tuple of (image_paths, labels)
    """
    # Define the mapping from filename to view label
    filename_to_label = {
        "pos_x.jpeg": "right",
        #"neg_x.jpeg": "left",
        "pos_y.jpeg": "top",
        #"neg_y.jpeg": "bottom",
        "pos_z.jpeg": "front",
        #"neg_z.jpeg": "back"
    }

    label_to_filename = {
        "right": "pos_x.jpeg",
        "left": "neg_x.jpeg",
        "top": "pos_y.jpeg",
        "bottom": "neg_y.jpeg",
        "front": "pos_z.jpeg",
        "back": "neg_z.jpeg"
    }

    # Check if directory exists
    if not os.path.exists(directory_path):
        raise ValueError(f"Image directory not found: {directory_path}")
    
    # Get all image paths and their corresponding labels
    image_paths = []
    labels = []
    
    for filename, label in filename_to_label.items():
        file_path = os.path.join(directory_path, filename)
        if not os.path.exists(file_path):
            raise ValueError(f"Required image not found: {file_path}")
        
        image_paths.append(file_path)
        labels.append(label)
    
    return image_paths, label_to_filename

def main():

    target_dir = "objects/sphere_cube/images"
    target_obj = trimesh.load("objects/sphere_cube/sphere_cube.obj")
    target_vertices = np.array(target_obj.vertices, dtype=np.float64)
    target_faces = np.array(target_obj.faces, dtype=np.int32)
    mm = Mesh(target_vertices, target_faces)
    target = Manifold(mm)
    target_volume = target.volume()

    try:
        # Read existing code from code.py
        with open("initial_code.py", "r") as f:
            code = f.read()
        # Write the initial code to code.py
        with open("code.py", "w") as f:
            f.write(code)
        
        max_iterations = 60  # Set a maximum number of iterations to prevent infinite loops
        for iteration in range(max_iterations):
            print(f"\nIteration {iteration + 1}/{max_iterations}")
            
            # Read the current code from code.py
            with open("code.py", "r") as f:
                code = f.read()
            
            # Execute the code to create the Manifold object
            manifold_obj = execute_code.execute_code(code)
            mesh = manifold_obj.to_mesh()
            vertices = np.array(mesh.vert_properties)
            faces = np.array(mesh.tri_verts)
            
            # Render the current object
            ps.init()
            render_image.create_coordinate_axes()
            current_dir = render_image.render_mesh_views_from_arrays(vertices, faces, "temp_" + str(iteration))
           

            # Generate the object code from images
            new_code = make_code_edit(code, target_dir, current_dir)
            
            # Check if the code has changed
            if new_code == code:
                print("Code has converged - no further changes needed.")
                break
                
            # Update the code for the next iteration
            code = new_code
            print(f"Generated new code: {code}")
            
            # Write the updated code to code.py
            with open("code.py", "w") as f:
                f.write(code)
            print(f"Updated code written to code.py")

            symmetric_difference = (manifold_obj - target) + (target - manifold_obj)
            error = symmetric_difference.volume()
            print(f"Created Manifold object with volume {manifold_obj.volume()}")
            print(f"Error: {error}")
            # Write volumes to file
            with open("objects/temp_" + str(iteration) + "/volumes.txt", "w") as f:
                f.write(f"Created object volume: {manifold_obj.volume()}\n")
                f.write(f"Target object volume: {target_volume}\n")
                f.write(f"Error: {error}\n")

    except Exception as e:
        print(f"Error: {e}")

        if iteration == max_iterations - 1:
            print("Reached maximum number of iterations.")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
