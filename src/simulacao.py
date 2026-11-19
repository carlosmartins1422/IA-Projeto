# MOTOR DE SIMULAÇÃO
# Executa uma missão por passos de tempo discretos.
#
# ORDEM DE UM PASSO (regra temporal da Fase 1: sem isto o resultado dependeria
# da ordem em que o código está escrito). Em cada chamada a passo():
#   1. o tempo avança uma unidade;
#   2. [Fase 3, pontos seguintes] eventos do mapa (portas/barreiras) -> deteção/captura/fuga
#   3. as travessias em curso avançam; quem chega ao destino atualiza a posição
#      (agentes processados por ORDEM DE ID — desempate da Fase 1);
#   4. quem ficou num nó com percurso por cumprir começa a travessia seguinte;
#   5. [Fase 3, pontos seguintes] recolha de bens, energia e recarga.
# Só os passos 1, 3 e 4 estão implementados nesta versão (ciclo + movimento).

import json
import re

from ambiente import Ambiente
from agentes import Drone, Intruso
from procura import custo_aresta

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
    def __init__(self, ambiente, drones, intrusos, duracao_maxima=100):
        self.ambiente = ambiente

        # Dicionários id -> objeto, guardados por ordem de id (desempate da Fase 1)
        self.drones = {d.id: d for d in sorted(drones, key=lambda d: d.id)}
        self.intrusos = {i.id: i for i in sorted(intrusos, key=lambda i: i.id)}

        repetidos = set(self.drones) & set(self.intrusos)
        if repetidos:
            raise ValueError(f"Identificadores repetidos: {sorted(repetidos)}")

        self.duracao_maxima = duracao_maxima
        self.tempo = 0

        # Estado do movimento de cada agente (drone OU intruso), indexado por id:
        #   movimentos[id] = {"origem", "destino", "tempo_restante"}  -> está a atravessar uma aresta
        #   percursos[id]  = [nó, nó, ...]                            -> nós que faltam visitar
        self.movimentos = {}
        self.percursos = {}

        # Registo de acontecimentos: lista de (tempo, texto). Útil para testes e relatório.
        self.registo = []

        # Agentes que estão parados porque a próxima aresta está bloqueada
        # (serve para registar o bloqueio uma só vez e, mais tarde, disparar replaneamento)
        self.bloqueados = set()

    # ------------------------------------------------------------------
    # Construção a partir de um cenário JSON
    # ------------------------------------------------------------------
    @classmethod
    def carregar(cls, caminho):
        ambiente = Ambiente.carregar_json(caminho)

        with open(caminho, encoding="utf-8") as ficheiro:
            dados = json.load(ficheiro)

        drones = [
            Drone(
                id=d["id"], posicao=d["posicao"], velocidade=d["velocidade"],
                energia_atual=d["energia_atual"], energia_max=d["energia_max"],
                consumo_movimento=d["consumo_movimento"], consumo_parado=d["consumo_parado"],
                taxa_recarga=d["taxa_recarga"], custo_ativacao=d["custo_ativacao"],
                custo_voo=d["custo_voo"], custo_parado=d["custo_parado"],
                custo_recarga=d["custo_recarga"],
                alcance_deteccao=d.get("alcance_deteccao", 2),
            )
            for d in dados["drones"]
        ]

        intrusos = [
            Intruso(
                id=i["id"], posicao=i["posicao"], velocidade=i["velocidade"],
                perfil=i["perfil"], tempo_entrada=i.get("tempo_entrada", 0),
            )
            for i in dados["intrusos"]
        ]

        duracao = dados["parametros"].get("duracao_maxima") or 100
        return cls(ambiente, drones, intrusos, duracao)

    # ------------------------------------------------------------------
    # Consultas auxiliares
    # ------------------------------------------------------------------
    def agente(self, id_agente):
        # Devolve o drone ou o intruso com esse id
        if id_agente in self.drones:
            return self.drones[id_agente]
        if id_agente in self.intrusos:
            return self.intrusos[id_agente]
        raise ValueError(f"Agente desconhecido: {id_agente}")

    def _pode_mover(self, id_agente):
        # Drones movem-se sempre; intrusos só enquanto estão ativos
        # (um capturado ou fugido já não se mexe).
        if id_agente in self.intrusos:
            return self.intrusos[id_agente].estado == "ativo"
        return True

    def ponto_de_decisao(self, id_agente):
        # Nó onde o agente poderá voltar a decidir: se está a meio de uma aresta,
        # é o destino dessa aresta (não se pode mudar de ideias a meio do corredor);
        # caso contrário, é a posição atual.
        if id_agente in self.movimentos:
            return self.movimentos[id_agente]["destino"]
        return self.agente(id_agente).posicao

    def terminou(self):
        # Condições de fim (Fase 1, 2.º tópico):
        #   - todos os intrusos resolvidos (nenhum "ativo"), ou
        #   - atingido o limite de tempo.
        if self.tempo >= self.duracao_maxima:
            return True
        return not any(i.estado == "ativo" for i in self.intrusos.values())

    # ------------------------------------------------------------------
    # Percursos e movimento
    # ------------------------------------------------------------------
    def atribuir_percurso(self, id_agente, caminho):
        # 'caminho' tem o formato devolvido por bfs/a_estrela: ["A2", "B2", "C2", ...]
        # O primeiro nó tem de ser o ponto de decisão do agente.
        self.agente(id_agente)   # valida o id
        if not caminho:
            raise ValueError("Caminho vazio")
        if caminho[0] != self.ponto_de_decisao(id_agente):
            raise ValueError(
                f"{id_agente}: o caminho começa em {caminho[0]} "
                f"mas o agente decide em {self.ponto_de_decisao(id_agente)}"
            )

        # INVARIANTE: enquanto o agente está em trânsito, percurso[0] é o destino da
        # travessia em curso (é esse nó que _avancar_travessias remove à chegada).
        #   - em trânsito: caminho[0] JÁ é esse destino -> guardar o caminho todo
        #   - parado:      caminho[0] é a posição atual   -> guardar só o que falta
        # (list(...) faz uma cópia: não alteramos a lista do chamador)
        if id_agente in self.movimentos:
            self.percursos[id_agente] = list(caminho)
        else:
            self.percursos[id_agente] = list(caminho[1:])
        self._tentar_iniciar(id_agente)

    def _tentar_iniciar(self, id_agente):
        # Se o agente está parado num nó e tem percurso, começa a próxima travessia.
        # Devolve True se começou, False caso contrário.
        if id_agente in self.movimentos or not self._pode_mover(id_agente):
            return False

        percurso = self.percursos.get(id_agente)
        if not percurso:
            return False

        agente = self.agente(id_agente)
        origem, destino = agente.posicao, percurso[0]
        vizinhos = self.ambiente.vizinhos(origem)   # só ligações abertas neste instante

        if destino not in vizinhos:
            # Porta fechada/barreira ativa (ou nó inexistente): o agente espera e volta
            # a tentar no passo seguinte. O replaneamento fica para um ponto posterior da Fase 3.
            if id_agente not in self.bloqueados:
                self.bloqueados.add(id_agente)
                self.registo.append((self.tempo, f"{id_agente} bloqueado em {origem}: {origem}->{destino} indisponível"))
            return False

        self.bloqueados.discard(id_agente)
        duracao = custo_aresta(vizinhos[destino], agente.velocidade)   # ceil(comprimento / velocidade)
        self.movimentos[id_agente] = {"origem": origem, "destino": destino, "tempo_restante": duracao}
        return True

    def _avancar_travessias(self):
        # Passo 3: cada travessia em curso gasta uma unidade de tempo.
        chegaram = []
        for id_agente in sorted(self.movimentos):
            movimento = self.movimentos[id_agente]
            movimento["tempo_restante"] -= 1

            if movimento["tempo_restante"] <= 0:
                self.agente(id_agente).posicao = movimento["destino"]
                del self.movimentos[id_agente]
                self.percursos[id_agente].pop(0)    # este nó já foi visitado
                chegaram.append(id_agente)
                self.registo.append((self.tempo, f"{id_agente} chegou a {movimento['destino']}"))

                if not self.percursos[id_agente]:
                    self.registo.append((self.tempo, f"{id_agente} terminou o percurso"))
        return chegaram

    def _iniciar_travessias(self):
        # Passo 4: todos os agentes parados com percurso pendente tentam avançar.
        for id_agente in sorted(list(self.drones) + list(self.intrusos)):
            self._tentar_iniciar(id_agente)

    def passo(self):
        # Um passo de simulação (ver a ordem no topo do ficheiro).
        self.tempo += 1
        self._avancar_travessias()
        self._iniciar_travessias()

    def tem_percursos_pendentes(self):
        # True se algum agente ainda está a atravessar uma aresta ou tem nós por visitar
        return bool(self.movimentos) or any(self.percursos.values())

    def executar(self, mostrar=False, max_passos=None, ate_percursos_acabarem=False):
        # Corre até terminou() e devolve o tempo final. Paragens opcionais:
        #   max_passos              -> no máximo N passos;
        #   ate_percursos_acabarem  -> pára quando já ninguém tem percurso por cumprir
        #                              (útil em demonstrações, enquanto não há captura/fuga).
        if mostrar:
            self.mostrar_estado()
        passos = 0
        while not self.terminou():
            if max_passos is not None and passos >= max_passos:
                break
            if ate_percursos_acabarem and not self.tem_percursos_pendentes():
                break
            self.passo()
            passos += 1
            if mostrar:
                self.mostrar_estado()
        return self.tempo

    # ------------------------------------------------------------------
    # Visualização
    # ------------------------------------------------------------------
    def _e_grelha(self):
        # imprimir_mapa só sabe desenhar nós do tipo letra+número (A1, B3, ...)
        return all(re.fullmatch(r"[A-Z]\d+", no) for no in self.ambiente.grafo)

    def mostrar_estado(self):
        print(f"\n===== Tempo: {self.tempo} =====\n")

        # Agentes em trânsito não aparecem em nenhum nó: são listados por baixo do mapa
        pos_drones = {d.posicao for i, d in self.drones.items() if i not in self.movimentos}
        pos_intrusos = {i.posicao for k, i in self.intrusos.items()
                        if i.estado == "ativo" and k not in self.movimentos}
        bens = {b["local"] for b in self.ambiente.bens.values() if b["disponivel"]}
        recargas = {e["local"] for e in self.ambiente.estacoes.values()}

        if self._e_grelha():
            imprimir_mapa(self.ambiente, pos_drones, pos_intrusos, bens,
                          self.ambiente.saidas, recargas)
        else:
            print("Drones:  ", {i: d.posicao for i, d in self.drones.items()})
            print("Intrusos:", {k: i.posicao for k, i in self.intrusos.items()})

        for id_agente, mov in self.movimentos.items():
            print(f"{id_agente} em movimento: {mov['origem']} -> {mov['destino']} "
                  f"faltam: {mov['tempo_restante']} passo(s)")
        print()

    @staticmethod
    def mostrar_legenda():
        print(f"{AZUL}D{RESET} - Drone   {VERMELHO}I{RESET} - Intruso   "
              f"{CIANO}X{RESET} - Drone e intruso no mesmo nó   {AMARELO}B{RESET} - Bem   "
              f"{VERDE}S{RESET} - Saída   {ROXO}R{RESET} - Recarga")