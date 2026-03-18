import pygame
from constantes import *
from agente import Agente
from renderer import EstoqueRenderer  
import random
from dataclasses import dataclass

# caixa para coletar
@dataclass
class ItemEstoque:
    pos: pygame.Vector2
    shelf_index: int
    coletado: bool = False

# cria objeto de coleta em posição aleatoria (mas semopre proximo ao canto)
def gerar_item_aleatorio(racks):
    shelf_index = random.randint(0, len(racks) - 1)
    rack = racks[shelf_index]

    distancia = 10  # quão longe da prateleira o item nasce

    pontos_possiveis = [
        pygame.Vector2(rack.centerx, rack.top - distancia),      # acima da prateleira
        pygame.Vector2(rack.centerx, rack.bottom + distancia),   # abaixo da prateleira
        pygame.Vector2(rack.left - distancia, rack.centery),     # esquerda
        pygame.Vector2(rack.right + distancia, rack.centery),    # direita
    ]

    random.shuffle(pontos_possiveis)

    for pos in pontos_possiveis:
        if 10 <= pos.x <= LARGURA_MAPA - 10 and 10 <= pos.y <= ALTURA_MAPA - 10:
            return ItemEstoque(
                pos=pos,
                shelf_index=shelf_index,
                coletado=False
            )

    return ItemEstoque(
        pos=pygame.Vector2(rack.centerx, rack.bottom + distancia),
        shelf_index=shelf_index,
        coletado=False
    )

pygame.init()
screen = pygame.display.set_mode((LARGURA_MAPA, ALTURA_MAPA))
pygame.display.set_caption("Visualizacao de Estoque - Top Down")
clock = pygame.time.Clock()
running = True
dt = 0

# adiciona o robo controlavel
agentes = [Agente(100, 100, controlavel=True)] + [
    Agente(100 + i * 30, 150) for i in range(NUM_AGENTES - 1)
]

resource_pos = pygame.Vector2(700, 300)
renderer = EstoqueRenderer(screen, LARGURA_MAPA, ALTURA_MAPA, FPS)
obstaculos = renderer.obter_obstaculos()

zona_entrega = pygame.Rect(
    ENTREGA_X,
    ENTREGA_Y,
    ENTREGA_LARGURA,
    ENTREGA_ALTURA
)

item_atual = gerar_item_aleatorio(renderer.rack_rects)

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # permite a colisão
    for agente in agentes:
        agente.mover(
            dt,
            resource_pos,
            obstaculos=obstaculos,
            outros_agentes=agentes
        )

        # tenta pegar item
        if item_atual and not item_atual.coletado:
            agente.tentar_pegar_item(item_atual)

        # tenta entregar item
        entregou = agente.tentar_entregar_item(zona_entrega)
        if entregou:
            item_atual = gerar_item_aleatorio(renderer.rack_rects)

    renderer.renderizar(agentes, resource_pos, item=item_atual, zona_entrega=zona_entrega)

    pygame.display.flip()
    dt = clock.tick(FPS) / 1000

pygame.quit()