def cube(n):
    return n*n*n

def triarea(base,height):
    return base* height/2

import unittest

class sujith(unittest.TestCase):
    def test_cube(self):
        self.assertEqual(cube(5),125)
    def test_triarea(self):
        self.assertEqual(triarea(10,10),50)

unittest.main()
