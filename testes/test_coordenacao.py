# TESTES DA PERSEGUIÇÃO DIRETA
# Correr a partir da pasta do projeto:   python3 -m unittest discover -s testes -v

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ambiente import Ambiente
from agentes import Drone, Intruso
from coordenacao import PerseguicaoDireta, saltos_ate


def linha():
    # A - B - C - D - E (comprimento 1 cada), com porta em C-D
    a = Ambiente()
    for u, v in [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")]:
        a.adicionar_ligacao(u, v, 1)
    a.adicionar_porta("C", "D", True)
    return a


def drone(id, pos, alcance=2, velocidade=1):
    return Drone(id, pos, velocidade, 100, 100, 2, 0.5, 10, 5, 2, 0.5, 1, alcance_deteccao=alcance)


def intruso(id, pos):
    return Intruso(id, pos, 1, "recolhedor")


class TestSaltos(unittest.TestCase):
    def test_limite_de_saltos(self):
        self.assertEqual(saltos_ate(linha(), "A", 2), {"A": 0, "B": 1, "C": 2})

    def test_porta_fechada_corta_alcance(self):
        a = linha()
        a.alterar_porta("C", "D", False)
        self.assertNotIn("E", saltos_ate(a, "C", 5))


class TestDeteccao(unittest.TestCase):
    def test_detecta_dentro_do_alcance_e_nao_fora(self):
        p = PerseguicaoDireta()
        det = p.atualizar_conhecimento(linha(), [drone("DR1", "A")], [intruso("IN1", "C"), intruso("IN2", "E")])
        self.assertEqual(det, {"IN1": "C"})
        self.assertEqual(p.conhecimento, {"IN1": "C"})

    def test_conhecimento_e_partilhado(self):
        p = PerseguicaoDireta()
        drones = [drone("DR1", "A"), drone("DR2", "E", alcance=0)]
        p.atualizar_conhecimento(linha(), drones, [intruso("IN1", "B")])
        # DR2 não vê IN1, mas conhece-o e consegue planear
        plano = p.decidir(linha(), drones[1])
        self.assertEqual(plano["alvo"], "IN1")

    def test_esquece_intrusos_capturados(self):
        p = PerseguicaoDireta()
        i = intruso("IN1", "B")
        p.atualizar_conhecimento(linha(), [drone("DR1", "A")], [i])
        i.estado = "capturado"
        p.atualizar_conhecimento(linha(), [drone("DR1", "A")], [i])
        self.assertEqual(p.conhecimento, {})

    def test_esquece_pista_ao_chegar_sem_encontrar(self):
        p = PerseguicaoDireta()
        i = intruso("IN1", "C")
        d = drone("DR1", "A")
        p.atualizar_conhecimento(linha(), [d], [i])
        i.posicao = "E"          # o intruso fugiu para fora do alcance
        d.posicao = "C"          # o drone chega à última posição conhecida
        d.alcance_deteccao = 0
        p.atualizar_conhecimento(linha(), [d], [i])
        self.assertEqual(p.conhecimento, {})


class TestDecisao(unittest.TestCase):
    def test_sem_alvos_devolve_none(self):
        self.assertIsNone(PerseguicaoDireta().decidir(linha(), drone("DR1", "A")))

    def test_escolhe_o_mais_proximo(self):
        p = PerseguicaoDireta()
        p.conhecimento = {"IN1": "E", "IN2": "B"}
        plano = p.decidir(linha(), drone("DR1", "A"))
        self.assertEqual(plano["alvo"], "IN2")
        self.assertEqual(plano["caminho"], ["A", "B"])
        self.assertEqual(plano["custo"], 1)

    def test_velocidade_altera_custo_do_plano(self):
        a = Ambiente()
        a.adicionar_ligacao("A", "B", 3)
        p = PerseguicaoDireta()
        p.conhecimento = {"IN1": "B"}
        self.assertEqual(p.decidir(a, drone("DR1", "A", velocidade=1))["custo"], 3)
        self.assertEqual(p.decidir(a, drone("DR1", "A", velocidade=2))["custo"], 2)   # ceil(3/2)

    def test_replaneia_quando_porta_fecha(self):
        a = linha()
        a.adicionar_ligacao("B", "E", 6)         # rota longa alternativa
        p = PerseguicaoDireta()
        p.conhecimento = {"IN1": "E"}
        d = drone("DR1", "A")
        self.assertEqual(p.decidir(a, d)["caminho"], ["A", "B", "C", "D", "E"])
        a.alterar_porta("C", "D", False)
        self.assertEqual(p.decidir(a, d)["caminho"], ["A", "B", "E"])

    def test_alvo_inalcancavel_devolve_none(self):
        a = linha()
        a.alterar_porta("C", "D", False)
        p = PerseguicaoDireta()
        p.conhecimento = {"IN1": "E"}
        self.assertIsNone(p.decidir(a, drone("DR1", "A")))

    def test_ja_no_local_do_alvo(self):
        p = PerseguicaoDireta()
        p.conhecimento = {"IN1": "A"}
        plano = p.decidir(linha(), drone("DR1", "A"))
        self.assertEqual(plano["caminho"], ["A"])
        self.assertEqual(plano["custo"], 0)

    def test_todos_perseguem_o_mesmo_alvo(self):
        # Característica da estratégia de referência: sem coordenação
        p = PerseguicaoDireta()
        p.conhecimento = {"IN1": "C", "IN2": "A"}
        planos = p.decidir_todos(linha(), [drone("DR1", "B"), drone("DR2", "B")])
        self.assertEqual(planos["DR1"]["alvo"], planos["DR2"]["alvo"])


if __name__ == "__main__":
    unittest.main()