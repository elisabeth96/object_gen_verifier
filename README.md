# 3D Object Generator from Images

This script uses Claude Sonnet to generate 3D objects based on 6 images showing different sides of an object, and creates them using the Manifold Python library.

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set your Anthropic API key as an environment variable:
   ```
   export ANTHROPIC_API_KEY="your-api-key"
   ```

## Usage

Run the script with 6 images showing different sides of the object:

```
python generate_objects.py \
  --front front.jpg \
  --back back.jpg \
  --left left.jpg \
  --right right.jpg \
  --top top.jpg \
  --bottom bottom.jpg
```

Optional arguments:
- `--output-dir`: Directory to save the generated objects (default: "generated_objects")

## Input Requirements

- You must provide exactly 6 images, one for each side of the object (front, back, left, right, top, bottom)
- Images should be clear and well-lit
- The object should be centered in each image
- Consistent background and lighting across all images will improve results
- Supported image formats include JPG, PNG, and other common formats

## Output

The script generates the following files for each object:
- `.obj` file: 3D object in OBJ format
- `.stl` file: 3D object in STL format
- `_metadata.json`: JSON file containing metadata about the object

## Example

```
python generate_objects.py \
  --front chair_front.jpg \
  --back chair_back.jpg \
  --left chair_left.jpg \
  --right chair_right.jpg \
  --top chair_top.jpg \
  --bottom chair_bottom.jpg \
  --output-dir "my_objects"
```

## How It Works

1. The script sends your 6 images to Claude Sonnet, which analyzes them to understand the 3D structure.
2. Claude generates a 3D mesh description with vertices and faces based on the visual information.
3. The Manifold library is used to create a valid 3D object from this description.
4. The object is saved in multiple formats for use in 3D modeling software or 3D printing.

## Tips for Best Results

- Use consistent lighting across all images
- Ensure the object is clearly visible against the background
- Capture images from directly perpendicular to each face
- Maintain the same distance from the object in all images
- Include the entire object in each frame

## Requirements

- Python 3.7+
- Anthropic API key (Claude 3 Sonnet)
- Internet connection 