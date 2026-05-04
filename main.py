import pygame
from constantes import *
from agente import Agente
from renderer import EstoqueRenderer
import random
from dataclasses import dataclass


@dataclass
class Pacote:
    pos: pygame.Vector2
    shelf_index: int
    coletado: bool = False

def calcular_mutacao(geracao):
    taxa = TAXA_MUTACAO * (0.97 ** geracao)
    forca = FORCA_MUTACAO * (0.97 ** geracao)
    return max(0.05, taxa), max(0.08, forca)

def gerar_pacote_aleatorio(racks):
    shelf_index = random.randint(0, len(racks) - 1)
    rack = racks[shelf_index]

    distancia = 12

    pontos_possiveis = [
        pygame.Vector2(rack.centerx, rack.top - distancia),
        pygame.Vector2(rack.centerx, rack.bottom + distancia),
        pygame.Vector2(rack.left - distancia, rack.centery),
        pygame.Vector2(rack.right + distancia, rack.centery),
    ]

    random.shuffle(pontos_possiveis)

    for pos in pontos_possiveis:
        if 20 <= pos.x <= LARGURA_MAPA - 20 and 20 <= pos.y <= ALTURA_MAPA - 20:
            return Pacote(pos=pos, shelf_index=shelf_index, coletado=False)

    return Pacote(
        pos=pygame.Vector2(rack.centerx, rack.bottom + distancia),
        shelf_index=shelf_index,
        coletado=False
    )


def criar_agente_em_posicao_aleatoria(obstaculos, agentes_existentes=None):
    if agentes_existentes is None:
        agentes_existentes = []

    for _ in range(300):
        x = random.randint(50, LARGURA_MAPA - 50)
        y = random.randint(50, ALTURA_MAPA - 50)

        agente = Agente(x, y)
        rect = agente.get_rect()

        colidiu_obstaculo = any(rect.colliderect(obs) for obs in obstaculos)
        colidiu_agente = any(rect.colliderect(outro.get_rect()) for outro in agentes_existentes)

        if not colidiu_obstaculo and not colidiu_agente:
            return agente

    return Agente(50, 50)

POSICAO_INICIAL_FIXA = pygame.Vector2(100, 300)
PACOTE_FIXO_POS = None

def criar_populacao(racks, obstaculos):
    agentes = []
    for _ in range(NUM_AGENTES):
        agente = criar_agente_em_posicao_aleatoria(obstaculos, agentes)
        agentes.append(agente)

    pacotes = atribuir_pacotes_para_agentes(agentes, racks, rack_fixo=racks[0])
    return agentes, pacotes

def atribuir_pacotes_para_agentes(agentes, racks, rack_fixo=None):
    pacotes = []
    for agente in agentes:
        if rack_fixo is not None:
            distancia = 12
            pos = pygame.Vector2(rack_fixo.centerx, rack_fixo.bottom + distancia)
            pacote = Pacote(pos=pos, shelf_index=0, coletado=False)
        else:
            pacote = gerar_pacote_aleatorio(racks)
        agente.atribuir_pacote(pacote)
        pacotes.append(pacote)
    return pacotes


def criar_nova_geracao(agentes_atuais, racks, obstaculos, geracao=1):
    agentes_ordenados = sorted(
        agentes_atuais,
        key=lambda a: (a.itens_entregues, a.coletas, a.fitness),
        reverse=True
    )

    elite_agentes = agentes_ordenados[:ELITE]
    pool_tamanho = max(len(agentes_atuais) // 2, ELITE * 2)
    pool_reproducao = agentes_ordenados[:pool_tamanho]

    novos_agentes = []

    for elite in elite_agentes:
        novo = criar_agente_em_posicao_aleatoria(obstaculos, novos_agentes)
        novo.brain = elite.brain.copy()
        novos_agentes.append(novo)

    while len(novos_agentes) < NUM_AGENTES:
        pai1 = random.choice(pool_reproducao)
        pai2 = random.choice(pool_reproducao)

        filho = criar_agente_em_posicao_aleatoria(obstaculos, novos_agentes)
        filho.brain = pai1.brain.crossover(pai2.brain)

        taxa_mut, forca_mut = calcular_mutacao(geracao)
        filho.brain.mutate(rate=taxa_mut, strength=forca_mut)

        novos_agentes.append(filho)

    fitness_medio = sum(a.fitness for a in agentes_atuais) / len(agentes_atuais)
    entregas_total = sum(a.itens_entregues for a in agentes_atuais)
    coletas_total = sum(a.coletas for a in agentes_atuais)
    colisoes_total = sum(a.colisoes for a in agentes_atuais)

    # ← AGORA pode usar entregas_total
    usar_rack_fixo = racks[0] if entregas_total == 0 else None
    pacotes = atribuir_pacotes_para_agentes(novos_agentes, racks, rack_fixo=usar_rack_fixo)

    return novos_agentes, pacotes, fitness_medio, entregas_total, coletas_total, colisoes_total


pygame.init()

screen = pygame.display.set_mode((LARGURA_MAPA, ALTURA_MAPA))
pygame.display.set_caption("Neuroevolução - Armazém 2D")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 26)

renderer = EstoqueRenderer(screen, LARGURA_MAPA, ALTURA_MAPA, FPS)
obstaculos = renderer.obter_obstaculos()

zona_entrega = pygame.Rect(
    ENTREGA_X,
    ENTREGA_Y,
    ENTREGA_LARGURA,
    ENTREGA_ALTURA
)

agentes, pacotes = criar_populacao(renderer.rack_rects, obstaculos)

geracao = 1
tempo_geracao = 0.0
fitness_medio_anterior = 0.0
entregas_anteriores = 0
coletas_anteriores = 0
colisoes_anteriores = 0

running = True

while running:
    dt = clock.tick(FPS) / 1000
    tempo_geracao += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    for agente in agentes:
        agente.mover(
            dt,
            zona_entrega_rect=zona_entrega,
            obstaculos=obstaculos,
            outros_agentes=agentes
        )

        pegou = agente.tentar_pegar_pacote()
        entregou = agente.tentar_entregar_pacote(zona_entrega)


    pacotes_visiveis = [p for p in pacotes if not p.coletado]

    if pacotes_visiveis:
        alvo_visual = pacotes_visiveis[0].pos
    else:
        alvo_visual = pygame.Vector2(zona_entrega.center)

    renderer.renderizar(
        agentes,
        alvo_visual,
        item=None,
        zona_entrega=zona_entrega
    )

    for pacote in pacotes_visiveis:
        pygame.draw.circle(
            screen,
            (70, 90, 220),
            (int(pacote.pos.x), int(pacote.pos.y)),
            6
        )
        pygame.draw.circle(
            screen,
            (220, 230, 255),
            (int(pacote.pos.x), int(pacote.pos.y)),
            2
        )

    texto_geracao = font.render(
        f"Geração: {geracao}",
        True,
        (255, 255, 255)
    )

    texto_tempo = font.render(
        f"Tempo: {tempo_geracao:.1f}s / {DURACAO_GERACAO}s",
        True,
        (255, 255, 255)
    )

    texto_fitness = font.render(
        f"Fitness médio anterior: {fitness_medio_anterior:.2f}",
        True,
        (255, 255, 255)
    )

    texto_entregas = font.render(
        f"Entregas geração anterior: {entregas_anteriores}",
        True,
        (255, 255, 255)
    )

    texto_colisoes = font.render(
        f"Colisões geração anterior: {colisoes_anteriores}",
        True,
        (255, 255, 255)
    )

    texto_coletas = font.render(
        f"Coletas geração anterior: {coletas_anteriores}",
        True,
        (255, 255, 255)
    )

    screen.blit(texto_geracao, (10, 10))
    screen.blit(texto_tempo, (10, 35))
    screen.blit(texto_fitness, (10, 60))
    screen.blit(texto_coletas, (10, 85))
    screen.blit(texto_entregas, (10, 110))
    screen.blit(texto_colisoes, (10, 135))
    #screen.blit(texto_atual, (10, 160))

    pygame.display.flip()

    if tempo_geracao >= DURACAO_GERACAO:
        (
            agentes,
            pacotes,
            fitness_medio_anterior,
            entregas_anteriores,
            coletas_anteriores,
            colisoes_anteriores
        ) = criar_nova_geracao(agentes, renderer.rack_rects, obstaculos, geracao)

        geracao += 1
        tempo_geracao = 0.0

pygame.quit()