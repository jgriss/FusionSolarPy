import cv2
import time
import os

import unittest

from fusion_solar_py.captcha_solver_onnx import Solver

currentdir = os.path.dirname(__file__)

class TestInference(unittest.TestCase):
    def test_inference(self):
        """Test if the inference works on the test image"""
        solver = Solver(os.path.join(currentdir, "../models/captcha_huawei.onnx"), device=["CPUExecutionProvider"])
        start = time.perf_counter()
        result = solver.solve_captcha(cv2.imread(os.path.join(currentdir, "test_img.png")))
        stop = time.perf_counter()
        print(f"inference time on cpu: {(stop - start) * 1000}ms")
        self.assertEqual(result, "8fab")

if __name__ == '__main__':
    unittest.main()