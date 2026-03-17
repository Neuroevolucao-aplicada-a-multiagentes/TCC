import numpy as np
from rede_neural import RedeNeural

def print_titulo(texto):
    print('\n' + '=' * 60)
    print(texto)
    print('=' * 60)

def print_saida_rede(nome, rede, entradas_teste):
    print(f'\n{nome}')
    for i, entrada in enumerate(entradas_teste, start=1):
        saida = rede.forward(entrada)
        print(f'Caso {i}:')
        print(f"  Entrada: {np.round(entrada, 3)}")
        print(f"  Saída:   {np.round(saida, 3)}")

def comparar_pesos(rede1, rede2):
    diff_w1 = np.sum(np.abs(rede1.w1 - rede2.w1))
    diff_w2 = np.sum(np.abs(rede1.w2 - rede2.w2))
    diff_b1 = np.sum(np.abs(rede1.b1 - rede2.b1))
    diff_b2 = np.sum(np.abs(rede1.b2 - rede2.b2))

    print("\nDiferença total entre parâmetros:")
    print(f"w1: {diff_w1:.6f}")
    print(f"w2: {diff_w2:.6f}")
    print(f"b1: {diff_b1:.6f}")
    print(f"b2: {diff_b2:.6f}")

def contar_parametros_alterados(rede1, rede2):
    alt_w1 = np.sum(rede1.w1 != rede2.w1)
    alt_w2 = np.sum(rede1.w2 != rede2.w2)
    alt_b1 = np.sum(rede1.b1 != rede2.b1)
    alt_b2 = np.sum(rede1.b2 != rede2.b2)

    total_alterados = alt_w1 + alt_w2 + alt_b1 + alt_b2
    total_parametros = (
        rede1.w1.size + rede1.w2.size + rede1.b1.size + rede1.b2.size
    )

    print("\nQuantidade de parâmetros alterados:")
    print(f"w1: {alt_w1}")
    print(f"w2: {alt_w2}")
    print(f"b1: {alt_b1}")
    print(f"b2: {alt_b2}")
    print(f"Total alterados: {total_alterados}/{total_parametros}")


def gerar_filhos(rede_pai, quantidade=5, rate=0.1, strength=0.2):
    filhos = []

    for _ in range(quantidade):
        filho = rede_pai.copy()
        filho.mutate(rate=rate, strength=strength)
        filhos.append(filho)

    return filhos

entradas_teste = [
    [0.8, 0.1, 0.7, 0.9, 0.0, 0.0],     # alvo mais à direita, sem robô próximo
    [-0.8, 0.0, 0.7, 0.9, 0.0, 0.0],    # alvo à esquerda
    [0.0, -0.9, 0.8, 0.9, 0.0, 0.0],    # alvo acima
    [0.1, 0.1, 0.2, 0.1, -0.2, 0.0],    # alvo perto, robô bem próximo
    [0.6, 0.4, 0.8, 0.05, 0.1, -0.1],   # alvo longe, risco de colisão
]



print_titulo("CRIANDO REDE PAI")
rede_pai = RedeNeural()
print("w1:", rede_pai.w1.shape)
print("w2:", rede_pai.w2.shape)
print("Rede pai criada com sucesso.")

print_titulo("SAÍDAS DA REDE PAI")
print_saida_rede("Rede Pai", rede_pai, entradas_teste)

print_titulo("CRIANDO FILHO POR CÓPIA")
filho = rede_pai.copy()
print("Filho criado por cópia.")

print_titulo("COMPARANDO PAI E FILHO ANTES DA MUTAÇÃO")
comparar_pesos(rede_pai, filho)
contar_parametros_alterados(rede_pai, filho)

print_titulo("SAÍDAS DO FILHO ANTES DA MUTAÇÃO")
print_saida_rede("Filho antes da mutação", filho, entradas_teste)

print_titulo("MUTANDO FILHO")
filho.mutate(rate=0.2, strength=0.3)
print("Mutação aplicada ao filho.")

print_titulo("COMPARANDO PAI E FILHO APÓS MUTAÇÃO")
comparar_pesos(rede_pai, filho)
contar_parametros_alterados(rede_pai, filho)

print_titulo("SAÍDAS DO FILHO APÓS MUTAÇÃO")
print_saida_rede("Filho após mutação", filho, entradas_teste)

print_titulo("GERANDO VÁRIOS FILHOS MUTADOS")
filhos = gerar_filhos(rede_pai, quantidade=5, rate=0.15, strength=0.25)

for i, f in enumerate(filhos, start=1):
    print(f"\nFilho {i}")
    saida = f.forward(entradas_teste[0])
    print(f"Entrada teste: {np.round(entradas_teste[0], 3)}")
    print(f"Saída:         {np.round(saida, 3)}")

print_titulo("TESTE FINALIZADO")