from manifold3d import *
import numpy as np

def create_object():
    cube = Manifold.cube((0.5, 0.5, 0.5))
    sphere = Manifold.tetrahedron().scale((0.25, 0.25, 0.25)).translate((-0.3, -0.3, 0))
    return cube + sphere