import random as rd
from time import sleep

linhas = 8
colunas = 8

# Cria matriz vazia
matriz = []
for i in range(linhas):
    linha = []
    for j in range(colunas):
        linha.append(0)
    matriz.append(linha)

def mostrar(matriz, titulo=""):
    if titulo:
        print(f"\n{titulo}")
    for linha in matriz:
        linha_str = "  ".join(f"{n:5.1f}" for n in linha)
        print(f"  | {linha_str} |")
    print()

mostrar(matriz, "MATRIZ DE IA (vazia)")

print("Alimentando com pesos sinapticos...")
sleep(1)

for i in range(linhas):
    for j in range(colunas):
        matriz[i][j] = rd.uniform(-1.0, 1.0)

mostrar(matriz, "IA PENSANDO...")

print("Treinando...")
sleep(1)

for epoca in range(5):
    for i in range(linhas):
        for j in range(colunas):
            matriz[i][j] += rd.uniform(-0.1, 0.1)
    mostrar(matriz, f"Epoca {epoca + 1}/5")
    sleep(0.3)

entrada = [1, 0, 1, 0, 1, 0, 1, 1]
print(f"ENTRADA: {entrada}")
sleep(0.5)

saida = []
for i in range(linhas):
    soma = 0.0
    for j in range(colunas):
        soma += entrada[j] * matriz[i][j]
    ativado = 1 / (1 + 2.718 ** (-soma))
    saida.append(ativado)

print("SAIDA:")
for i, v in enumerate(saida):
    barra = "#" * int(abs(v) * 20)
    print(f"  Neuronio {i+1}: {v:6.3f} {barra}")

decisao = "SIM" if sum(saida) / len(saida) > 0.5 else "NAO"
print(f"\nDECISAO: {decisao}")
