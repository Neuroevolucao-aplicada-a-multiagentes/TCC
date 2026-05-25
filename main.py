import pygame
from constantes import *
from agente import Agente
from renderer import EstoqueRenderer
import random
import os
import csv
from dataclasses import dataclass

USAR_REDE_PRETREINADA = True
SEED_DEMO = 42
CHECKPOINT_DEMO = "tcc_neuroevolucao/melhor_rede_fase5.npz"
SALVAR_CSV = True
CSV_PATH = "runs/snapshots.csv"

random.seed(SEED_DEMO)

controlador = None
if USAR_REDE_PRETREINADA:
    from controlador_neural import ControladorNeural
    controlador = ControladorNeural(CHECKPOINT_DEMO)


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

    distancia = 35

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


def encontrar_posicao_livre(obstaculos, agentes, ignorar_agente=None, tentativas=300):
    for _ in range(tentativas):
        x = random.randint(50, LARGURA_MAPA - 50)
        y = random.randint(50, ALTURA_MAPA - 50)
        rect = pygame.Rect(x - 10, y - 10, 20, 20)
        if any(rect.colliderect(obs) for obs in obstaculos):
            continue
        if any(rect.colliderect(outro.get_rect()) for outro in agentes if outro is not ignorar_agente):
            continue
        return x, y
    return None

POSICAO_INICIAL_FIXA = pygame.Vector2(100, 300)
PACOTE_FIXO_POS = None

def criar_populacao(racks, obstaculos, num_agentes=NUM_AGENTES, rack_fixo=None):
    agentes = []
    for _ in range(num_agentes):
        agente = criar_agente_em_posicao_aleatoria(obstaculos, agentes)
        agentes.append(agente)

    pacotes = atribuir_pacotes_para_agentes(agentes, racks, rack_fixo=rack_fixo)
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

if USAR_REDE_PRETREINADA:
    NUM_AGENTES_EFETIVO = 6
    RACK_FIXO_INICIAL = None
else:
    NUM_AGENTES_EFETIVO = NUM_AGENTES
    RACK_FIXO_INICIAL = renderer.rack_rects[0]

agentes, pacotes = criar_populacao(
    renderer.rack_rects, obstaculos,
    num_agentes=NUM_AGENTES_EFETIVO,
    rack_fixo=RACK_FIXO_INICIAL,
)

if controlador is not None:
    for agente in agentes:
        agente.controlador_externo = controlador

geracao = 1
tempo_geracao = 0.0
fitness_medio_anterior = 0.0
entregas_anteriores = 0
coletas_anteriores = 0
colisoes_anteriores = 0

running = True

tempo_real = 0.0
ultimo_print = 0.0
frames_parado = [0 for _ in agentes]
frames_em_colisao = [0 for _ in agentes]
frames_colisao_consecutivos = [0 for _ in agentes]
reposicionamentos = [0 for _ in agentes]
flash_restante = [0 for _ in agentes]
total_frames = 0

LIMITE_TRAVADO_FRAMES = int(FPS * 3.0)
FLASH_FRAMES = int(FPS * 0.5)

snapshots = []
NOME_REDE = os.path.basename(CHECKPOINT_DEMO) if USAR_REDE_PRETREINADA else "treinando do zero"
font_hud_titulo = pygame.font.SysFont(None, 22)
font_hud_valor = pygame.font.SysFont(None, 26)

while running:
    dt = clock.tick(FPS) / 1000
    tempo_geracao += dt
    tempo_real += dt
    total_frames += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if controlador is not None:
        controlador.set_contexto(obstaculos, agentes, zona_entrega, tempo_geracao)

    for idx, agente in enumerate(agentes):
        agente.mover(
            dt,
            zona_entrega_rect=zona_entrega,
            obstaculos=obstaculos,
            outros_agentes=agentes
        )

        pegou = agente.tentar_pegar_pacote()
        entregou = agente.tentar_entregar_pacote(zona_entrega)

        if entregou:
            novo_pacote = gerar_pacote_aleatorio(renderer.rack_rects)
            agente.atribuir_pacote(novo_pacote)
            pacotes.append(novo_pacote)

        if agente.vel.length() < 0.05:
            frames_parado[idx] += 1
        if agente.em_colisao:
            frames_em_colisao[idx] += 1
            frames_colisao_consecutivos[idx] += 1
        else:
            frames_colisao_consecutivos[idx] = 0

        if frames_colisao_consecutivos[idx] >= LIMITE_TRAVADO_FRAMES:
            nova_pos = encontrar_posicao_livre(obstaculos, agentes, ignorar_agente=agente)
            if nova_pos is not None:
                agente.pos = pygame.Vector2(*nova_pos)
                agente.vel = pygame.Vector2(0, 0)
                agente.em_colisao = False
                agente.distancia_anterior = None
                frames_colisao_consecutivos[idx] = 0
                reposicionamentos[idx] += 1
                flash_restante[idx] = FLASH_FRAMES

    if tempo_real - ultimo_print >= 10.0:
        total_coletas = sum(a.coletas for a in agentes)
        total_entregas = sum(a.itens_entregues for a in agentes)
        total_colisoes = sum(a.colisoes for a in agentes)
        total_manut = sum(reposicionamentos)
        snapshots.append({
            "tempo": round(tempo_real, 1),
            "coletas": total_coletas,
            "entregas": total_entregas,
            "colisoes": total_colisoes,
            "manutencoes": total_manut,
        })
        print(
            f"[{tempo_real:5.1f}s] coletas={total_coletas:3d} "
            f"entregas={total_entregas:3d} colisoes={total_colisoes:4d} "
            f"manut={total_manut:3d}",
            flush=True,
        )
        ultimo_print = tempo_real

    pacotes_visiveis = [
        a.pacote for a in agentes
        if a.pacote is not None and not a.pacote.coletado
    ]

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

    for idx, agente in enumerate(agentes):
        if flash_restante[idx] > 0:
            progresso = flash_restante[idx] / FLASH_FRAMES
            raio = int(8 + (1 - progresso) * 28)
            alpha = int(220 * progresso)
            flash_surf = pygame.Surface((raio * 2 + 4, raio * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 215, 80, alpha),
                               (raio + 2, raio + 2), raio, 3)
            screen.blit(flash_surf,
                       (int(agente.pos.x) - raio - 2, int(agente.pos.y) - raio - 2))
            flash_restante[idx] -= 1

    texto_geracao = font.render(f"Geração: {geracao}", True, (255, 255, 255))
    texto_tempo = font.render(
        f"Tempo: {tempo_real:.1f}s",
        True, (255, 255, 255)
    )
    screen.blit(texto_geracao, (16, 14))
    screen.blit(texto_tempo, (16, 40))

    if USAR_REDE_PRETREINADA:
        hud_total_coletas = sum(a.coletas for a in agentes)
        hud_total_entregas = sum(a.itens_entregues for a in agentes)
        hud_total_colisoes = sum(a.colisoes for a in agentes)
        hud_total_manut = sum(reposicionamentos)

        hud_linhas = [
            ("Rede", NOME_REDE),
            ("Coletas", str(hud_total_coletas)),
            ("Entregas", str(hud_total_entregas)),
            ("Colisões", str(hud_total_colisoes)),
            ("Manutenções", str(hud_total_manut)),
        ]

        hud_w = 230
        hud_h = 26 + len(hud_linhas) * 32
        hud_x = LARGURA_MAPA - hud_w - 12
        hud_y = 12

        painel = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
        pygame.draw.rect(painel, (20, 24, 30, 200), painel.get_rect(), border_radius=8)
        pygame.draw.rect(painel, (255, 255, 255, 60), painel.get_rect(), 1, border_radius=8)
        screen.blit(painel, (hud_x, hud_y))

        for i, (rotulo, valor) in enumerate(hud_linhas):
            base_y = hud_y + 14 + i * 32
            txt_rotulo = font_hud_titulo.render(rotulo, True, (180, 195, 215))
            txt_valor = font_hud_valor.render(valor, True, (255, 255, 255))
            screen.blit(txt_rotulo, (hud_x + 14, base_y))
            valor_rect = txt_valor.get_rect()
            valor_rect.topright = (hud_x + hud_w - 14, base_y - 2)
            screen.blit(txt_valor, valor_rect)

    pygame.display.flip()

    if tempo_geracao >= DURACAO_GERACAO and not USAR_REDE_PRETREINADA:
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
    elif tempo_geracao >= DURACAO_GERACAO and USAR_REDE_PRETREINADA:
        tempo_geracao = 0.0

print()
print("=" * 70)
print(f"Resumo final apos {tempo_real:.1f}s ({total_frames} frames, {NUM_AGENTES_EFETIVO} agentes)")
print("=" * 70)
print(f"{'#':>3} {'coletas':>7} {'entregas':>8} {'colisoes':>8} {'parado%':>8} {'colidiu%':>9} {'manut':>6}")
for idx, a in enumerate(agentes):
    pct_parado = 100.0 * frames_parado[idx] / max(1, total_frames)
    pct_colisao = 100.0 * frames_em_colisao[idx] / max(1, total_frames)
    print(f"{idx:>3} {a.coletas:>7d} {a.itens_entregues:>8d} {a.colisoes:>8d} "
          f"{pct_parado:>7.1f}% {pct_colisao:>8.1f}% {reposicionamentos[idx]:>6d}")
print("-" * 70)
total_c = sum(a.coletas for a in agentes)
total_e = sum(a.itens_entregues for a in agentes)
total_col = sum(a.colisoes for a in agentes)
print(f"TOT {total_c:>7d} {total_e:>8d} {total_col:>8d}")
print(f"taxa entrega/coleta = {(total_e / total_c * 100) if total_c else 0:.1f}%")
print(f"colisoes/min = {total_col / max(0.01, tempo_real / 60):.1f}")

if SALVAR_CSV and snapshots:
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["tempo", "coletas", "entregas", "colisoes", "manutencoes"])
        writer.writeheader()
        writer.writerows(snapshots)
    print(f"snapshots salvos em {CSV_PATH} ({len(snapshots)} linhas)")

pygame.quit()