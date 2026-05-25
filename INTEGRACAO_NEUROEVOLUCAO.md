# Onboarding — Integracao da rede neuroevoluida no projeto visual de armazem

> Documento de handoff entre duas sessoes do Claude Code em projetos diferentes.
> Quando aberto no outro projeto (`TCC_Testes/TCC`, branch `front/estoque-visual-pygame`),
> serve como contexto completo pra continuar a integracao sem perda de informacao.

---

## TL;DR

Existem **dois projetos** trabalhando na mesma ideia:

| Projeto | Caminho | Branch | Funcao |
|---|---|---|---|
| **TCC de pesquisa** | `C:\Users\arthu\OneDrive\Documentos\tcc_fases_transfer` | `main` | Lab de treinamento — onde a rede e treinada por neuroevolucao em 5 fases |
| **TCC visual** | `C:\Users\arthu\OneDrive\Documentos\TCC_Testes\TCC` | `front/estoque-visual-pygame` | Demo bonita — armazem com racks, agentes desenhados como pessoas, esteira |

**Objetivo da integracao:** rodar a rede pre-treinada do projeto de pesquisa
dentro do ambiente visual do TCC, demonstrando que a rede **generaliza** para
um ambiente realista. Esse e o MVP a ser apresentado para a banca.

---

## Projeto de pesquisa — o que ja foi feito

### Arquitetura da rede

- MLP feedforward: **16 inputs -> 32 (tanh) -> 16 (tanh) -> 2 (linear)**
- ~1 100 parametros
- Treinada por **algoritmo genetico** (neuroevolucao, sem backpropagation)
- Crossover por neuronio (coluna), mutacao gaussiana com decaimento
- Inicializacao Xavier

### Decisao tecnica importante: saida LINEAR

Inicialmente a saida usava `tanh` tambem. Isso causava **saturacao** —
outputs ficavam em ±1 e o agente so se movia em 4 diagonais.
Apos diagnostico, removemos o tanh da saida. **Resultado: a rede passou a
expressar qualquer direcao no plano.** Esse fix triplicou a taxa de entrega.

### Contrato I/O da rede (16 inputs, 2 outputs)

```
Inputs (normalizados):
  0  dx_alvo                            (direcao normalizada ate alvo atual)
  1  dy_alvo
  2  dist_alvo / DIAGONAL_MAPA
  3  carregando (0/1)
  4  dx_entrega                         (direcao ate ponto de entrega)
  5  dy_entrega
  6  |v| (modulo da velocidade)
  7  tempo_geracao_norm                 (tempo decorrido na geracao)
  8-15  raycasts (8 direcoes, alcance 220 px, normalizados)
        ray_0 = frente do agente
        ray_1 = +45 deg do heading
        ...
        ray_7 = -45 deg

Outputs:
  0  vx (linear, sera normalizado se |v|>1)
  1  vy
```

### Curriculo de 5 fases

| Fase | Cenario | Checkpoint resultante |
|---|---|---|
| 1 | navegar ate alvo unico, sem obstaculos | melhor_rede_fase1.npz |
| 2 | coletar pacote + entregar em outro ponto | melhor_rede_fase2.npz |
| 3 | 2 obstaculos no caminho, posicoes variaveis | melhor_rede_fase3.npz |
| 4 | 4 obstaculos no caminho, offset apertado (22 px) | melhor_rede_fase4.npz |
| 4.1 | 3 no caminho + 2 livres | melhor_rede_fase4_1.npz |
| 4.2 | 6 obstaculos livres (armazem real) | melhor_rede_fase4_2.npz |
| 5 | 4 obstaculos livres + 4 robos moveis | **melhor_rede_fase5.npz** ← usar este |

Os checkpoints **encadeados** (transfer learning): cada fase parte do final da anterior.

### Arquivos relevantes do projeto de pesquisa (origem)

```
tcc_fases_transfer/
├── rede_transfer.py             # classe RedeNeural — IMPORTAR no outro repo
├── simulador.py                 # contem a funcao raycast — EXTRAIR essa parte
├── treinar.py                   # loop GA
├── config_fase*.py              # parametros por fase
├── melhor_rede_fase5.npz        # ← arquivo treinado a copiar pro outro repo
├── figuras/
│   ├── arquitetura_rede.png     # ja usadas no README
│   ├── fluxo_sistema.png
│   └── curriculo_fases.png
└── README.md                    # documentacao completa
```

---

## Projeto visual — o que ja existe la

### Caminho

`C:\Users\arthu\OneDrive\Documentos\TCC_Testes\TCC`, branch `front/estoque-visual-pygame`

### Estrutura

```
TCC/
├── main.py                  # loop principal, treina populacao por geracao
├── agente.py                # classe Agente com brain=RedeNeural propria
├── rede_neural.py           # MLP 11 -> 12 -> 2 (tanh+tanh) — antiga, sera substituida
├── constantes.py            # LARGURA_MAPA=900, ALTURA_MAPA=600, etc.
├── renderer.py              # visualizacao bonita (racks, pessoas, esteira)
├── integracao.py            # outro experimento (acel/drag/bounce, sem armazem)
├── supabase_handler.py      # persiste metricas
├── teste_evolucao.py
├── teste_rede.py
└── requirements.txt
```

### Como o agente atual funciona

`agente.py` linhas 165–177 ja monta inputs **bem parecidos** com os nossos:

```python
inputs = [
    dx / LARGURA_MAPA,           # 0  =~ nosso input 0
    dy / ALTURA_MAPA,            # 1  =~ nosso input 1
    dist / DIAGONAL_MAPA,        # 2  == nosso input 2
    dist_robo / DIAGONAL_MAPA,   # 3  (so 1 robo mais proximo)
    dx_robo / LARGURA_MAPA,      # 4
    dy_robo / ALTURA_MAPA,       # 5
    dist_obst / DIAGONAL_MAPA,   # 6  (so 1 obstaculo mais proximo)
    dx_obst / LARGURA_MAPA,      # 7
    dy_obst / ALTURA_MAPA,       # 8
    carregando,                  # 9  == nosso input 3
    dist_entrega / DIAGONAL_MAPA # 10
]
```

E executa o movimento exatamente como a nossa rede espera:

```python
output = self.brain.forward(inputs)
self.vel = pygame.Vector2(output[0], output[1])
if self.vel.length() > 1:
    self.vel = self.vel.normalize()
```

**Pontos de coleta/entrega/colisao ja existem e funcionam.**

### Diferencas importantes vs nosso projeto

1. **Sensoriamento:** eles veem 1 obstaculo + 1 robo. Nossa rede ve 8 raycasts.
2. **Rede:** 11 -> 12 -> 2, tanh nas duas. A nossa: 16 -> 32 -> 16 -> 2, tanh nas
   ocultas + LINEAR na saida.
3. **Pacote:** la cada agente tem UM pacote por geracao (atribuido ao iniciar).
   Aqui no projeto de pesquisa o agente coleta e entrega, e o cenario reseta.

---

## Plano de integracao — 3 etapas

### Etapa 1 — Bridge minimo (sem mexer no main.py existente)

Criar no `TCC_Testes/TCC/`:

```
tcc_neuroevolucao/                # subpasta nova
├── __init__.py
├── rede_transfer.py              # copia do arquivo do projeto de pesquisa
├── raycast.py                    # so a funcao raycast extraida do simulador.py
└── melhor_rede_fase5.npz         # copia do checkpoint treinado

controlador_neural.py             # ARQUIVO NOVO no raiz — adapter
```

#### Conteudo de `raycast.py`

A funcao raycast original em `simulador.py` esta dentro da classe `Ambiente`.
Extrair como funcao livre que recebe a lista de obstaculos:

```python
import math
import pygame

ALCANCE_RAY = 220.0

def raycast(origem, angulo_rad, obstaculos, outros_agentes,
            largura, altura, alcance=ALCANCE_RAY):
    """Retorna distancia ate o primeiro obstaculo (ou alcance se nada)."""
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
```

#### Conteudo de `controlador_neural.py`

```python
import math
import pygame
import numpy as np

from tcc_neuroevolucao.rede_transfer import RedeNeural
from tcc_neuroevolucao.raycast import raycast, ALCANCE_RAY
from constantes import LARGURA_MAPA, ALTURA_MAPA, DIAGONAL_MAPA, DURACAO_GERACAO

NUM_RAYS = 8


class ControladorNeural:
    """Adapta a RedeNeural pre-treinada (16 inputs, saida linear) para o
    formato do projeto visual de armazem.

    Substituivel por self.brain no agente.py — implementa forward(inputs).
    Como o ambiente visual chama brain.forward(inputs_de_11), este controlador
    IGNORA esses inputs e remonta o vetor de 16 a partir do agente + ambiente.
    """

    def __init__(self, caminho_checkpoint):
        self.rede = RedeNeural()
        self.rede.carregar(caminho_checkpoint)
        self._tempo_geracao = 0.0
        self._ctx_obstaculos = []
        self._ctx_outros = []
        self._ctx_entrega = None

    def set_contexto(self, obstaculos, outros_agentes, zona_entrega, tempo_geracao):
        """Chamar UMA VEZ por frame antes do loop de agentes."""
        self._ctx_obstaculos = obstaculos
        self._ctx_outros = outros_agentes
        self._ctx_entrega = zona_entrega
        self._tempo_geracao = tempo_geracao

    def montar_inputs(self, agente):
        # alvo: pacote se nao carregando, entrega se carregando
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

        # vetor ate entrega (mesmo quando indo pegar pacote)
        if self._ctx_entrega is not None:
            entrega_centro = pygame.Vector2(self._ctx_entrega.center)
            ddx = entrega_centro.x - agente.pos.x
            ddy = entrega_centro.y - agente.pos.y
            dist_ent = math.sqrt(ddx*ddx + ddy*ddy)
            dx_ent = ddx / (dist_ent + 1e-6)
            dy_ent = ddy / (dist_ent + 1e-6)
        else:
            dx_ent = dir_alvo_x
            dy_ent = dir_alvo_y

        # heading do agente
        vel = getattr(agente, "vel", pygame.Vector2(0, 0))
        if vel.length() > 0.01:
            heading = math.atan2(vel.y, vel.x)
        else:
            heading = math.atan2(dy, dx) if (dx or dy) else 0.0

        # 8 raycasts em torno do heading (excluindo o proprio agente)
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

    # Interface compativel com a RedeNeural antiga (ignora inputs deles).
    # O `agente` precisa ser injetado externamente — ver patch em agente.py.
    def forward(self, _inputs_ignorados):
        raise NotImplementedError(
            "Use decidir(agente) — este controlador precisa do agente inteiro, "
            "nao apenas dos inputs."
        )

    def decidir(self, agente):
        inputs = self.montar_inputs(agente)
        return self.rede.forward(inputs)
```

### Etapa 2 — Patch no `agente.py` e `main.py`

#### Em `agente.py`

Adicionar atributo opcional e usar se presente:

```python
class Agente:
    def __init__(self, x, y):
        # ... codigo existente ...
        self.controlador_externo = None   # NOVO

    def _mover_ia(self, dt, target_pos, ...):
        # ... codigo existente ate ler inputs ...

        if self.controlador_externo is not None:
            output = self.controlador_externo.decidir(self)
        else:
            output = self.brain.forward(inputs)

        # ... resto igual ...
```

#### Em `main.py`

```python
USAR_REDE_PRETREINADA = True   # flag de modo demo
controlador = None

if USAR_REDE_PRETREINADA:
    from controlador_neural import ControladorNeural
    controlador = ControladorNeural("tcc_neuroevolucao/melhor_rede_fase5.npz")

# ... criar populacao normalmente ...
if controlador is not None:
    for agente in agentes:
        agente.controlador_externo = controlador

# no loop:
while running:
    # ... existente ...
    if controlador is not None:
        controlador.set_contexto(obstaculos, agentes, zona_entrega, tempo_geracao)

    for agente in agentes:
        agente.mover(dt, ...)

    # NAO executar criar_nova_geracao quando USAR_REDE_PRETREINADA estiver True
    # (a rede ja esta treinada, queremos so VER ela operando)
    if tempo_geracao >= DURACAO_GERACAO and not USAR_REDE_PRETREINADA:
        agentes, ... = criar_nova_geracao(...)
```

### Etapa 3 — Demo de apresentacao

Rodar `python main.py` com `USAR_REDE_PRETREINADA = True`. Esperado:
- agentes coletam pacotes dos racks
- entregam na zona vermelha de entrega
- desviam de obstaculos (racks) e uns dos outros via raycast
- comportamento muito melhor que a rede atual (11 inputs, 1 hidden layer)

Esse e o **MVP** a ser apresentado.

---

## Pontos de atencao

1. **Raycast custa CPU.** 8 raycasts × 20 agentes × 60 fps = 9600/s. Se ficar
   lento, reduzir NUM_RAYS pra 4 ou ALCANCE_RAY pra 150.

2. **Zona de entrega e Rect de 70×70.** A nossa rede foi treinada com PONTO.
   Usar `zona_entrega.center` como alvo. O agente pode "rodear" o centro;
   se for problema, usar `zona_entrega.collidepoint(agente.pos)` como criterio
   de chegada (ja e como o codigo deles esta — OK).

3. **Densidade de obstaculos.** O renderer cria 20 racks. A nossa rede foi
   treinada com max ~6 obstaculos. Pode ter dificuldade. **Solucao se necessario:**
   reduzir num_colunas em `renderer._criar_racks` de 5 para 3 (volta a 12 racks).

4. **Pacote por agente.** No projeto visual cada agente tem seu pacote desde o inicio
   (atribuido pelo `atribuir_pacotes_para_agentes`). Nossa rede espera detectar o
   pacote sempre na mesma posicao logica (`agente.pacote.pos`). Como o atributo
   ja existe, o controlador funciona sem mudanca.

5. **NUM_AGENTES default = 20.** Pode ficar denso. Comecar com 5–8 para validar.

---

## Comandos para o Claude do outro projeto rodar

Quando voce abrir `TCC_Testes/TCC` no VS Code e iniciar o Claude la:

```
1. Leia este onboarding (que estara em INTEGRACAO_NEUROEVOLUCAO.md)
2. Crie a pasta tcc_neuroevolucao/ e copie:
   - rede_transfer.py de C:\Users\arthu\OneDrive\Documentos\tcc_fases_transfer\
   - melhor_rede_fase5.npz de C:\Users\arthu\OneDrive\Documentos\tcc_fases_transfer\
3. Crie raycast.py extraindo a logica do simulador.py original
4. Crie controlador_neural.py conforme o template aqui
5. Faca o patch minimo em agente.py (atributo controlador_externo)
6. Adicione a flag USAR_REDE_PRETREINADA no main.py
7. Rode python main.py e veja se os agentes coletam/entregam usando a rede treinada
```

---

## Referencias

- Repo de pesquisa: `C:\Users\arthu\OneDrive\Documentos\tcc_fases_transfer`
  README explica arquitetura, curriculo, fitness — leia primeiro se for entender
  a rede do zero.

- Repo visual: `C:\Users\arthu\OneDrive\Documentos\TCC_Testes\TCC`
  branch `front/estoque-visual-pygame`

- Checkpoints disponiveis (treinados localmente, NAO commitados — gerar com
  `python treinar.py 1` ... `5` se nao existirem):
  - `melhor_rede_fase1.npz` ate `melhor_rede_fase5.npz`
  - Recomendado para integracao: **melhor_rede_fase5.npz**
