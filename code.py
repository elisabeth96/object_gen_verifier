from manifold3d import *
import numpy as np

def create_object():
    # Create a cube scaled to correct size
    cube = Manifold.cube((0.4, 0.4, 0.4))
    
    # Create a sphere with more segments to make it rounder
    set_circular_segments(32)  # Increased segments for smoother appearance
    sphere = Manifold.sphere(0.15)  # Reduced sphere size
    
    # Position the sphere relative to the cube
    sphere = sphere.translate((-0.3, 0, 0))
    
    # Move the cube to match target position
    cube = cube.translate((0.4, 0, 0))
    
    # Combine the shapes
    result = cube + sphere
    
    return result