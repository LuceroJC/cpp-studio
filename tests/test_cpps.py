import numpy as np
from cli.cpps import _preemphasis, _q_range


def test_preemphasis_stability():
x = np.zeros(1000); x[10]=1
y = _preemphasis(x, 0.97)
assert np.isfinite(y).all()




def test_q_range():
qmin, qmax = _q_range(60, 500)
assert 0.0 < qmin < qmax