import os
from dotenv import load_dotenv

load_dotenv()

ALTURA_MAPA = int(os.getenv("ALTURA_MAPA", 600))
LARGURA_MAPA = int(os.getenv("LARGURA_MAPA", 900))

NUM_AGENTES = int(os.getenv("NUM_AGENTES", 20))
FPS = int(os.getenv("FPS", 60))
VELOCIDADE_AGENTE = float(os.getenv("VELOCIDADE_AGENTE", 200))

INPUT_SIZE = int(os.getenv("INPUT_SIZE", 3))
HIDDEN_SIZE = int(os.getenv("HIDDEN_SIZE", 6))
OUTPUT_SIZE = int(os.getenv("OUTPUT_SIZE", 2))

# ponto de entrega
ENTREGA_X = 820
ENTREGA_Y = 560
ENTREGA_LARGURA = 70
ENTREGA_ALTURA = 70