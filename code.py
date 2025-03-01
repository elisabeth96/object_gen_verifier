from manifold3d import *
import numpy as np

def create_object():
    cube = Manifold.cube((0.5, 0.5, 0.5))
    octahedron = Manifold.tetrahedron().scale((0.3, 0.3, 0.3)).translate((-0.3, -0.3, 0.3))
    return cube + octahedron