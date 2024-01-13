from .exceptions import FusionSolarException

try:
    import cv2
    import numpy as np
    import onnxruntime as rt
except ImportError:
    print("Required libraries for CAPTCHA solving are not available. Please install the package using pip install fusion_solar_py[captcha].")
    raise FusionSolarException("Required libraries for CAPTCHA solving are not available. Please install the package using pip install fusion_solar_py[captcha].")

from fusion_solar_py.interfaces import GenericSolver

from .ctc_decoder import decode

alphabet = ['2', '3', '4', '5', '6', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'l', 'r', 't', 'y']
blank_idx = 20

class Solver(GenericSolver):

    def _init_model(self):
        self.session = rt.InferenceSession(self.model_path, providers=self.device)


    def solve_captcha(self, img):
        if type(img) != np.ndarray:
            img = np.frombuffer(img, np.uint8)
            img = cv2.imdecode(img, cv2.IMREAD_GRAYSCALE)
        img = self.preprocess_image(img)
        img = np.expand_dims(img, axis=0)
        out = self.session.run(None, {"image": img.astype(np.float32), "label": None})
        return self.decode_batch_predictions(out[0])

    def decode_batch_predictions(self, pred):
        # Using a beam size of 10 here as the output is quite small as
        # we only have 19 characters and a string length of 4
        # If this causese, probelms, increas the beam size
        # default val is 100
        # I have tested it with 10 and it seemed to work well
        results = decode(pred[0], beam_size=10, blank=blank_idx)
        # Iterate over the results and get back the text
        output_text = list(map(lambda n: alphabet[n-1], results[0]))
        return ''.join(output_text)

    def preprocess_image(self, img):
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = img / 255.0
        # swap axis
        img = np.swapaxes(img, 0, 1)
        img = np.expand_dims(img, axis=2)
        return img
