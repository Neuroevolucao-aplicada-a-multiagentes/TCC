import numpy as np
from rede_neural import RedeNeural

def print_titulo(texto):
    print('\n' + '=' * 60)
    print(texto)
    print('=' * 60)

def print_saida_rede(nome, rede, entradas):
    print(f'\n{nome}')
    for i, entrada in enumerate(entradas, start=1):
        saida = rede.forward(entrada)
        print(f'Caso {i}:')
        print(f"  Entrada: {np.round(entrada, 3)}")
        print(f"  Saída:   {np.round(saida, 3)}")

def comparar_pesos(rede1, rede2):
    for attr in ['w1', 'w2', 'b1', 'b2']:
        diff = np.sum(np.abs(getattr(rede1, attr) - getattr(rede2, attr)))
        print(f"{attr}: {diff:.6f}")

def contar_parametros_alterados(rede1, rede2):
    total_alt = 0
    total = 0
    for attr in ['w1', 'w2', 'b1', 'b2']:
        a, b = getattr(rede1, attr), getattr(rede2, attr)
        alt = np.sum(a != b)
        print(f"{attr}: {alt}")
        total_alt += alt
        total += a.size
    print(f"Total alterados: {total_alt}/{total}")

def gerar_filhos(rede_pai, quantidade=5, rate=0.1, strength=0.2):
    filhos = []
    for _ in range(quantidade):
        filho = rede_pai.copy()
        filho.mutate(rate=rate, strength=strength)
        filhos.append(filho)
    return filhos

# [dx, dy, dist, dist_robo, dx_robo, dy_robo, dist_obst, dx_obst, dy_obst, carregando, dist_entrega]
ENTRADAS_TESTE = [
    [0.8, 0.0, 0.8, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
    [-0.8, 0.0, 0.8, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
    [0.0, -0.8, 0.8, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
    [0.0, 0.8, 0.8, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
    [0.7, 0.0, 0.7, 0.05, 0.3, 0.0, 0.3, 0.2, 0.0, 0.0, 0.8],
    [0.5, 0.0, 0.5, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.3],
]

print_titulo("CRIANDO REDE PAI")
rede_pai = RedeNeural()
print("w1:", rede_pai.w1.shape)
print("w2:", rede_pai.w2.shape)

print_titulo("SAÍDAS DA REDE PAI")
print_saida_rede("Rede Pai", rede_pai, ENTRADAS_TESTE)

print_titulo("CRIANDO FILHO POR CÓPIA")
filho = rede_pai.copy()

print_titulo("COMPARANDO PAI E FILHO ANTES DA MUTAÇÃO")
comparar_pesos(rede_pai, filho)
contar_parametros_alterados(rede_pai, filho)

print_titulo("MUTANDO FILHO")
filho.mutate(rate=0.2, strength=0.3)

print_titulo("COMPARANDO PAI E FILHO APÓS MUTAÇÃO")
comparar_pesos(rede_pai, filho)
contar_parametros_alterados(rede_pai, filho)

print_titulo("SAÍDAS DO FILHO APÓS MUTAÇÃO")
print_saida_rede("Filho após mutação", filho, ENTRADAS_TESTE)

print_titulo("GERANDO VÁRIOS FILHOS MUTADOS")
filhos = gerar_filhos(rede_pai, quantidade=5, rate=0.15, strength=0.25)
for i, f in enumerate(filhos, start=1):
    saida = f.forward(ENTRADAS_TESTE[0])
    print(f"\nFilho {i} → Saída: {np.round(saida, 3)}")

print_titulo("TESTE FINALIZADO")