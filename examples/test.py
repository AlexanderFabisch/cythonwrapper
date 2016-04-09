import numpy as np
from test import CppFactory, cpp_shutdown


fac = CppFactory()
a = fac.make()
vec = np.array([0.1, 0.5, 0.9])
print("Empty: %s" % a.is_empty())
a.set_vec(vec)
print("Empty: %s" % a.is_empty())
a.p()
vec2 = np.empty(3)
a.get_vec(vec2)
print(vec2)
print(a.info())
cpp_shutdown()
