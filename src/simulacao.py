# MOTOR DE SIMULAÇÃO
# Executar uma missão por passos de tempo: atualizar topologia, observar/detetar,
# decidir ações, mover agentes, atualizar bens/energia, recarga, captura/fuga.

from ambiente import Ambiente
import json

# Cores
AZUL = "\033[34m"
VERMELHO = "\033[31m"
AMARELO = "\033[33m"
VERDE = "\033[32m"
ROXO = "\033[35m"
RESET = "\033[0m"


def imprimir_mapa(ambiente, drones, intrusos, bens, saidas, recargas):
    # Neste momento apenas suporta o cenário 02_dinamico

    letras_impressas = set()

    for i in ambiente.grafo:
        letra = i[0]

        if letra not in letras_impressas:
            anterior = None

            # Ligações horizontais
            for j in ambiente.grafo:
                if j[0] == letra:

                    if anterior is not None:
                        chave = frozenset((anterior, j))

                        if chave in ambiente.portas:
                            if ambiente.portas[chave]:
                                print(f"{VERDE} ── {RESET}", end="")
                            else:
                                print(f"{VERMELHO} X  {RESET}", end="")
                        elif chave in ambiente.barreiras:
                            if ambiente.barreiras[chave]:
                                print(f"{AMARELO} ── {RESET}", end="")
                            else:
                                print(f"{AMARELO} X  {RESET}", end="")
                        elif j in ambiente.grafo[anterior]:
                            print(" ── ", end="")
                        else:
                            print("    ", end="")

                    # Imprimir intervenientes no nó ou simplesmente o nó vazio
                    if j in drones and j in intrusos:
                        print(f"{j}{AMARELO}X{RESET}", end="")
                    elif j in drones:
                        print(f"{j}{AZUL}D{RESET}", end="")
                    elif j in intrusos:
                        print(f"{j}{VERMELHO}I{RESET}", end="")
                    elif j in bens:
                        print(f"{j}{AMARELO}B{RESET}", end="")
                    elif j in saidas:
                        print(f"{j}{VERDE}S{RESET}", end="")
                    elif j in recargas:
                        print(f"{j}{ROXO}R{RESET}", end="")
                    else:
                        print(f"{j} ", end="")

                    anterior = j

            print()
            letras_impressas.add(letra)

            # Ligações verticais
            if letra != "F": # NOTA: NESTE MOMENTO ISTO SUPÕE QUE A ÚLTIMA LETRA É "F" !!!!!!!!!!!!!!! Alterar depois!!!!!
                for j in ambiente.grafo:
                    if j[0] == letra:

                        letra_seguinte = chr(ord(j[0]) + 1) # Próxima letra para verificar ligação vertical
                        no_baixo = letra_seguinte + j[1:]

                        chave = frozenset((j, no_baixo))

                        if chave in ambiente.portas:
                            if ambiente.portas[chave]:
                                print(f"{VERDE}│{RESET}", end="")
                            else:
                                print(f"{VERMELHO}X{RESET}", end="")
                        elif chave in ambiente.barreiras:
                            if ambiente.barreiras[chave]:
                                print(f"{AMARELO} | {RESET}", end="")
                            else:
                                print(f"{AMARELO}X{RESET}", end="")

                        elif no_baixo in ambiente.grafo[j]:
                            print("│", end="")
                        else:
                            print(" ", end="")

                        print("      ", end="")

                print()


# Carregar cenário
cenario = "cenarios/02_dinamico.json"

ambiente = Ambiente.carregar_json(cenario)

with open(cenario, encoding="utf-8") as ficheiro:
    dados = json.load(ficheiro)

# Guardar posições dos intervenientes no ambiente
drones = {d["posicao"] for d in dados["drones"]}
intrusos = {i["posicao"] for i in dados["intrusos"]}
bens = {b["local"] for b in dados["bens"]}
saidas = set(dados["saidas"])
recargas = {r["local"] for r in dados["recargas"]}

# Mostrar mapa
imprimir_mapa(ambiente, drones, intrusos, bens, saidas, recargas)

# Legenda
print()
print(f"{AZUL}D{RESET} - Drone")
print(f"{VERMELHO}I{RESET} - Intruso")
print(f"{AMARELO}X{RESET} - Drone e intruso na mesma posição")
print(f"{AMARELO}B{RESET} - Bem")
print(f"{VERDE}S{RESET} - Saída")
print(f"{ROXO}R{RESET} - Recarga")