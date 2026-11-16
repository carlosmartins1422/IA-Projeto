# MOTOR DE SIMULAÇÃO
# Executar uma missão por passos de tempo: atualizar topologia, observar/detetar,
# decidir ações, mover agentes, atualizar bens/energia, recarga, captura/fuga.

from ambiente import Ambiente
from agentes import Drone
from procura import custo_aresta, a_estrela
import json

# Cores
AZUL = "\033[34m"
VERMELHO = "\033[31m"
AMARELO = "\033[33m"
VERDE = "\033[32m"
ROXO = "\033[35m"
CIANO = "\033[36m"
CINZENTO = "\033[90m"
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
                            comprimento = ambiente.grafo[anterior][j] # Comprimento da aresta entre os nós
                            if ambiente.portas[chave]:
                                print(f"{VERDE} ─{comprimento}─ {RESET}", end="")
                            else:
                                print(f"{VERMELHO} X{comprimento}  {RESET}", end="")
                        elif chave in ambiente.barreiras:
                            comprimento = ambiente.grafo[anterior][j] # Comprimento da aresta entre os nós
                            if ambiente.barreiras[chave]:
                                print(f"{AMARELO} X{comprimento}  {RESET}", end="")
                            else:
                                print(f"{AMARELO} ─{comprimento}─ {RESET}", end="")
                        elif j in ambiente.grafo[anterior]:
                            comprimento = ambiente.grafo[anterior][j] # Comprimento da aresta entre os nós
                            print(f"{CINZENTO} ─{comprimento}─ {RESET}", end="")
                        else:
                            print("     ", end="")

                    # Imprimir intervenientes no nó ou simplesmente o nó vazio
                    if j in drones and j in intrusos:
                        print(f"{j}{CIANO}X{RESET}", end="")
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

            print(" ")
            letras_impressas.add(letra)

            # Ligações verticais
            if letra != "F": # NOTA: NESTE MOMENTO ISTO SUPÕE QUE A ÚLTIMA LETRA É "F" !!!!!!!!!!!!!!! Alterar depois!!!!!
                for j in ambiente.grafo:
                    if j[0] == letra:

                        letra_seguinte = chr(ord(j[0]) + 1) # Próxima letra para verificar ligação vertical
                        no_baixo = letra_seguinte + j[1:]

                        chave = frozenset((j, no_baixo))

                        if chave in ambiente.portas:
                            comprimento = ambiente.grafo[j][no_baixo] # Comprimento da aresta entre os nós
                            if ambiente.portas[chave]:
                                print(f"{VERDE}│{comprimento}{RESET}", end="")
                            else:
                                print(f"{VERMELHO}X{comprimento}{RESET}", end="")
                        elif chave in ambiente.barreiras:
                            comprimento = ambiente.grafo[j][no_baixo] # Comprimento da aresta entre os nós
                            if ambiente.barreiras[chave]:
                                print(f"{AMARELO} X {comprimento}{RESET}", end="")
                            else:
                                print(f"{AMARELO}|{comprimento}{RESET}", end="")

                        elif no_baixo in ambiente.grafo[j]:
                            comprimento = ambiente.grafo[j][no_baixo] # Comprimento da aresta entre os nós
                            print(f"{CINZENTO}│{comprimento}{RESET}", end="")
                        else:
                            print(" ", end="")

                        print("      ", end="")

                print(" ")



class Simulacao:
    def __init__(self, ambiente, drones, intrusos, bens, saidas, recargas):
        self.ambiente = ambiente
        self.drones = drones
        self.intrusos = intrusos
        self.bens = bens
        self.saidas = saidas
        self.recargas = recargas
        self.tempo = 0
        self.movimentos = {}
        self.percursos = {}

    def mostrar_estado(self):
        print(f"\n===== Tempo: {self.tempo} =====")
        print() # Espaço antes do mapa
        imprimir_mapa(self.ambiente, 
                      {d.posicao for id_drone, d in self.drones.items()
                       if id_drone not in self.movimentos}, # Obtem as posições atuais de todos os drones, se não estiverem em movimento
                      self.intrusos, 
                      self.bens, 
                      self.saidas, 
                      self.recargas
                      )
        for id_drone, movimento in self.movimentos.items():
            origem = self.drones[id_drone].posicao
            destino = movimento["destino"]
            restante = movimento["tempo_restante"]
            print(f"{id_drone} em movimento: {origem} -> {destino} "
                  f"faltam: {restante} passo(s)")
        print() # Espaço extra após o mapa

    def passo(self):
        self.tempo += 1
        chegaram = []

        for id_drone, movimento in list(self.movimentos.items()):
            movimento["tempo_restante"] -= 1

            if movimento["tempo_restante"] <= 0:
                self.drones[id_drone].posicao = movimento["destino"] # atualiza a posição do drone para a posiçao seguinte
                del self.movimentos[id_drone] # del faz com que o drone seja removido da lista de movimentos quando chega ao destino
                chegaram.append(id_drone)

                percurso = self.percursos.get(id_drone, []) # obtem o percurso do drone, se existir

                if percurso and percurso[0] == self.drones[id_drone].posicao:
                    percurso.pop(0) # Remove o primeiro ponto do percurso, pois o drone já chegou a ele
        
        # Mostrar o estado da simulação após atualizar os movimentos dos drones
        self.mostrar_estado()

        # Só depois iniciar as proximas travessias
        for id_drone in chegaram:
            percurso = self.percursos.get(id_drone, [])

            if percurso:
                self.mover_drones(id_drone, percurso[0])
            else:
                print(f"{id_drone} terminou o percurso") 



    def mover_drones(self, id_drone, destino):
        if id_drone in self.movimentos:
            print(f"Drone {id_drone} já está em movimento")
            return
        origem = self.drones[id_drone].posicao # Posição atual do drone, devolve a posição como string

        if destino in self.ambiente.vizinhos(origem):
            comprimento = self.ambiente.vizinhos(origem)[destino] # Comprimento da aresta entre origem e destino
            velocidade = self.drones[id_drone].velocidade
            duracao = custo_aresta(comprimento, velocidade)

            self.movimentos[id_drone] = {
                "destino": destino,
                "tempo_restante": duracao

            }
        else:
            print(f"Movimento inválido para o drone {id_drone} de {origem} para {destino}")

# Carregar cenário
cenario = "cenarios/02_dinamico.json"

ambiente = Ambiente.carregar_json(cenario)

with open(cenario, encoding="utf-8") as ficheiro:
    dados = json.load(ficheiro)

# Guardar posições dos intervenientes no ambiente
drones = {}
for d in dados["drones"]:
    drone = Drone(
        id=d["id"],
        posicao=d["posicao"],
        velocidade=d["velocidade"],
        energia_atual=d["energia_atual"],
        energia_max=d["energia_max"],
        consumo_movimento=d["consumo_movimento"],
        consumo_parado=d["consumo_parado"],
        taxa_recarga=d["taxa_recarga"],
        custo_ativacao=d["custo_ativacao"],
        custo_voo=d["custo_voo"],
        custo_parado=d["custo_parado"],
        custo_recarga=d["custo_recarga"],
        alcance_deteccao=d.get("alcance_deteccao", 2)
    )
    drones[d["id"]] = drone


intrusos = {i["posicao"] for i in dados["intrusos"]}
bens = {b["local"] for b in dados["bens"]}
saidas = set(dados["saidas"])
recargas = {r["local"] for r in dados["recargas"]}

# Criar simulação com o ambiente e os intervenientes carregados
simulacao = Simulacao(ambiente, drones, intrusos, bens, saidas, recargas)

# Mostrar mapa
simulacao.mostrar_estado()

# Testes
drone = simulacao.drones["DR1"]

resultado = a_estrela (simulacao.ambiente, drone.posicao, "E4", drone.velocidade)
print("REsultado procura:", resultado)
simulacao.percursos["DR1"] = resultado["caminho"][1:]
if simulacao.percursos["DR1"]:
    simulacao.mover_drones("DR1", simulacao.percursos["DR1"][0])

if resultado["sucesso"]:
    for _ in range(resultado["custo"]):
        simulacao.passo()

# Legenda
print()
print(f"{AZUL}D{RESET} - Drone")
print(f"{VERMELHO}I{RESET} - Intruso")
print(f"{CIANO}X{RESET} - Drone e intruso na mesma posição")
print(f"{AMARELO}B{RESET} - Bem")
print(f"{VERDE}S{RESET} - Saída")
print(f"{ROXO}R{RESET} - Recarga")
print(f"{CINZENTO}|{RESET} - Arestas")


