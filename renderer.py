import math
from dataclasses import dataclass
from typing import Iterable, List, Tuple

import pygame


Color = Tuple[int, int, int]


@dataclass
class ShelfCell:
    col: int
    row: int
    quantidade: int
    tipo_produto: str


@dataclass
class ViewState:
    shelves: List[ShelfCell]
    agentes_pos: List[Tuple[float, float]]
    total_produtos: int
    baixo_estoque: int
    decisoes_recentes: List[str]


class EstoqueAdapter:
    """
    Camada de leitura de estado para visualização.
    Não altera a lógica existente, apenas consome dados já atualizados.
    """

    def __init__(self, largura_mapa: int, altura_mapa: int, cols: int = 12, rows: int = 8):
        self.largura_mapa = largura_mapa
        self.altura_mapa = altura_mapa
        self.cols = cols
        self.rows = rows
        self._cell_w = max(1, largura_mapa / cols)
        self._cell_h = max(1, altura_mapa / rows)

    def _status_quantidade(self, quantidade: int) -> str:
        if quantidade <= 2:
            return "baixo"
        if quantidade <= 4:
            return "medio"
        return "ok"

    def _direcao(self, vx: float, vy: float) -> str:
        if abs(vx) < 0.05 and abs(vy) < 0.05:
            return "parado"
        angulo = math.degrees(math.atan2(-vy, vx)) % 360
        if 22.5 <= angulo < 67.5:
            return "nordeste"
        if 67.5 <= angulo < 112.5:
            return "norte"
        if 112.5 <= angulo < 157.5:
            return "noroeste"
        if 157.5 <= angulo < 202.5:
            return "oeste"
        if 202.5 <= angulo < 247.5:
            return "sudoeste"
        if 247.5 <= angulo < 292.5:
            return "sul"
        if 292.5 <= angulo < 337.5:
            return "sudeste"
        return "leste"

    def _tipo_produto(self, agente, index: int) -> str:
        if hasattr(agente, "tipo_produto"):
            return str(agente.tipo_produto)
        return f"P{(index % 4) + 1}"

    def ler_estado(self, agentes: Iterable, resource_pos: pygame.Vector2) -> ViewState:
        shelf_map = {}
        agentes_pos: List[Tuple[float, float]] = []
        decisoes_recentes: List[str] = []

        for i, agente in enumerate(agentes):
            x = float(getattr(agente, "pos").x)
            y = float(getattr(agente, "pos").y)
            agentes_pos.append((x, y))

            col = min(self.cols - 1, max(0, int(x / self._cell_w)))
            row = min(self.rows - 1, max(0, int(y / self._cell_h)))
            chave = (col, row)

            if chave not in shelf_map:
                shelf_map[chave] = {"quantidade": 0, "tipo": self._tipo_produto(agente, i)}
            shelf_map[chave]["quantidade"] += 1

            if hasattr(agente, "ultima_decisao"):
                decisao = str(agente.ultima_decisao)
            else:
                vel = getattr(agente, "vel", pygame.Vector2(0, 0))
                direcao = self._direcao(float(vel.x), float(vel.y))
                decisao = f"Agente {i + 1}: direcao {direcao}"
            if len(decisoes_recentes) < 5:
                decisoes_recentes.append(decisao)

        shelves = [
            ShelfCell(col=col, row=row, quantidade=dados["quantidade"], tipo_produto=dados["tipo"])
            for (col, row), dados in shelf_map.items()
        ]
        total_produtos = sum(c.quantidade for c in shelves)
        baixo_estoque = sum(1 for c in shelves if self._status_quantidade(c.quantidade) == "baixo")

        if not decisoes_recentes:
            decisoes_recentes = ["Nenhuma decisao disponivel"]

        return ViewState(
            shelves=shelves,
            agentes_pos=agentes_pos,
            total_produtos=total_produtos,
            baixo_estoque=baixo_estoque,
            decisoes_recentes=decisoes_recentes,
        )


class EstoqueRenderer:
    def __init__(
        self,
        screen: pygame.Surface,
        largura_mapa: int,
        altura_mapa: int,
        fps: int,
        cols: int = 12,
        rows: int = 8,
    ):
        self.screen = screen
        self.largura = largura_mapa
        self.altura = altura_mapa
        self.fps = fps
        self.cols = cols
        self.rows = rows
        self.adapter = EstoqueAdapter(largura_mapa, altura_mapa, cols=cols, rows=rows)
        self.font = pygame.font.SysFont("arial", 14)
        self._cell_w = self.largura / self.cols
        self._cell_h = self.altura / self.rows

        self.cor_fundo: Color = (148, 156, 168)
        self.cor_doca: Color = (118, 126, 138)
        self.cor_faixa: Color = (238, 196, 74)
        self.cor_corredor: Color = (170, 178, 190)
        self.cor_grid: Color = (130, 138, 150)
        self.cor_sombra: Color = (95, 100, 107)
        self.cor_rack: Color = (72, 79, 89)
        self.cor_rack_topo: Color = (100, 111, 125)
        self.cor_caixa: Color = (172, 130, 86)
        self.cor_ok: Color = (72, 172, 93)
        self.cor_medio: Color = (222, 178, 66)
        self.cor_baixo: Color = (199, 77, 66)
        self.cor_texto: Color = (30, 35, 40)
        self.cor_agente: Color = (64, 136, 213)
        self.cor_capacete: Color = (247, 210, 73)
        self.cor_recurso: Color = (66, 93, 214)
        self.rack_rects = self._criar_racks()

    def _status_cor(self, quantidade: int) -> Color:
        if quantidade <= 2:
            return self.cor_baixo
        if quantidade <= 4:
            return self.cor_medio
        return self.cor_ok

    def _desenhar_piso(self):
        self.screen.fill(self.cor_fundo)

        doca = pygame.Rect(0, 0, self.largura, int(self.altura * 0.12))
        pygame.draw.rect(self.screen, self.cor_doca, doca)
        pygame.draw.line(
            self.screen, (90, 96, 105),
            (0, int(self.altura * 0.12)),
            (self.largura, int(self.altura * 0.12)),
            2,
        )

        corredor_h = pygame.Rect(0, int(self.altura * 0.44), self.largura, int(self.altura * 0.09))
        corredor_v = pygame.Rect(int(self.largura * 0.49), int(self.altura * 0.12), int(self.largura * 0.09), int(self.altura * 0.88))
        pygame.draw.rect(self.screen, self.cor_corredor, corredor_h, border_radius=6)
        pygame.draw.rect(self.screen, self.cor_corredor, corredor_v, border_radius=6)

    def _desenhar_grid_base(self):
        for col in range(self.cols + 1):
            x = int(col * self._cell_w)
            pygame.draw.line(self.screen, self.cor_grid, (x, 0), (x, self.altura), 1)
        for row in range(self.rows + 1):
            y = int(row * self._cell_h)
            pygame.draw.line(self.screen, self.cor_grid, (0, y), (self.largura, y), 1)

    def _desenhar_estrutura(self):
        cor_parede = (108, 116, 128)
        cor_parede_top = (138, 146, 158)
        espessura = 8

        pygame.draw.rect(self.screen, cor_parede,
                         pygame.Rect(0, 0, espessura, self.altura))
        pygame.draw.rect(self.screen, cor_parede,
                         pygame.Rect(self.largura - espessura, 0, espessura, self.altura))
        pygame.draw.rect(self.screen, cor_parede,
                         pygame.Rect(0, self.altura - espessura, self.largura, espessura))

        pygame.draw.rect(self.screen, cor_parede_top,
                         pygame.Rect(0, 0, espessura, 4))
        pygame.draw.rect(self.screen, cor_parede_top,
                         pygame.Rect(self.largura - espessura, 0, espessura, 4))

    def _criar_racks(self) -> List[pygame.Rect]:
        racks: List[pygame.Rect] = []
        num_colunas = 3
        linhas = [2, 3, 5, 6]
        rack_w = int(self._cell_w) - 14
        rack_h = int(self._cell_h) - 30

        x_min = int(self.largura * 0.14)
        x_max = int(self.largura * 0.86) - rack_w
        espaco = max(1, x_max - x_min)
        passo = espaco / max(1, num_colunas - 1)

        for i in range(num_colunas):
            x = int(x_min + (i * passo))
            for row in linhas:
                y = int(row * self._cell_h)
                corpo = pygame.Rect(x, y + 6, rack_w, rack_h)
                racks.append(corpo)
        return racks

    def obter_obstaculos(self) -> List[pygame.Rect]:
        return [rack.copy() for rack in self.rack_rects]

    def _desenhar_layout_racks(self):
        for corpo in self.rack_rects:
            sombra = pygame.Rect(corpo.x + 3, corpo.y + 4, corpo.w, corpo.h)
            topo = pygame.Rect(corpo.x + 2, corpo.y + 2, corpo.w - 4, int(corpo.h * 0.35))

            pygame.draw.rect(self.screen, self.cor_sombra, sombra, border_radius=8)
            pygame.draw.rect(self.screen, self.cor_rack, corpo, border_radius=6)
            pygame.draw.rect(self.screen, self.cor_rack_topo, topo, border_radius=4)

            caixa_1 = pygame.Rect(corpo.x + 8, corpo.y + corpo.h - 14, 10, 8)
            caixa_2 = pygame.Rect(corpo.x + 21, corpo.y + corpo.h - 14, 10, 8)
            pygame.draw.rect(self.screen, self.cor_caixa, caixa_1, border_radius=2)
            pygame.draw.rect(self.screen, self.cor_caixa, caixa_2, border_radius=2)

    def _desenhar_agentes(self, agentes):
        paleta = [
            (64, 136, 213),
            (92, 176, 107),
            (199, 104, 92),
            (147, 117, 212),
        ]

        for i, agente in enumerate(agentes):
            x = agente.pos.x
            y = agente.pos.y
            px = int(x)
            py = int(y)

            if getattr(agente, "controlavel", False):
                cor_uniforme = (255, 170, 0)  # laranja para destacar
            else:
                cor_uniforme = paleta[i % len(paleta)]

            pygame.draw.ellipse(self.screen, (70, 76, 84),
                                pygame.Rect(px - 7, py + 6, 14, 4))

            tronco = pygame.Rect(px - 5, py - 1, 10, 9)
            pygame.draw.rect(self.screen, cor_uniforme, tronco, border_radius=3)

            pygame.draw.circle(self.screen, (236, 204, 175), (px, py - 4), 4)
            pygame.draw.circle(self.screen, self.cor_capacete, (px, py - 7), 4)
            pygame.draw.rect(self.screen, self.cor_capacete,
                             pygame.Rect(px - 4, py - 7, 8, 2), border_radius=1)

            if getattr(agente, "controlavel", False):
                pygame.draw.circle(self.screen, (255, 255, 255), (px, py - 12), 2)

    def renderizar(self, agentes: Iterable, resource_pos: pygame.Vector2, item=None, zona_entrega=None):
        estado = self.adapter.ler_estado(agentes, resource_pos)
        self._desenhar_piso()
        self._desenhar_estrutura()
        self._desenhar_grid_base()
        self._desenhar_layout_racks()
        self._desenhar_agentes(list(agentes))

        if zona_entrega is not None:
            self.desenhar_zona_entrega(zona_entrega)

        if item is not None:
            self.desenhar_item(item)


    def desenhar_zona_entrega(self, zona_rect: pygame.Rect):
        pygame.draw.rect(self.screen, (190, 60, 60), zona_rect, border_radius=8)
        pygame.draw.rect(self.screen, (240, 240, 240), zona_rect, 2, border_radius=8)

        texto = self.font.render("ENTREGA", True, (255, 255, 255))
        self.screen.blit(texto, (zona_rect.x + 6, zona_rect.y + 8))
    
    def desenhar_item(self, item):
        if item is None or item.coletado:
            return

        x = int(item.pos.x)
        y = int(item.pos.y)

        pygame.draw.circle(self.screen, (70, 90, 220), (x, y), 6)
        pygame.draw.circle(self.screen, (220, 230, 255), (x, y), 2)
