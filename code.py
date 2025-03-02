from manifold3d import *
import numpy as np

def create_object():
    # Create a cube scaled to the right size
    cube = Manifold.cube((0.3, 0.3, 0.3))
    
    # Create a polyhedron by reducing segments
    set_circular_segments(10)  # Further reduce segments for more faceted appearance
    sphere = Manifold.sphere(0.15)  # Keep sphere size
    
    # Position the sphere relative to the cube
    sphere = sphere.translate((-0.3, 0, 0))  # Move sphere further left
    
    # Move cube to correct position
    cube = cube.translate((0, 0, 0))  # Keep cube at origin
    
    # Combine the shapes
    result = cube + sphere
    
    return result