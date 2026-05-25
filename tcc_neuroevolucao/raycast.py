import math
import pygame

ALCANCE_RAY = 220.0


def raycast(origem, angulo_rad, obstaculos, outros_agentes,
            largura, altura, alcance=ALCANCE_RAY):
    passo = 6.0
    dx = math.cos(angulo_rad) * passo
    dy = math.sin(angulo_rad) * passo
    x, y = origem.x, origem.y
    n_passos = int(alcance / passo)
    for i in range(1, n_passos + 1):
        x += dx
        y += dy
        if x < 0 or x > largura or y < 0 or y > altura:
            return i * passo
        for obs in obstaculos:
            if obs.collidepoint(x, y):
                return i * passo
        for outro in outros_agentes:
            if outro is None:
                continue
            if (x - outro.pos.x) ** 2 + (y - outro.pos.y) ** 2 <= (outro.tamanho * 1.5) ** 2:
                return i * passo
    return alcance
