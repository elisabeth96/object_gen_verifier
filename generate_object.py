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
    You are an expert in 3D modeling and 3D understanding. You will be given 2 images:
    - 1 image showing the target object
    - 1 image showing the current result of running the existing code
    
    You will also be given the current Python code that attempts to create this 3D object.
    
    Your task is to suggest a SINGLE, SMALL EDIT to the existing code to make the result closer to the target object shown in the first image.
    
    The edit should be an atomic change such as:
    - Fixing a transformation (position, rotation, scale)
    - Adding a new primitive and unioning it with the current result
    - Subtracting a primitive from the current result
    - Modifying parameters of an existing primitive
    - Changing a CSG operation
    
    Return ONLY the complete, updated Python code. Do not include any JSON, markdown formatting, or explanations.
    
    The code should:
    1. Define a function named 'create_object()' that returns the final Manifold object
    2. Use Manifold CSG operations (not raw mesh data with vertices and faces)
    
    Here's an example of how to use the Manifold library:
    
    {manifold_example}
    
    Focus on making one specific improvement to bring the current result closer to the target object.
    """
    
    # Prepare the message content with all images
    message_content = []
    
    # first do target image, for now we use the first image in the list
    # Add image description
    message_content.append({
        "type": "text", 
        "text": f"Image 1 (target):"
    })
    
    # Add the image
    image_path = os.path.join(target_dir, "pos_z.jpeg")
    message_content.append({
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": f"image/{image_path.split('.')[-1].lower()}",
            "data": encode_image_to_base64(image_path)
        }
    })

    # Add current result image
    message_content.append({
        "type": "text", 
        "text": f"Image 2 (current result):"
    })
    
    # Add the image
    image_path = os.path.join(current_dir, "pos_z.jpeg")
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
            model="claude-3-7-sonnet-20250219",
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

def execute_code(code) -> Manifold:
    try:
        # Create a local namespace to execute the code
        local_namespace = {
            'manifold3d': manifold3d,
            'np': np
        }
        
        # Execute the code in the local namespace
        exec(code, globals(), local_namespace)
        
        # Find the created manifold object in the namespace
        # This assumes the code creates a variable that is a Manifold object
        manifold_obj = None
        for var_name, var_value in local_namespace.items():
            if isinstance(var_value, Manifold) and var_name != 'Manifold':
                manifold_obj = var_value
                break
        
        # If no manifold object was found, try to find a function that returns a manifold
        if manifold_obj is None:
            for var_name, var_value in local_namespace.items():
                if callable(var_value) and var_name not in ['Manifold']:
                    try:
                        result = var_value()
                        if isinstance(result, Manifold):
                            manifold_obj = result
                            break
                    except:
                        continue
        
        if manifold_obj is None:
            raise ValueError("Could not find a Manifold object in the executed code")
        
        # Ensure the manifold is valid
        if not manifold_obj.is_empty():
            # Fix any issues with the manifold
            manifold_obj = manifold_obj.fix()
        
        return manifold_obj
    
    except Exception as e:
        print(f"Error executing object code: {e}")
        print(f"Generated code:\n{code}")
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
        "neg_x.jpeg": "left",
        "pos_y.jpeg": "top",
        "neg_y.jpeg": "bottom",
        "pos_z.jpeg": "front",
        "neg_z.jpeg": "back"
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

    target_dir = "objects/100032/images"

    try:
        # Read existing code from code.py
        with open("code.py", "r") as f:
            code = f.read()

        manifold_obj = execute_code(code)
        mesh = manifold_obj.to_mesh()
        vertices = np.array(mesh.vert_properties)
        faces = np.array(mesh.tri_verts)

        current_dir = render_image.render_mesh_views_from_arrays(vertices, faces, "temp") 
        # Generate the object code from images
        code = make_code_edit(code, target_dir, current_dir)
        print(f"Generated code for: {code}")
        
        # Write the updated code to code.py
        with open("code.py", "w") as f:
            f.write(code)
        print(f"Updated code written to code.py")
        
        # Execute the code to create the Manifold object
        print(f"Created Manifold object with volume {manifold_obj.volume()}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
