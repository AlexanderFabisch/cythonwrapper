import numpy as np
from test import CppA


a = CppA()
vec = np.array([0.1, 0.5, 0.9])
a.set_vec(vec)
a.p()
vec2 = np.empty(3)
a.get_vec(vec2)
print(vec2)
