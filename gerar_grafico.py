import argparse
import csv
import os
import sys

import matplotlib.pyplot as plt


def carregar(caminho_csv):
    with open(caminho_csv, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def plotar(linhas, titulo, saida_png):
    tempos = [float(l["tempo"]) for l in linhas]
    coletas = [int(l["coletas"]) for l in linhas]
    entregas = [int(l["entregas"]) for l in linhas]
    colisoes = [int(l["colisoes"]) for l in linhas]
    manut = [int(l["manutencoes"]) for l in linhas]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    ax1.plot(tempos, coletas, marker="o", linewidth=2, label="Coletas")
    ax1.plot(tempos, entregas, marker="s", linewidth=2, label="Entregas")
    ax1.set_ylabel("Acumulado")
    ax1.set_title(titulo)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="upper left")

    ax2.plot(tempos, colisoes, marker="x", color="#cc4444", linewidth=1.5, label="Colisões")
    ax2.plot(tempos, manut, marker="d", color="#dd9933", linewidth=1.5, label="Manutenções")
    ax2.set_xlabel("Tempo (s)")
    ax2.set_ylabel("Acumulado")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="upper left")

    plt.tight_layout()
    plt.savefig(saida_png, dpi=120)
    print(f"grafico salvo em {saida_png}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", nargs="?", default="runs/snapshots.csv")
    parser.add_argument("--saida", default="runs/grafico.png")
    parser.add_argument("--titulo", default="Demonstração - Rede pré-treinada (fase 5)")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"arquivo nao encontrado: {args.csv}")
        sys.exit(1)

    linhas = carregar(args.csv)
    if not linhas:
        print("csv vazio")
        sys.exit(1)

    plotar(linhas, args.titulo, args.saida)


if __name__ == "__main__":
    main()
