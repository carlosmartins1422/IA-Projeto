# TESTES DE PROCURA (BFS e A*)
# Correr a partir da pasta do projeto:   python3 -m unittest discover -s testes -v

import heapq
import math
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ambiente import Ambiente
from procura import bfs, a_estrela, custo_aresta, custo_caminho
from heuristicas import heuristica_referencia

CENARIO_BASICO = os.path.join(os.path.dirname(__file__), "..", "cenarios", "01_basico.json")


# Construtores de mapas pequenos

def mapa_atalho():
    # S->G direto custa 10 (1 aresta); S->M->G custa 1+1 (2 arestas)
    a = Ambiente()
    a.adicionar_ligacao("S", "G", 10)
    a.adicionar_ligacao("S", "M", 1)
    a.adicionar_ligacao("M", "G", 1)
    return a


def mapa_desconexo():
    a = Ambiente()
    a.adicionar_ligacao("A", "B", 1)
    a.adicionar_local("C")
    return a


def mapa_com_porta():
    # Duas rotas A->D: curta por B (com porta) e longa por C
    a = Ambiente()
    a.adicionar_ligacao("A", "B", 1)
    a.adicionar_ligacao("B", "D", 1)
    a.adicionar_ligacao("A", "C", 4)
    a.adicionar_ligacao("C", "D", 4)
    a.adicionar_porta("A", "B", True)
    return a


def dijkstra_independente(ambiente, origem, objetivos, velocidade):
    # Referência escrita à parte (Custo Uniforme) para validar o A*
    dist = {origem: 0}
    fila = [(0, origem)]
    while fila:
        d, no = heapq.heappop(fila)
        if d > dist[no]:
            continue
        if no in objetivos:
            return d
        for viz, comp in ambiente.vizinhos(no).items():
            nd = d + custo_aresta(comp, velocidade)
            if nd < dist.get(viz, math.inf):
                dist[viz] = nd
                heapq.heappush(fila, (nd, viz))
    return None


def mapa_aleatorio(rng):
    n = rng.randint(4, 14)
    a = Ambiente()
    for i in range(n):
        a.adicionar_local(str(i))
    for i in range(1, n):  # árvore para garantir ligações
        a.adicionar_ligacao(str(i), str(rng.randint(0, i - 1)), rng.randint(1, 9))
    for _ in range(rng.randint(0, n)):  # ligações extra (ciclos)
        u, v = rng.sample(range(n), 2)
        a.adicionar_ligacao(str(u), str(v), rng.randint(1, 9))
    for u in list(a.grafo):  # fecha algumas portas
        for v in list(a.grafo[u]):
            if u < v and rng.random() < 0.25:
                a.adicionar_porta(u, v, False)
    return a


# ---------- Custos ----------

class TestCustos(unittest.TestCase):
    def test_custo_aresta_arredonda_para_cima(self):
        self.assertEqual(custo_aresta(3, 2), 2)
        self.assertEqual(custo_aresta(4, 2), 2)
        self.assertEqual(custo_aresta(1, 5), 1)

    def test_custo_caminho_soma_arestas(self):
        a = mapa_atalho()
        self.assertEqual(custo_caminho(a, ["S", "M", "G"], 1), 2)
        self.assertEqual(custo_caminho(a, ["S", "G"], 1), 10)
        self.assertEqual(custo_caminho(a, ["S"], 1), 0)


# BFS

class TestBFS(unittest.TestCase):
    def test_caminho_existente(self):
        r = bfs(mapa_atalho(), "S", "G")
        self.assertTrue(r["sucesso"])
        self.assertEqual(r["caminho"][0], "S")
        self.assertEqual(r["caminho"][-1], "G")

    def test_origem_igual_ao_objetivo(self):
        r = bfs(mapa_atalho(), "S", "S")
        self.assertTrue(r["sucesso"])
        self.assertEqual(r["caminho"], ["S"])
        self.assertEqual(r["custo"], 0)
        self.assertEqual(r["nos_explorados"], 0)

    def test_sem_caminho(self):
        r = bfs(mapa_desconexo(), "A", "C")
        self.assertFalse(r["sucesso"])
        self.assertEqual(r["caminho"], [])
        self.assertIsNone(r["custo"])

    def test_origem_ou_objetivo_inexistente(self):
        a = mapa_atalho()
        self.assertFalse(bfs(a, "X", "G")["sucesso"])
        self.assertFalse(bfs(a, "S", "X")["sucesso"])

    def test_bfs_minimiza_arestas_nao_custo(self):
        # O BFS escolhe o atalho direto (1 aresta, custo 10), apesar de haver custo 2
        r = bfs(mapa_atalho(), "S", "G")
        self.assertEqual(r["caminho"], ["S", "G"])
        self.assertEqual(r["custo"], 10)

    def test_varios_objetivos(self):
        a = mapa_atalho()
        r = bfs(a, "S", {"M", "G"})
        self.assertTrue(r["sucesso"])
        self.assertIn(r["caminho"][-1], {"M", "G"})

    def test_porta_fechada_reencaminha(self):
        a = mapa_com_porta()
        self.assertEqual(bfs(a, "A", "D")["caminho"], ["A", "B", "D"])
        a.alterar_porta("A", "B", False)
        self.assertEqual(bfs(a, "A", "D")["caminho"], ["A", "C", "D"])

    def test_barreira_ativa_bloqueia_e_pode_cortar_tudo(self):
        a = Ambiente()
        a.adicionar_ligacao("A", "B", 1)
        a.adicionar_barreira("A", "B", False)
        self.assertTrue(bfs(a, "A", "B")["sucesso"])
        a.alterar_barreira("A", "B", True)
        self.assertFalse(bfs(a, "A", "B")["sucesso"])

    def test_custo_depende_da_velocidade(self):
        a = mapa_atalho()
        self.assertEqual(bfs(a, "S", "G", velocidade=1)["custo"], 10)
        self.assertEqual(bfs(a, "S", "G", velocidade=5)["custo"], 2)

    def test_determinismo(self):
        a = Ambiente.carregar_json(CENARIO_BASICO)
        r1 = bfs(a, "Entrada", a.saidas)
        r2 = bfs(a, "Entrada", a.saidas)
        self.assertEqual(r1, r2)


# ---------- A* ----------

class TestAEstrela(unittest.TestCase):
    def test_encontra_caminho_mais_barato(self):
        r = a_estrela(mapa_atalho(), "S", "G")
        self.assertEqual(r["caminho"], ["S", "M", "G"])
        self.assertEqual(r["custo"], 2)

    def test_a_estrela_vs_bfs_custos_diferentes(self):
        a = mapa_atalho()
        self.assertLess(a_estrela(a, "S", "G")["custo"], bfs(a, "S", "G")["custo"])

    def test_origem_igual_ao_objetivo(self):
        r = a_estrela(mapa_atalho(), "S", "S")
        self.assertTrue(r["sucesso"])
        self.assertEqual(r["caminho"], ["S"])
        self.assertEqual(r["custo"], 0)

    def test_sem_caminho(self):
        r = a_estrela(mapa_desconexo(), "A", "C")
        self.assertFalse(r["sucesso"])
        self.assertEqual(r["caminho"], [])
        self.assertIsNone(r["custo"])

    def test_origem_inexistente(self):
        self.assertFalse(a_estrela(mapa_atalho(), "X", "G")["sucesso"])

    def test_objetivo_inexistente(self):
        self.assertFalse(a_estrela(mapa_atalho(), "S", "X")["sucesso"])

    def test_porta_fechada_aumenta_custo(self):
        a = mapa_com_porta()
        self.assertEqual(a_estrela(a, "A", "D")["custo"], 2)
        a.alterar_porta("A", "B", False)
        r = a_estrela(a, "A", "D")
        self.assertEqual(r["caminho"], ["A", "C", "D"])
        self.assertEqual(r["custo"], 8)

    def test_varios_objetivos_escolhe_o_mais_barato(self):
        a = mapa_atalho()
        r = a_estrela(a, "S", {"M", "G"})
        self.assertEqual(r["caminho"], ["S", "M"])
        self.assertEqual(r["custo"], 1)

    def test_velocidade_altera_custo_com_ceil(self):
        a = mapa_atalho()
        self.assertEqual(a_estrela(a, "S", "G", velocidade=2)["custo"], 2)  # ceil(1/2)+ceil(1/2)
        self.assertEqual(a_estrela(a, "S", "G", velocidade=10)["custo"], 1)  # direto: ceil(10/10)

    def test_aceita_heuristica_personalizada(self):
        r = a_estrela(mapa_atalho(), "S", "G", heuristica=lambda no: 0)
        self.assertEqual(r["custo"], 2)

    def test_cenario_basico(self):
        a = Ambiente.carregar_json(CENARIO_BASICO)
        r = a_estrela(a, "Entrada", a.saidas)
        self.assertEqual(r["custo"], 12)
        self.assertEqual(r["caminho"][-1], "Saida")
        a.alterar_porta("CorredorA", "SalaCofre", False)
        self.assertEqual(a_estrela(a, "Entrada", a.saidas)["custo"], 13)

    def test_a_estrela_explora_menos_que_bfs_no_cenario_basico(self):
        a = Ambiente.carregar_json(CENARIO_BASICO)
        self.assertLessEqual(a_estrela(a, "Entrada", a.saidas)["nos_explorados"],
                             bfs(a, "Entrada", a.saidas)["nos_explorados"])


# Heurística de referência

class TestHeuristica(unittest.TestCase):
    def test_zero_nos_objetivos(self):
        h = heuristica_referencia(mapa_atalho(), {"G"}, 1)
        self.assertEqual(h("G"), 0)

    def test_valores_no_cenario_basico(self):
        a = Ambiente.carregar_json(CENARIO_BASICO)
        h = heuristica_referencia(a, a.saidas, 1)
        self.assertEqual(h("Entrada"), 12)
        self.assertEqual(h("SalaCofre"), 4)

    def test_no_sem_ligacao_ao_objetivo_e_infinito(self):
        h = heuristica_referencia(mapa_desconexo(), {"A"}, 1)
        self.assertEqual(h("C"), math.inf)

    def test_continua_admissivel_apos_fechar_porta(self):
        # h foi calculada com tudo aberto; fechar portas só pode subir o custo real
        a = Ambiente.carregar_json(CENARIO_BASICO)
        h = heuristica_referencia(a, a.saidas, 1)
        a.alterar_porta("CorredorA", "SalaCofre", False)
        for no in a.grafo:
            real = dijkstra_independente(a, no, a.saidas, 1)
            if real is not None:
                self.assertLessEqual(h(no), real)


# Validação aleatória (propriedades)

class TestPropriedadesAleatorias(unittest.TestCase):
    def test_a_estrela_igual_a_dijkstra_e_heuristica_consistente(self):
        rng = random.Random(7)
        for _ in range(300):
            a = mapa_aleatorio(rng)
            v = rng.choice([1, 2, 3])
            objs = {str(rng.randrange(len(a.grafo))) for _ in range(rng.randint(1, 2))}
            origem = str(rng.randrange(len(a.grafo)))
            h = heuristica_referencia(a, objs, v)

            # consistência: h(u) <= custo(u,w) + h(w) em todas as arestas
            for u in a.grafo:
                for w, comp in a.grafo[u].items():
                    self.assertLessEqual(h(u), custo_aresta(comp, v) + h(w))

            esperado = dijkstra_independente(a, origem, objs, v)
            r = a_estrela(a, origem, objs, v)
            self.assertEqual(r["sucesso"], esperado is not None)
            if r["sucesso"]:
                self.assertEqual(r["custo"], esperado)
                self.assertEqual(r["caminho"][0], origem)
                self.assertIn(r["caminho"][-1], objs)
                for x, y in zip(r["caminho"], r["caminho"][1:]):
                    self.assertIn(y, a.vizinhos(x))      # só usa ligações abertas
                self.assertEqual(custo_caminho(a, r["caminho"], v), r["custo"])
                # h=0 dá o mesmo custo, mas nunca explora menos nós
                z = a_estrela(a, origem, objs, v, heuristica=lambda no: 0)
                self.assertEqual(z["custo"], r["custo"])
                self.assertGreaterEqual(z["nos_explorados"], r["nos_explorados"])

    def test_bfs_minimiza_numero_de_arestas(self):
        rng = random.Random(11)
        for _ in range(200):
            a = mapa_aleatorio(rng)
            origem = str(rng.randrange(len(a.grafo)))
            destino = str(rng.randrange(len(a.grafo)))
            r = bfs(a, origem, destino)
            # nº mínimo de arestas por uma BFS independente (distâncias em saltos)
            salto = {origem: 0}
            fila = [origem]
            for no in fila:
                for viz in a.vizinhos(no):
                    if viz not in salto:
                        salto[viz] = salto[no] + 1
                        fila.append(viz)
            self.assertEqual(r["sucesso"], destino in salto)
            if r["sucesso"]:
                self.assertEqual(len(r["caminho"]) - 1, salto[destino])


if __name__ == "__main__":
    unittest.main()