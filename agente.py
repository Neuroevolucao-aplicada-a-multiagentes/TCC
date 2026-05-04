import pygame
from constantes import *
from rede_neural import RedeNeural


class Agente:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.tamanho = 10

        self.brain = RedeNeural()
        self.fitness = 0

        self.ultima_decisao = "Parado"

        self.pacote = None
        self.carregando_item = False
        self.itens_entregues = 0

        self.distancia_anterior = None
        self.colisoes = 0
        self.coletas = 0
        self.em_colisao = False

    def resetar(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)

        self.fitness = 0
        self.ultima_decisao = "Parado"

        self.pacote = None
        self.carregando_item = False
        self.itens_entregues = 0

        self.distancia_anterior = None
        self.colisoes = 0

        self.coletas = 0
        self.em_colisao = False

    def atribuir_pacote(self, pacote):
        self.pacote = pacote
        self.carregando_item = False
        self.distancia_anterior = None

    def get_rect(self, pos=None):
        if pos is None:
            pos = self.pos

        return pygame.Rect(
            int(pos.x - self.tamanho),
            int(pos.y - self.tamanho),
            self.tamanho * 2,
            self.tamanho * 2
        )

    def _get_robo_mais_proximo(self, outros_agentes):
        dist_robo = 1000
        dx_robo = 0
        dy_robo = 0

        if not outros_agentes:
            return dist_robo, dx_robo, dy_robo

        menor_dist = float("inf")

        for outro in outros_agentes:
            if outro is self:
                continue

            dx_tmp = outro.pos.x - self.pos.x
            dy_tmp = outro.pos.y - self.pos.y
            dist_tmp = self.pos.distance_to(outro.pos)

            if dist_tmp < menor_dist:
                menor_dist = dist_tmp
                dist_robo = dist_tmp
                dx_robo = dx_tmp
                dy_robo = dy_tmp

        return dist_robo, dx_robo, dy_robo

    def _get_obstaculo_mais_proximo(self, obstaculos):
        dist_obst = 1000
        dx_obst = 0
        dy_obst = 0

        if not obstaculos:
            return dist_obst, dx_obst, dy_obst

        menor_dist = float("inf")

        for obs in obstaculos:
            ponto_x = max(obs.left, min(self.pos.x, obs.right))
            ponto_y = max(obs.top, min(self.pos.y, obs.bottom))

            ponto = pygame.Vector2(ponto_x, ponto_y)

            dx_tmp = ponto.x - self.pos.x
            dy_tmp = ponto.y - self.pos.y
            dist_tmp = self.pos.distance_to(ponto)

            if dist_tmp < menor_dist:
                menor_dist = dist_tmp
                dist_obst = dist_tmp
                dx_obst = dx_tmp
                dy_obst = dy_tmp

        return dist_obst, dx_obst, dy_obst

    def _colidiu_com_obstaculos(self, rect, obstaculos):
        if not obstaculos:
            return False

        return any(rect.colliderect(obs) for obs in obstaculos)

    def _colidiu_com_agentes(self, rect, outros_agentes):
        if not outros_agentes:
            return False

        for outro in outros_agentes:
            if outro is self:
                continue

            if rect.colliderect(outro.get_rect()):
                return True

        return False

    def _fora_do_mapa(self, rect):
        return (
            rect.left < 0 or
            rect.right > LARGURA_MAPA or
            rect.top < 0 or
            rect.bottom > ALTURA_MAPA
        )

    def _definir_alvo(self, zona_entrega_rect):
        if self.carregando_item and zona_entrega_rect is not None:
            return pygame.Vector2(zona_entrega_rect.center)

        if self.pacote is not None and not self.pacote.coletado:
            return self.pacote.pos

        return self.pos

    def _mover_ia(self, dt, target_pos, zona_entrega_rect=None, obstaculos=None, outros_agentes=None):
        dx = target_pos.x - self.pos.x
        dy = target_pos.y - self.pos.y
        dist = self.pos.distance_to(target_pos)

        dist_robo, dx_robo, dy_robo = self._get_robo_mais_proximo(outros_agentes)
        dist_obst, dx_obst, dy_obst = self._get_obstaculo_mais_proximo(obstaculos)

        carregando = 1.0 if self.carregando_item else 0.0

        if zona_entrega_rect is not None:
            entrega_pos = pygame.Vector2(zona_entrega_rect.center)
            dist_entrega = self.pos.distance_to(entrega_pos)
        else:
            dist_entrega = DIAGONAL_MAPA

        inputs = [
            dx / LARGURA_MAPA,
            dy / ALTURA_MAPA,
            dist / DIAGONAL_MAPA,
            dist_robo / DIAGONAL_MAPA,
            dx_robo / LARGURA_MAPA,
            dy_robo / ALTURA_MAPA,
            dist_obst / DIAGONAL_MAPA,
            dx_obst / LARGURA_MAPA,
            dy_obst / ALTURA_MAPA,
            carregando,
            dist_entrega / DIAGONAL_MAPA
        ]

        output = self.brain.forward(inputs)

        self.vel = pygame.Vector2(output[0], output[1])

        if self.vel.length() > 1:
            self.vel = self.vel.normalize()

        deslocamento = self.vel * VELOCIDADE_AGENTE * dt

        self.ultima_decisao = (
            f"IA v=({self.vel.x:.2f}, {self.vel.y:.2f}) "
            f"alvo={dist:.1f}"
        )

        return deslocamento, dist, dist_obst

    def mover(self, dt, zona_entrega_rect=None, obstaculos=None, outros_agentes=None):
        target_pos = self._definir_alvo(zona_entrega_rect)

        deslocamento, dist, dist_obst = self._mover_ia(
            dt,
            target_pos,
            zona_entrega_rect=zona_entrega_rect,
            obstaculos=obstaculos,
            outros_agentes=outros_agentes
        )

        colidiu = False

        nova_pos_x = pygame.Vector2(self.pos.x + deslocamento.x, self.pos.y)
        rect_x = self.get_rect(nova_pos_x)

        if self._fora_do_mapa(rect_x):
            colidiu = True
        elif self._colidiu_com_obstaculos(rect_x, obstaculos):
            colidiu = True
        elif self._colidiu_com_agentes(rect_x, outros_agentes):
            colidiu = True
        else:
            self.pos.x = nova_pos_x.x

        nova_pos_y = pygame.Vector2(self.pos.x, self.pos.y + deslocamento.y)
        rect_y = self.get_rect(nova_pos_y)

        if self._fora_do_mapa(rect_y):
            colidiu = True
        elif self._colidiu_com_obstaculos(rect_y, obstaculos):
            colidiu = True
        elif self._colidiu_com_agentes(rect_y, outros_agentes):
            colidiu = True
        else:
            self.pos.y = nova_pos_y.y

        if colidiu and not self.em_colisao:
            self.colisoes += 1
            self.fitness -= 50
            self.em_colisao = True

        if not colidiu:
            self.em_colisao = False

        if self.distancia_anterior is not None and dist < DIAGONAL_MAPA * 0.99:
            progresso = self.distancia_anterior - dist
            self.fitness += progresso * 2

        self.distancia_anterior = dist

        if self.pacote is not None or self.carregando_item:
            self.fitness += 1 / (dist + 1)

        if self.vel.length() < 0.03:
            self.fitness -= 0.01

        if self.carregando_item:
            self.fitness += 0.02

    def tentar_pegar_pacote(self):
        if self.pacote is None:
            return False

        if self.pacote.coletado:
            return False

        if self.carregando_item:
            return False

        distancia = self.pos.distance_to(self.pacote.pos)

        if distancia <= 15:
            self.carregando_item = True
            self.pacote.coletado = True
            self.ultima_decisao = "Pegou pacote"
            self.coletas += 1
            self.fitness += 500
            self.distancia_anterior = None
            return True

        return False

    def tentar_entregar_pacote(self, zona_entrega_rect):
        if not self.carregando_item:
            return False

        if zona_entrega_rect.colliderect(self.get_rect()):
            self.carregando_item = False
            self.itens_entregues += 1
            self.ultima_decisao = "Entregou pacote"
            self.fitness += 2000
            self.pacote = None
            self.distancia_anterior = None
            return True

        return False

    def desenhar(self, screen):
        cor = (0, 180, 255)

        if self.carregando_item:
            cor = (255, 180, 0)

        pygame.draw.circle(
            screen,
            cor,
            (int(self.pos.x), int(self.pos.y)),
            self.tamanho
        )