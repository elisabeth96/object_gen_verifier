from manifold3d import *
import numpy as np
if not hasattr(Manifold, '__qualname__'):
    Manifold.__qualname__ = 'Manifold'

def create_object():
    # Create the vertical central rod
    central_rod = Manifold.cylinder(0.05, 3).translate((0, 0, 0))
    
    # Create the top row of two rectangles with rounded corners
    top_left = create_rounded_rectangle(0.5, 0.25, 0.05, 0.05).translate((-0.3, 0, 1))
    top_right = create_rounded_rectangle(0.4, 0.25, 0.05, 0.05).translate((0.3, 0, 1))
    
    # Create the bottom row of three rectangles with rounded corners
    bottom_left = create_rounded_rectangle(0.4, 0.7, 0.05, 0.1).translate((-0.5, 0, 0))
    bottom_middle = create_rounded_rectangle(0.4, 0.7, 0.05, 0.1).translate((0, 0, 0))
    bottom_right = create_rounded_rectangle(0.4, 0.7, 0.05, 0.1).translate((0.5, 0, 0))
    
    # Create horizontal rod on right side
    horizontal_rod = Manifold.cylinder(0.02, 1).rotate(90).translate((1, 0, 0))
    
    # Combine all objects
    result = central_rod + top_left + top_right + bottom_left + bottom_middle + bottom_right + horizontal_rod
    
    return result

def create_rounded_rectangle(width, height, thickness, radius):
    # Create a rectangle with rounded corners by unioning cylinders at corners with cuboids
    half_width = width / 2
    half_height = height / 2
    
    # Main body
    body = Manifold.cube((width - 2 * radius, height, thickness)).translate((0, 0, 0))
    body_horizontal = Manifold.cube((width, height - 2 * radius, thickness)).translate((0, 0, 0))
    
    # Corner cylinders
    c1 = Manifold.cylinder(radius, thickness).translate((half_width - radius, half_height - radius, 0))
    c2 = Manifold.cylinder(radius, thickness).translate((-half_width + radius, half_height - radius, 0))
    c3 = Manifold.cylinder(radius, thickness).translate((half_width - radius, -half_height + radius, 0))
    c4 = Manifold.cylinder(radius, thickness).translate((-half_width + radius, -half_height + radius, 0))
    
    # Bottom cutout (semicircle)
    bottom_cutout = Manifold.cylinder(height/4, thickness).translate((0, -half_height, 0))
    
    # Union everything except the bottom cutout
    result = body + body_horizontal + c1 + c2 + c3 + c4
    
    # Subtract the bottom cutout
    result = result - bottom_cutout
    
    return result