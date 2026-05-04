from constantes import INPUT_SIZE, HIDDEN_SIZE, OUTPUT_SIZE
import numpy as np


class RedeNeural:
    def __init__(self, input_size=INPUT_SIZE, hidden_size=HIDDEN_SIZE, output_size=OUTPUT_SIZE):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
    
        self.w1 = np.random.randn(input_size, hidden_size) * np.sqrt(1 / input_size)
        self.w2 = np.random.randn(hidden_size, output_size) * np.sqrt(1 / hidden_size)

        self.b1 = np.zeros(hidden_size)
        self.b2 = np.zeros(output_size)

    def forward(self, x):
        x = np.array(x)

        h = np.tanh(np.dot(x, self.w1) + self.b1)
        out = np.tanh(np.dot(h, self.w2) + self.b2)

        return out
    
    def copy(self):
        nova_rede = RedeNeural(self.input_size, self.hidden_size, self.output_size)

        nova_rede.w1 = np.copy(self.w1)
        nova_rede.w2 = np.copy(self.w2)
        nova_rede.b1 = np.copy(self.b1)
        nova_rede.b2 = np.copy(self.b2)
        
        return nova_rede

    def crossover(self, outra_rede):
        filho = self.copy()

        for attr in ["w1", "w2", "b1", "b2"]:
            a = getattr(self, attr)
            b = getattr(outra_rede, attr)

            mask = np.random.rand(*a.shape) > 0.5
            setattr(filho, attr, np.where(mask, a, b))

        return filho
    
    def mutate(self, rate=0.1, strength=0.2):
        for matrix in [self.w1, self.w2]:
            mask = np.random.rand(*matrix.shape) < rate
            matrix += mask * np.random.randn(*matrix.shape) * strength

        for bias in [self.b1, self.b2]:
            mask = np.random.rand(*bias.shape) < rate
            bias += mask * np.random.randn(*bias.shape) * strength