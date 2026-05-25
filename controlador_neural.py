import math
import pygame
import numpy as np

from tcc_neuroevolucao.rede_transfer import RedeNeural
from tcc_neuroevolucao.raycast import raycast, ALCANCE_RAY
from constantes import LARGURA_MAPA, ALTURA_MAPA, DIAGONAL_MAPA, DURACAO_GERACAO

NUM_RAYS = 8


class ControladorNeural:

    def __init__(self, caminho_checkpoint):
        self.rede = RedeNeural()
        self.rede.carregar(caminho_checkpoint)
        self._tempo_geracao = 0.0
        self._ctx_obstaculos = []
        self._ctx_outros = []
        self._ctx_entrega = None

    def set_contexto(self, obstaculos, outros_agentes, zona_entrega, tempo_geracao):
        self._ctx_obstaculos = obstaculos
        self._ctx_outros = outros_agentes
        self._ctx_entrega = zona_entrega
        self._tempo_geracao = tempo_geracao

    def montar_inputs(self, agente):
        if agente.carregando_item and self._ctx_entrega is not None:
            alvo = pygame.Vector2(self._ctx_entrega.center)
        elif agente.pacote is not None and not agente.pacote.coletado:
            alvo = agente.pacote.pos
        else:
            alvo = agente.pos

        dx = alvo.x - agente.pos.x
        dy = alvo.y - agente.pos.y
        dist = agente.pos.distance_to(alvo)
        dir_alvo_x = dx / (dist + 1e-6)
        dir_alvo_y = dy / (dist + 1e-6)

        if self._ctx_entrega is not None:
            entrega_centro = pygame.Vector2(self._ctx_entrega.center)
            ddx = entrega_centro.x - agente.pos.x
            ddy = entrega_centro.y - agente.pos.y
            dist_ent = math.sqrt(ddx * ddx + ddy * ddy)
            dx_ent = ddx / (dist_ent + 1e-6)
            dy_ent = ddy / (dist_ent + 1e-6)
        else:
            dx_ent = dir_alvo_x
            dy_ent = dir_alvo_y

        vel = getattr(agente, "vel", pygame.Vector2(0, 0))
        if vel.length() > 0.01:
            heading = math.atan2(vel.y, vel.x)
        else:
            heading = math.atan2(dy, dx) if (dx or dy) else 0.0

        outros_ex_self = [a for a in self._ctx_outros if a is not agente]
        rays = []
        for i in range(NUM_RAYS):
            ang = heading + (i / NUM_RAYS) * 2 * math.pi
            d = raycast(agente.pos, ang, self._ctx_obstaculos, outros_ex_self,
                        LARGURA_MAPA, ALTURA_MAPA)
            rays.append(d / ALCANCE_RAY)

        return np.asarray([
            dir_alvo_x,
            dir_alvo_y,
            dist / DIAGONAL_MAPA,
            1.0 if agente.carregando_item else 0.0,
            dx_ent,
            dy_ent,
            min(vel.length(), 1.0),
            min(self._tempo_geracao / DURACAO_GERACAO, 1.0),
            *rays,
        ], dtype=np.float32)

    def forward(self, _inputs_ignorados):
        raise NotImplementedError("Use decidir(agente)")

    def decidir(self, agente):
        inputs = self.montar_inputs(agente)
        return self.rede.forward(inputs)
