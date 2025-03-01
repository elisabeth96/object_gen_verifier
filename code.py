from manifold3d import *
import numpy as np

def create_object():
    # Create cube scaled to correct size
    cube = Manifold.cube((0.4, 0.4, 0.4)).translate((0.8, 0, 0))
    
    # Create octahedron by using sphere with fewer segments
    set_circular_segments(8)
    octahedron = Manifold.sphere(0.2)
    
    # Position octahedron relative to cube
    octahedron = octahedron.translate((0, 0, 0))
    
    # Combine cube and octahedron
    result = cube + octahedron
    
    return result