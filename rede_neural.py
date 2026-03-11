from constantes import INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE
import numpy as np


class RedeNeural:
    def __init__(self, input_size=INPUT_SIZE, hidden_size=HIDDEN_SIZE, output_size=OUTPUT_SIZE):
        #pesos aleatorios
        self.w1 = np.random.randn(input_size, hidden_size)
        self.w2 = np.random.randn(hidden_size, output_size)

    def forward(self, x):
        x = np.array(x)

        h = np.tanh(np.dot(x, self.w1))
        out = np.tanh(np.dot(h, self.w2))

        return out