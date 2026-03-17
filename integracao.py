import os
import random

os.environ["LARGURA_MAPA"] = "1920"
os.environ["ALTURA_MAPA"] = "1080"

import pygame
from constantes import ALTURA_MAPA, LARGURA_MAPA, NUM_AGENTES, FPS
from agente import Agente

GEN_DURATION = 20.0
ELITE_RATIO = 0.2
MUTATION_RATE = 0.1
MUTATION_STRENGTH = 0.2
TARGET_RADIUS = 6
TARGET_SLOW_RADIUS = 120
PROGRESS_REWARD = 5.0
SPEED_PENALTY = 0.01
TIME_PENALTY = 0.1
REACH_BONUS = 200.0
WALL_PENALTY = 8.0
HOLD_BONUS = 16.0
HOLD_VEL_PENALTY = 0.8
DISTANCE_PENALTY = 0.004
OVERSHOOT_PENALTY = 8.0
WALL_RECOVER_REWARD = 2.0
MAX_SPEED = 220.0
MIN_SPEED = 25.0
ACCEL = 1000.0
DRAG = 0.85
WALL_BOUNCE = 0.3
WALL_PUSH_PENALTY = 4.0


def criar_agentes(n):
    return [AgenteSolido(LARGURA_MAPA/2, ALTURA_MAPA/4) for _ in range(n)]


def criar_agente_com_brain(brain):
    agente = AgenteSolido(LARGURA_MAPA/2, ALTURA_MAPA/4)
    agente.brain = brain
    agente.reset_stats()
    return agente


class AgenteSolido(Agente):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.reset_stats()

    def reset_stats(self):
        self.fitness = 0
        self.time_alive = 0.0
        self.prev_dist = None
        self.prev_wall_dist = None
        self.reached = False

    def mover(self, dt, resource_pos):
        self.time_alive += dt
        dx = resource_pos.x - self.pos.x
        dy = resource_pos.y - self.pos.y
        dist = self.pos.distance_to(resource_pos)

        inputs = [dx / LARGURA_MAPA, dy / ALTURA_MAPA, dist / 1000]

        output = self.brain.forward(inputs)

        accel_vec = pygame.Vector2(output[0], output[1])
        if accel_vec.length_squared() > 1e-6:
            accel_vec = accel_vec.normalize()
        self.vel += accel_vec * ACCEL * dt

        max_speed = MIN_SPEED + (MAX_SPEED - MIN_SPEED) * min(
            dist / TARGET_SLOW_RADIUS, 1.0
        )
        if self.vel.length() > max_speed:
            self.vel.scale_to_length(max_speed)

        self.vel *= DRAG
        self.pos += self.vel * dt

        if self.pos.x > LARGURA_MAPA:
            self.pos.x = LARGURA_MAPA
            self.vel.x *= -WALL_BOUNCE
        if self.pos.x < 0:
            self.pos.x = 0
            self.vel.x *= -WALL_BOUNCE
        if self.pos.y > ALTURA_MAPA:
            self.pos.y = ALTURA_MAPA
            self.vel.y *= -WALL_BOUNCE
        if self.pos.y < 0:
            self.pos.y = 0
            self.vel.y *= -WALL_BOUNCE

        if self.prev_dist is None:
            self.prev_dist = dist

        progress = self.prev_dist - dist
        if progress > 0:
            self.fitness += progress * PROGRESS_REWARD
        else:
            self.fitness += progress * OVERSHOOT_PENALTY

        self.fitness -= dist * DISTANCE_PENALTY
        self.fitness -= self.vel.length() * SPEED_PENALTY
        self.fitness -= TIME_PENALTY * dt

        if not self.reached and dist <= TARGET_RADIUS:
            self.reached = True
            time_factor = max(0.0, 1.0 - min(self.time_alive / GEN_DURATION, 1.0))
            self.fitness += REACH_BONUS * (0.25 + 0.75 * time_factor)

        if dist <= TARGET_RADIUS:
            self.fitness += HOLD_BONUS * dt
            self.fitness -= self.vel.length() * HOLD_VEL_PENALTY

        wall_margin = 30
        wall_dist = min(
            self.pos.x,
            self.pos.y,
            LARGURA_MAPA - self.pos.x,
            ALTURA_MAPA - self.pos.y,
        )
        if self.prev_wall_dist is None:
            self.prev_wall_dist = wall_dist

        if (
            self.pos.x <= wall_margin
            or self.pos.x >= LARGURA_MAPA - wall_margin
            or self.pos.y <= wall_margin
            or self.pos.y >= ALTURA_MAPA - wall_margin
        ):
            self.fitness -= WALL_PENALTY * dt
            if (
                (self.pos.x <= wall_margin and self.vel.x < 0)
                or (self.pos.x >= LARGURA_MAPA - wall_margin and self.vel.x > 0)
                or (self.pos.y <= wall_margin and self.vel.y < 0)
                or (self.pos.y >= ALTURA_MAPA - wall_margin and self.vel.y > 0)
            ):
                self.fitness -= WALL_PUSH_PENALTY * dt
            wall_progress = wall_dist - self.prev_wall_dist
            if wall_progress > 0:
                self.fitness += wall_progress * WALL_RECOVER_REWARD
        self.prev_wall_dist = wall_dist

        self.prev_dist = dist


def evoluir(agentes):
    agentes_ordenados = sorted(agentes, key=lambda a: a.fitness, reverse=True)
    elite_count = max(1, int(len(agentes_ordenados) * ELITE_RATIO))
    elite = agentes_ordenados[:elite_count]

    novos_agentes = []
    for agente in elite:
        novos_agentes.append(criar_agente_com_brain(agente.brain.copy()))

    while len(novos_agentes) < len(agentes_ordenados):
        parent = random.choice(elite)
        child_brain = parent.brain.copy()
        child_brain.mutate(rate=MUTATION_RATE, strength=MUTATION_STRENGTH)
        novos_agentes.append(criar_agente_com_brain(child_brain))

    return novos_agentes


def main():
    pygame.init()
    screen = pygame.display.set_mode(
        (LARGURA_MAPA, ALTURA_MAPA), pygame.FULLSCREEN
    )
    pygame.display.set_caption("Agentes + Rede Neural")

    clock = pygame.time.Clock()
    dt = 0.0
    running = True

    agentes = criar_agentes(NUM_AGENTES)
    resource_pos = pygame.Vector2(LARGURA_MAPA - 200, ALTURA_MAPA / 2)
    generation = 1
    gen_elapsed = 0.0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))

        for agente in agentes:
            agente.mover(dt, resource_pos)
            agente.desenhar(screen)

        pygame.draw.circle(screen, (0, 255, 0), resource_pos, 15)
        pygame.display.flip()

        dt = clock.tick(FPS) / 1000.0
        gen_elapsed += dt
        if gen_elapsed >= GEN_DURATION:
            agentes = evoluir(agentes)
            generation += 1
            gen_elapsed = 0.0
            pygame.display.set_caption(
                f"Agentes + Rede Neural | Geração {generation}"
            )

    pygame.quit()


if __name__ == "__main__":
    main()