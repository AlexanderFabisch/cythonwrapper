import numpy as np
from rotations import Quaternion


q = Quaternion()
q.set(0.5, 0.2, 0.1, 0.3)
print(q.to_string())
