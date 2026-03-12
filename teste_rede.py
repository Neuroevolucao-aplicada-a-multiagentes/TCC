from rede_neural import RedeNeural

rede = RedeNeural()

estado = [0.5, -0.3, 0.7]

saida = rede.forward(estado)

print("Entrada:", estado)
print("Saída:", saida)