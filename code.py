from manifold3d import *
import numpy as np

def create_object():
    cube = Manifold.cube((1, 1, 1)).translate((2, 0, 0))
    sphere = Manifold.sphere(0.5).translate((-1, 0, 0))
    return cube + sphere