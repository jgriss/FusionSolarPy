import onnxruntime as rt
import cv2
import numpy as np
import time

from fusion_solar_py.captcha_solver_onnx import Solver

solver = Solver("D:\\Code\\Repos\\walzen-group\\FusionSolarPy\\src\\fusion_solar_py\\captcha_huawei.onnx", device=["CPUExecutionProvider"])

start = time.time()
result = solver.solve_captcha(cv2.imread("D:\\Code\\Projects\\captcha\\captcha\\bcch.jpg"))
stop = time.time()
print(f"inference time on cpu: {(stop - start) * 1000}ms")
print(result)
