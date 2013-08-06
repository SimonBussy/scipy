"""Test functions for the sparse.linalg.interface module
"""

from __future__ import division, print_function, absolute_import

from numpy.testing import TestCase, assert_, assert_equal, \
        assert_raises

import numpy as np
import scipy.sparse as sparse
from itertools import product

from scipy.sparse.linalg import interface


class TestLinearOperator(TestCase):
    def setUp(self):
        self.A = np.array([[1,2,3],
                           [4,5,6]])
        self.B = np.array([[1,2],
                           [3,4],
                           [5,6]])
        self.C = np.array([[1,2],
                           [3,4]])

    def test_matvec(self):
        def get_matvecs(A):
            return [{
                        'shape': A.shape,
                        'matvec': lambda x: np.dot(A, x).reshape(A.shape[0]),
                        'rmatvec':
                            lambda x: np.dot(A.T.conj(), x).reshape(A.shape[1])
                    },
                    {
                        'shape': A.shape,
                        'matvec': lambda x: np.dot(A, x),
                        'rmatvec': lambda x: np.dot(A.T.conj(), x),
                        'matmat': lambda x: np.dot(A, x)
                    }]

        for matvecs in get_matvecs(self.A):
            A = interface.LinearOperator(**matvecs)

            assert_equal(A.matvec(np.array([1,2,3])), [14,32])
            assert_equal(A.matvec(np.array([[1],[2],[3]])), [[14],[32]])
            assert_equal(A * np.array([1,2,3]), [14,32])
            assert_equal(A * np.array([[1],[2],[3]]), [[14],[32]])
            assert_equal(A.dot(np.array([1,2,3])), [14,32])
            assert_equal(A.dot(np.array([[1],[2],[3]])), [[14],[32]])

            assert_equal(A.matvec(np.matrix([[1],[2],[3]])), [[14],[32]])
            assert_equal(A * np.matrix([[1],[2],[3]]), [[14],[32]])
            assert_equal(A.dot(np.matrix([[1],[2],[3]])), [[14],[32]])

            assert_equal((2*A)*[1,1,1], [12,30])
            assert_equal((2*A)*[[1],[1],[1]], [[12],[30]])
            assert_equal((A+A)*[1,1,1], [12, 30])
            assert_equal((A+A)*[[1],[1],[1]], [[12], [30]])
            assert_equal((-A)*[1,1,1], [-6,-15])
            assert_equal((-A)*[[1],[1],[1]], [[-6],[-15]])
            assert_equal((A-A)*[1,1,1], [0,0])
            assert_equal((A-A)*[[1],[1],[1]], [[0],[0]])

            assert_(isinstance(A.matvec(np.array([1,2,3])), np.ndarray))
            assert_(isinstance(A.matvec(np.array([[1],[2],[3]])), np.ndarray))
            assert_(isinstance(A * np.array([1,2,3]), np.ndarray))
            assert_(isinstance(A * np.array([[1],[2],[3]]), np.ndarray))
            assert_(isinstance(A.dot(np.array([1,2,3])), np.ndarray))
            assert_(isinstance(A.dot(np.array([[1],[2],[3]])), np.ndarray))

            assert_(isinstance(A.matvec(np.matrix([[1],[2],[3]])), np.ndarray))
            assert_(isinstance(A * np.matrix([[1],[2],[3]]), np.ndarray))
            assert_(isinstance(A.dot(np.matrix([[1],[2],[3]])), np.ndarray))

            assert_(isinstance(2*A, interface.LinearOperator))
            assert_(isinstance(A+A, interface.LinearOperator))
            assert_(isinstance(-A, interface.LinearOperator))
            assert_(isinstance(A-A, interface.LinearOperator))

            assert_raises(ValueError, A.matvec, np.array([1,2]))
            assert_raises(ValueError, A.matvec, np.array([1,2,3,4]))
            assert_raises(ValueError, A.matvec, np.array([[1],[2]]))
            assert_raises(ValueError, A.matvec, np.array([[1],[2],[3],[4]]))

            assert_raises(ValueError, A.__mul__, A)
            assert_raises(ValueError, A.__pow__, 2)

        for matvecsA, matvecsB in product(get_matvecs(self.A),
                                          get_matvecs(self.B)):
            A = interface.LinearOperator(**matvecsA)
            B = interface.LinearOperator(**matvecsB)

            assert_equal((A*B)*[1,1], [50,113])
            assert_equal((A*B)*[[1],[1]], [[50],[113]])

            assert_(isinstance(A*B, interface.LinearOperator))

            assert_raises(ValueError, A.__add__, B)
            assert_raises(ValueError, A.__pow__, 2)

        for matvecsC in get_matvecs(self.C):
            C = interface.LinearOperator(**matvecsC)

            assert_equal((C**2)*[1,1], [17,37])

            assert_(isinstance(C**2, interface.LinearOperator))

class TestAsLinearOperator(TestCase):
    def setUp(self):
        self.cases = []

        def make_cases(dtype):
            self.cases.append(np.matrix([[1,2,3],[4,5,6]], dtype=dtype))
            self.cases.append(np.array([[1,2,3],[4,5,6]], dtype=dtype))
            self.cases.append(sparse.csr_matrix([[1,2,3],[4,5,6]], dtype=dtype))

            class matlike:
                def __init__(self, dtype):
                    self.dtype = np.dtype(dtype)
                    self.shape = (2,3)

                def matvec(self,x):
                    y = np.array([1*x[0] + 2*x[1] + 3*x[2],
                                   4*x[0] + 5*x[1] + 6*x[2]], dtype=self.dtype)
                    if len(x.shape) == 2:
                        y = y.reshape(-1,1)
                    return y

                def rmatvec(self,x):
                    return np.array([1*x[0] + 4*x[1],
                                      2*x[0] + 5*x[1],
                                      3*x[0] + 6*x[1]], dtype=self.dtype)
            self.cases.append(matlike('int'))

        make_cases('int32')
        make_cases('float32')
        make_cases('float64')

    def test_basic(self):

        for M in self.cases:
            A = interface.aslinearoperator(M)
            M,N = A.shape

            assert_equal(A.matvec(np.array([1,2,3])), [14,32])
            assert_equal(A.matvec(np.array([[1],[2],[3]])), [[14],[32]])

            assert_equal(A * np.array([1,2,3]), [14,32])
            assert_equal(A * np.array([[1],[2],[3]]), [[14],[32]])

            assert_equal(A.rmatvec(np.array([1,2])), [9,12,15])
            assert_equal(A.rmatvec(np.array([[1],[2]])), [[9],[12],[15]])

            assert_equal(
                    A.matmat(np.array([[1,4],[2,5],[3,6]])),
                    [[14,32],[32,77]])

            assert_equal(A * np.array([[1,4],[2,5],[3,6]]), [[14,32],[32,77]])

            if hasattr(M,'dtype'):
                assert_equal(A.dtype, M.dtype)

    def test_dot(self):

        for M in self.cases:
            A = interface.aslinearoperator(M)
            M,N = A.shape

            assert_equal(A.dot(np.array([1,2,3])), [14,32])
            assert_equal(A.dot(np.array([[1],[2],[3]])), [[14],[32]])

            assert_equal(
                    A.dot(np.array([[1,4],[2,5],[3,6]])),
                    [[14,32],[32,77]])
