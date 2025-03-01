from manifold3d import *
import numpy as np

def create_object():
    cube = Manifold.cube((0.5, 0.5, 0.5))
    octahedron = Manifold.tetrahedron().scale((0.35, 0.35, 0.35)).translate((-0.5, 0, 0))
    return cube + octahedron