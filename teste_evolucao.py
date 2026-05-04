import numpy as np
from rede_neural import RedeNeural


POPULACAO = 100
GERACOES = 200
ELITE = 15
TAXA_MUTACAO = 0.15
FORCA_MUTACAO = 0.25


# Casos de teste:
# entrada = [dx_alvo, dy_alvo, dist_alvo, dist_robo, dx_robo, dy_robo]
# saída esperada = [vx, vy]
# SUBSTITUIR o bloco CASOS_TESTE por:
CASOS_TESTE = [
    # [dx, dy, dist, dist_robo, dx_robo, dy_robo, dist_obst, dx_obst, dy_obst, carregando, dist_entrega]
    ([0.8, 0.0, 0.8, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0], [1.0, 0.0]),
    ([-0.8, 0.0, 0.8, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0], [-1.0, 0.0]),
    ([0.0, -0.8, 0.8, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0], [0.0, -1.0]),
    ([0.0, 0.8, 0.8, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0], [0.0, 1.0]),
    ([0.7, 0.0, 0.7, 0.05, 0.3, 0.0, 0.3, 0.2, 0.0, 0.0, 0.8], [-0.6, 0.4]),
    ([-0.7, 0.0, 0.7, 0.05, -0.3, 0.0, 0.3, -0.2, 0.0, 0.0, 0.8], [0.6, -0.4]),
    ([0.5, 0.0, 0.5, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.3], [1.0, 0.0]),
    ([-0.5, 0.0, 0.5, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.3], [-1.0, 0.0]),
]

def calcular_fitness(rede):
    fitness_total = 0.0

    for entrada, saida_esperada in CASOS_TESTE:
        saida_rede = rede.forward(entrada)

        erro = np.sum((saida_rede - np.array(saida_esperada)) ** 2)
        fitness_caso = max(0, 2 - erro)
        
        fitness_total += fitness_caso

    return fitness_total


def criar_populacao(tamanho):
    return [RedeNeural() for _ in range(tamanho)]


def avaliar_populacao(populacao):
    resultados = []

    for rede in populacao:
        fitness = calcular_fitness(rede)
        resultados.append((rede, fitness))

    resultados.sort(key=lambda x: x[1], reverse=True)
    return resultados


def reproduzir(nova_base, tamanho_populacao, taxa_mutacao, forca_mutacao):
    nova_populacao = []

    # mantém a elite sem alteração
    for rede, _ in nova_base:
        nova_populacao.append(rede.copy())

    # gera filhos até completar a população
    while len(nova_populacao) < tamanho_populacao:
        pai, _ = nova_base[np.random.randint(len(nova_base))]
        filho = pai.copy()
        filho.mutate(rate=taxa_mutacao, strength=forca_mutacao)
        nova_populacao.append(filho)

    return nova_populacao


def mostrar_melhor_rede(rede):
    print("\nMelhor rede testada nos cenários:")
    for i, (entrada, saida_esperada) in enumerate(CASOS_TESTE, start=1):
        saida_rede = rede.forward(entrada)
        print(f"\nCaso {i}")
        print(f"Entrada:        {np.round(entrada, 3)}")
        print(f"Saída esperada: {np.round(saida_esperada, 3)}")
        print(f"Saída da rede:  {np.round(saida_rede, 3)}")


def evoluir():
    populacao = criar_populacao(POPULACAO)

    melhor_fitness_historico = []
    media_fitness_historico = []

    for geracao in range(1, GERACOES + 1):
        avaliados = avaliar_populacao(populacao)

        melhor_rede, melhor_fitness = avaliados[0]
        media_fitness = sum(f for _, f in avaliados) / len(avaliados)

        melhor_fitness_historico.append(melhor_fitness)
        media_fitness_historico.append(media_fitness)

        print(
            f"Geração {geracao:03d} | "
            f"Melhor fitness: {melhor_fitness:.4f} | "
            f"Fitness médio: {media_fitness:.4f}"
        )

        elite = avaliados[:ELITE]
        populacao = reproduzir(elite, POPULACAO, TAXA_MUTACAO, FORCA_MUTACAO)

    print("\n" + "=" * 60)
    print("EVOLUÇÃO FINALIZADA")
    print("=" * 60)

    avaliados = avaliar_populacao(populacao)
    melhor_rede, melhor_fitness = avaliados[0]

    print(f"\nMelhor fitness final: {melhor_fitness:.4f}")
    mostrar_melhor_rede(melhor_rede)

    print("\nHistórico final:")
    print(f"Melhor fitness encontrado: {max(melhor_fitness_historico):.4f}")
    print(f"Último fitness médio: {media_fitness_historico[-1]:.4f}")


if __name__ == "__main__":
    evoluir()
