import pygame
from constantes import *
from rede_neural import RedeNeural
import random


class Agente:
    def __init__(self, x, y, controlavel=False):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.tamanho = 10

        self.brain = RedeNeural()
        self.fitness = 0

        self.controlavel = controlavel
        self.ultima_decisao = "Parado"

        self.carregando_item = False
        self.itens_entregues = 0

    def get_rect(self, pos=None):
        if pos is None:
            pos = self.pos
        return pygame.Rect(
            int(pos.x - self.tamanho),
            int(pos.y - self.tamanho),
            self.tamanho * 2,
            self.tamanho * 2
        )

    def _mover_manual(self, dt):
        # leitura do teclado
        keys = pygame.key.get_pressed()
        direcao = pygame.Vector2(0, 0)

        if keys[pygame.K_LEFT]:
            direcao.x = -1
        if keys[pygame.K_RIGHT]:
            direcao.x = 1
        if keys[pygame.K_UP]:
            direcao.y = -1
        if keys[pygame.K_DOWN]:
            direcao.y = 1

        if direcao.length() > 0:
            direcao = direcao.normalize()

        self.vel = direcao
        deslocamento = self.vel * VELOCIDADE_AGENTE * dt

        if direcao.length() == 0:
            self.ultima_decisao = "Parado"
        else:
            self.ultima_decisao = f"Controle manual ({direcao.x:.1f}, {direcao.y:.1f})"

        return deslocamento

    def _mover_ia(self, dt, resource_pos):
        dx = resource_pos.x - self.pos.x
        dy = resource_pos.y - self.pos.y
        dist = self.pos.distance_to(resource_pos)

        inputs = [dx / LARGURA_MAPA, dy / ALTURA_MAPA, dist / 1000]
        output = self.brain.forward(inputs)

        self.vel = pygame.Vector2(output[0], output[1])
        deslocamento = self.vel * VELOCIDADE_AGENTE * dt
        self.ultima_decisao = f"IA ({self.vel.x:.2f}, {self.vel.y:.2f})"

        return deslocamento, dist

    # criação da hit box com o rect
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

    # removido o wrap around (sair de um borda e aparecer em outra)
    def _fora_do_mapa(self, rect):
        return (
            rect.left < 0 or
            rect.right > LARGURA_MAPA or
            rect.top < 0 or
            rect.bottom > ALTURA_MAPA
        )

    # penalidade no fitness nas colisões, valores podem ser alterados
    def mover(self, dt, resource_pos, obstaculos=None, outros_agentes=None):
        penalidade_colisao = 0

        if self.controlavel:
            deslocamento = self._mover_manual(dt)
            dist = self.pos.distance_to(resource_pos)
        else:
            deslocamento, dist = self._mover_ia(dt, resource_pos)

        # testa movimento em X
        nova_pos_x = pygame.Vector2(self.pos.x + deslocamento.x, self.pos.y)
        rect_x = self.get_rect(nova_pos_x)

        if self._fora_do_mapa(rect_x):
            penalidade_colisao -= 1
        elif self._colidiu_com_obstaculos(rect_x, obstaculos):
            penalidade_colisao -= 2
        elif self._colidiu_com_agentes(rect_x, outros_agentes):
            penalidade_colisao -= 3
        else:
            self.pos.x = nova_pos_x.x

        # testa movimento em Y
        nova_pos_y = pygame.Vector2(self.pos.x, self.pos.y + deslocamento.y)
        rect_y = self.get_rect(nova_pos_y)

        if self._fora_do_mapa(rect_y):
            penalidade_colisao -= 1
        elif self._colidiu_com_obstaculos(rect_y, obstaculos):
            penalidade_colisao -= 2
        elif self._colidiu_com_agentes(rect_y, outros_agentes):
            penalidade_colisao -= 3
        else:
            self.pos.y = nova_pos_y.y

        # recompensa por proximidade do recurso
        self.fitness += 1 / (dist + 1)

        # penalidade por colisão
        self.fitness += penalidade_colisao

    def desenhar(self, screen):
        cor = (255, 255, 0) if self.controlavel else (255, 0, 0)
        pygame.draw.circle(screen, cor, (int(self.pos.x), int(self.pos.y)), self.tamanho)

    def pode_pegar_item(self):
        return not self.carregando_item

    def tentar_pegar_item(self, item):
        if item is None or item.coletado:
            return False

        if self.carregando_item:
            return False

        distancia = self.pos.distance_to(item.pos)

        if distancia <= 12:
            self.carregando_item = True
            item.coletado = True
            self.ultima_decisao = "Pegou item"
            self.fitness += 10
            print("ITEM COLETADO")
            return True

        return False

    def tentar_entregar_item(self, zona_entrega_rect):
        if not self.carregando_item:
            return False

        if zona_entrega_rect.colliderect(self.get_rect()):
            self.carregando_item = False
            self.itens_entregues += 1
            self.ultima_decisao = "Entregou item"
            self.fitness += 20
            return True

        return False