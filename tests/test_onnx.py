import cv2
import os

import unittest

from fusion_solar_py.captcha_solver_onnx import Solver

currentdir = os.path.dirname(__file__)

class TestInference(unittest.TestCase):
    def test_inference(self):
        """Test if the inference works on the test image"""
        solver = Solver(os.path.join(currentdir, "../models/captcha_huawei.onnx"), device=["CPUExecutionProvider"])
        result = solver.solve_captcha(cv2.imread(os.path.join(currentdir, "test_img.png")))
        self.assertEqual(result, "8fab")