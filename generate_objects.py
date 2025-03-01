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
    """
    Encode an image to base64.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_object_code_from_images(image_paths: List[str], labels: List[str]) -> str:
    if len(image_paths) != 6 or len(labels) != 6:
        raise ValueError("Exactly 6 images and 6 labels are required")
    
    # Read Manifold documentation from docs.txt
    try:
        with open("example.txt", "r") as f:
            manifold_example = f.read().strip()
    except FileNotFoundError:
        raise ValueError("example.txt file not found")
    except Exception as e:
        raise ValueError(f"Error reading documentation: {e}")

    
    system_prompt = f"""
    You are an expert in 3D modeling and 3D understanding. You will be given 7 images:
    - 6 images showing different sides (front, back, left, right, top, bottom) of a target object
    - 1 image showing the current result of running the existing code
    
    You will also be given the current Python code that attempts to create this 3D object.
    
    Your task is to suggest a SINGLE, SMALL EDIT to the existing code to make the result closer to the target object shown in the first 6 images.
    
    The edit should be an atomic change such as:
    - Fixing a transformation (position, rotation, scale)
    - Adding a new primitive and unioning it with the current result
    - Subtracting a primitive from the current result
    - Modifying parameters of an existing primitive
    - Changing a CSG operation
    
    Return ONLY the complete, updated Python code. Do not include any JSON, markdown formatting, or explanations.
    
    The code should:
    1. Define a function named 'create_object()' that returns the final Manifold object
    2. Include a descriptive name for the object as a comment at the top
    3. Use Manifold CSG operations (not raw mesh data with vertices and faces)
    
    Here's an example of how to use the Manifold library:
    
    {manifold_example}
    
    Focus on making one specific improvement to bring the current result closer to the target object.
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
        "text": "Based on these 6 images, generate Python code using the Manifold CSG library to create this 3D object."
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

def execute_object_code(code) -> Manifold:
    """
    Execute the generated Python code to create a Manifold object.
    
    Args:
        object_data: Dictionary containing the Python code
        
    Returns:
        Manifold object
    """
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
    
    return image_paths, labels

def main():
    try:
        # Load images from the directory
        image_paths, labels = load_images_from_directory()
        
        print("Generating 3D object from 6 images...")
        
        # Generate the object code from images
        code = generate_object_code_from_images(image_paths, labels)
        print(f"Generated code for: {code}")
        
        # Execute the code to create the Manifold object
        manifold_obj = execute_object_code(code)
        print(f"Created Manifold object with volume {manifold_obj.volume()}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
