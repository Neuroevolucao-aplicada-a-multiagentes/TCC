import pygame
from constantes import *
from agente import Agente
from renderer import EstoqueRenderer

pygame.init()
screen = pygame.display.set_mode((LARGURA_MAPA, ALTURA_MAPA))
pygame.display.set_caption("Visualizacao de Estoque - Top Down")
clock = pygame.time.Clock()
running = True
dt = 0

agentes = [Agente(100,100) for _ in range(NUM_AGENTES)]
resource_pos = pygame.Vector2(700,300)
renderer = EstoqueRenderer(screen, LARGURA_MAPA, ALTURA_MAPA, FPS)
obstaculos = renderer.obter_obstaculos()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    for agente in agentes:
        agente.mover(dt, resource_pos, obstaculos=obstaculos)

    renderer.renderizar(agentes, resource_pos)

    pygame.display.flip()

    dt = clock.tick(FPS)/1000

pygame.quit()
