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

def generate_object_code_from_images(image_paths: List[str], labels: List[str]) -> Dict[str, Any]:
    """
    Use Claude Sonnet to generate Python code using Manifold CSG library based on 6 images from different sides.
    
    Args:
        image_paths: List of paths to the 6 images (front, back, left, right, top, bottom)
        labels: List of labels for each image (e.g., "front", "back", etc.)
        
    Returns:
        Dictionary containing the object code, name and description
    """
    if len(image_paths) != 6 or len(labels) != 6:
        raise ValueError("Exactly 6 images and 6 labels are required")
    
    system_prompt = """
    You are an expert in 3D modeling and 3D understanding. You will be given 6 images showing different sides 
    (front, back, left, right, top, bottom) of an object. Your task is to generate a Python script that recreates
    the object using the Manifold CSG library.
    
    Return a JSON object with the following structure:
    {
        "code": "# Python code using Manifold CSG library to create the object\\n...",
        "name": "object_name",  # A simple name for the object
        "description": "brief description"  # A brief description of what was generated
    }
    
    The code should use Manifold CSG operations (like cube(), cylinder(), sphere(), boolean operations, etc.) 
    to construct the 3D model. Do not generate raw mesh data with vertices and faces.
    
    Example of good code:
    ```python
    from manifold import Manifold
    
    # Create a simple cup
    def create_cup():
        # Main body - hollow cylinder
        outer = Manifold.cylinder(radius=2.0, height=5.0, circularSegments=32)
        inner = Manifold.cylinder(radius=1.8, height=4.8, circularSegments=32)
        inner = inner.translate([0, 0, 0.2])
        body = outer - inner
        
        # Handle
        handle_ring = Manifold.cylinder(radius=0.5, height=0.3, circularSegments=32)
        handle_ring = handle_ring - Manifold.cylinder(radius=0.3, height=0.3, circularSegments=32)
        handle_ring = handle_ring.rotate([1, 0, 0], 90).translate([3, 0, 2.5])
        
        # Combine parts
        cup = body + handle_ring
        return cup
    
    cup = create_cup()
    ```
    
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
        
        # Extract the JSON from the response
        response_text = message.content[0].text
        # Find JSON content (assuming it's the only JSON in the response)
        try:
            # Try to parse the entire response as JSON first
            object_data = json.loads(response_text)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON from the text
            import re
            json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if json_match:
                object_data = json.loads(json_match.group(1))
            else:
                # Last resort: find anything that looks like JSON
                json_match = re.search(r'{.*}', response_text, re.DOTALL)
                if json_match:
                    object_data = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not extract JSON from the response")
        
        # Validate the object data
        if not all(key in object_data for key in ["code", "name", "description"]):
            raise ValueError("Missing required fields in the generated object data")
        
        return object_data
    
    except Exception as e:
        print(f"Error generating object code: {e}")
        raise

def execute_object_code(object_data: Dict[str, Any]) -> Manifold:
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
            'Manifold': Manifold,
            'np': np
        }
        
        # Extract the function that creates the object
        code = object_data["code"]
        
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

def save_object(manifold_obj: Manifold, object_data: Dict[str, Any], output_dir: str) -> str:
    """
    Save the Manifold object to a file.
    
    Args:
        manifold_obj: Manifold object to save
        object_data: Dictionary containing object metadata
        output_dir: Directory to save the object to
        
    Returns:
        Path to the saved file
    """
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create a filename from the object name
        filename = f"{object_data['name'].replace(' ', '_').lower()}_{int(time.time())}"
        
        # Save as OBJ
        obj_path = os.path.join(output_dir, f"{filename}.obj")
        manifold_obj.export_mesh().write_obj(obj_path)
        
        # Save as STL
        stl_path = os.path.join(output_dir, f"{filename}.stl")
        manifold_obj.export_mesh().write_stl(stl_path)
        
        # Save the Python code
        code_path = os.path.join(output_dir, f"{filename}_code.py")
        with open(code_path, 'w') as f:
            f.write(object_data["code"])
        
        # Save metadata
        metadata_path = os.path.join(output_dir, f"{filename}_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump({
                "name": object_data["name"],
                "description": object_data["description"],
                "timestamp": time.time()
            }, f, indent=2)
        
        return obj_path
    
    except Exception as e:
        print(f"Error saving object: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Generate 3D objects from 6 images using Claude Sonnet and Manifold CSG")
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
        
        # Generate the object code from images
        object_data = generate_object_code_from_images(image_paths, labels)
        print(f"Generated code for: {object_data['name']}")
        
        # Execute the code to create the Manifold object
        manifold_obj = execute_object_code(object_data)
        print(f"Created Manifold object with {manifold_obj.genus()} genus")
        
        # Save the object
        output_path = save_object(manifold_obj, object_data, args.output_dir)
        print(f"Saved object to: {output_path}")
        print(f"Object description: {object_data['description']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
