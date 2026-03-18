import pygame
import random
from constantes import *
from rede_neural import RedeNeural


class Agente:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x,y)

        self.vel = pygame.Vector2(0,0)

        self.tamanho = 10

        self.brain = RedeNeural()
        self.fitness = 0


    def mover(self, dt, resource_pos, obstaculos=None):
        dx = resource_pos.x - self.pos.x
        dy = resource_pos.y - self.pos.y
        dist = self.pos.distance_to(resource_pos)

        inputs = [dx / LARGURA_MAPA, dy / ALTURA_MAPA, dist / 1000]

        output = self.brain.forward(inputs)

        self.vel = pygame.Vector2(output[0], output[1])
        deslocamento = self.vel * 200 * dt

        if obstaculos:
            novo_x = self.pos.x + deslocamento.x
            hitbox_x = pygame.Rect(int(novo_x - self.tamanho), int(self.pos.y - self.tamanho), self.tamanho * 2, self.tamanho * 2)
            if not any(hitbox_x.colliderect(obs) for obs in obstaculos):
                self.pos.x = novo_x

            novo_y = self.pos.y + deslocamento.y
            hitbox_y = pygame.Rect(int(self.pos.x - self.tamanho), int(novo_y - self.tamanho), self.tamanho * 2, self.tamanho * 2)
            if not any(hitbox_y.colliderect(obs) for obs in obstaculos):
                self.pos.y = novo_y
        else:
            self.pos += deslocamento


        #volta no mapa
        if self.pos.x > LARGURA_MAPA: self.pos.x = 0
        if self.pos.x < 0: self.pos.x = LARGURA_MAPA
        if self.pos.y > ALTURA_MAPA: self.pos.y = 0
        if self.pos.y < 0: self.pos.y = ALTURA_MAPA

        self.fitness += 1/(dist + 1)


    def desenhar(self, screen):
        pygame.draw.circle(screen, (255,0,0), (int(self.pos.x), int(self.pos.y)), self.tamanho)
    
    
