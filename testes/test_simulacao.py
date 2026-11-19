# TESTES DO CICLO DA SIMULAÇÃO (Fase 3, ponto 1: tempo + movimento por velocidade)
# Correr a partir da pasta do projeto:   python3 -m unittest discover -s testes -v
#
# Os testes de captura, fuga, recolha, energia, recarga, perfis, eventos e
# replaneamento serão acrescentados quando essas funcionalidades existirem.

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ambiente import Ambiente
from agentes import Drone, Intruso
from procura import a_estrela, custo_caminho
from simulacao import Simulacao

RAIZ = os.path.join(os.path.dirname(__file__), "..")


def mapa():
    # A --3-- B --4-- C --2-- D      (porta em B-C)
    a = Ambiente()
    a.adicionar_ligacao("A", "B", 3)
    a.adicionar_ligacao("B", "C", 4)
    a.adicionar_ligacao("C", "D", 2)
    a.adicionar_porta("B", "C", True)
    return a


def drone(id, pos, velocidade=1):
    return Drone(id, pos, velocidade, 100, 100, 2, 0.5, 10, 5, 2, 0.5, 1)


def intruso(id, pos, velocidade=1, perfil="recolhedor"):
    return Intruso(id, pos, velocidade, perfil)


def sim(drones=(), intrusos=(), duracao=100, ambiente=None):
    return Simulacao(ambiente or mapa(), list(drones), list(intrusos), duracao)


class TestTempo(unittest.TestCase):
    def test_tempo_comeca_em_zero_e_avanca_um_por_passo(self):
        s = sim([drone("DR1", "A")])
        self.assertEqual(s.tempo, 0)
        s.passo()
        s.passo()
        self.assertEqual(s.tempo, 2)

    def test_ids_repetidos_sao_rejeitados(self):
        with self.assertRaises(ValueError):
            sim([drone("X1", "A")], [intruso("X1", "B")])


class TestVelocidade(unittest.TestCase):
    def test_travessia_demora_ceil_comprimento_sobre_velocidade(self):
        # A-B tem comprimento 3: velocidade 1 -> 3 passos; velocidade 2 -> ceil(1.5)=2; velocidade 3 -> 1
        for velocidade, esperado in [(1, 3), (2, 2), (3, 1)]:
            s = sim([drone("DR1", "A", velocidade)])
            s.atribuir_percurso("DR1", ["A", "B"])
            while s.drones["DR1"].posicao != "B":
                s.passo()
            self.assertEqual(s.tempo, esperado, f"velocidade {velocidade}")

    def test_posicao_so_muda_na_chegada(self):
        s = sim([drone("DR1", "A")])
        s.atribuir_percurso("DR1", ["A", "B"])
        s.passo()
        s.passo()
        self.assertEqual(s.drones["DR1"].posicao, "A")      # ainda em trânsito
        self.assertIn("DR1", s.movimentos)
        s.passo()
        self.assertEqual(s.drones["DR1"].posicao, "B")
        self.assertNotIn("DR1", s.movimentos)

    def test_percurso_com_varias_arestas_soma_os_custos(self):
        # O tempo total simulado tem de coincidir com o g(n) calculado pelo A* (mesma unidade)
        # (o intruso parado mantém a missão ativa: sem intrusos ativos a missão já terminou)
        s = sim([drone("DR1", "A", velocidade=2)], [intruso("IN1", "D")])
        r = a_estrela(s.ambiente, "A", "D", 2)
        s.atribuir_percurso("DR1", r["caminho"])
        s.executar(ate_percursos_acabarem=True)
        self.assertEqual(s.drones["DR1"].posicao, "D")
        self.assertEqual(s.tempo, r["custo"])
        self.assertEqual(s.tempo, custo_caminho(s.ambiente, r["caminho"], 2))

    def test_velocidades_diferentes_chegam_em_tempos_diferentes(self):
        s = sim([drone("DR1", "A", 3)], [intruso("IN1", "A", 1)])
        s.atribuir_percurso("DR1", ["A", "B"])
        s.atribuir_percurso("IN1", ["A", "B"])
        s.passo()
        self.assertEqual(s.drones["DR1"].posicao, "B")       # 1 passo
        self.assertEqual(s.intrusos["IN1"].posicao, "A")     # ainda a andar
        s.passo()
        s.passo()
        self.assertEqual(s.intrusos["IN1"].posicao, "B")     # 3 passos

    def test_intruso_e_drone_movem_se_em_simultaneo(self):
        s = sim([drone("DR1", "D")], [intruso("IN1", "A")])
        s.atribuir_percurso("DR1", ["D", "C"])
        s.atribuir_percurso("IN1", ["A", "B"])
        self.assertEqual(set(s.movimentos), {"DR1", "IN1"})


class TestPercursos(unittest.TestCase):
    def test_caminho_tem_de_comecar_onde_o_agente_decide(self):
        s = sim([drone("DR1", "A")])
        with self.assertRaises(ValueError):
            s.atribuir_percurso("DR1", ["B", "C"])

    def test_caminho_vazio_e_agente_desconhecido(self):
        s = sim([drone("DR1", "A")])
        with self.assertRaises(ValueError):
            s.atribuir_percurso("DR1", [])
        with self.assertRaises(ValueError):
            s.atribuir_percurso("XX", ["A", "B"])

    def test_atribuir_nao_altera_a_lista_do_chamador(self):
        s = sim([drone("DR1", "A")])
        caminho = ["A", "B", "C"]
        s.atribuir_percurso("DR1", caminho)
        s.executar(ate_percursos_acabarem=True)
        self.assertEqual(caminho, ["A", "B", "C"])

    def test_ponto_de_decisao_em_transito_e_o_destino(self):
        s = sim([drone("DR1", "A")], [intruso("IN1", "D")])
        s.atribuir_percurso("DR1", ["A", "B"])
        self.assertEqual(s.ponto_de_decisao("DR1"), "B")
        # novo percurso a meio da aresta: tem de começar em B
        s.atribuir_percurso("DR1", ["B", "C"])
        s.executar(ate_percursos_acabarem=True)
        self.assertEqual(s.drones["DR1"].posicao, "C")

    def test_percurso_de_um_so_no_nao_faz_nada(self):
        s = sim([drone("DR1", "A")])
        s.atribuir_percurso("DR1", ["A"])
        self.assertFalse(s.tem_percursos_pendentes())


class TestBloqueios(unittest.TestCase):
    def test_porta_fechada_faz_o_agente_esperar_e_depois_continuar(self):
        s = sim([drone("DR1", "B")])
        s.ambiente.alterar_porta("B", "C", False)
        s.atribuir_percurso("DR1", ["B", "C"])
        self.assertNotIn("DR1", s.movimentos)
        s.passo()
        s.passo()
        self.assertEqual(s.drones["DR1"].posicao, "B")
        self.assertIn("DR1", s.bloqueados)

        s.ambiente.alterar_porta("B", "C", True)           # a porta abre
        s.passo()                                          # começa a travessia (comp. 4, vel. 1)
        self.assertNotIn("DR1", s.bloqueados)
        for _ in range(4):
            s.passo()
        self.assertEqual(s.drones["DR1"].posicao, "C")

    def test_bloqueio_e_registado_uma_so_vez(self):
        s = sim([drone("DR1", "B")])
        s.ambiente.alterar_porta("B", "C", False)
        s.atribuir_percurso("DR1", ["B", "C"])
        for _ in range(5):
            s.passo()
        bloqueios = [t for t in s.registo if "bloqueado" in t[1]]
        self.assertEqual(len(bloqueios), 1)

    def test_barreira_ativa_tambem_bloqueia(self):
        s = sim([drone("DR1", "C")])
        s.ambiente.adicionar_barreira("C", "D", True)
        s.atribuir_percurso("DR1", ["C", "D"])
        s.passo()
        self.assertEqual(s.drones["DR1"].posicao, "C")


class TestFim(unittest.TestCase):
    def test_termina_no_limite_de_tempo(self):
        s = sim([drone("DR1", "A")], [intruso("IN1", "D")], duracao=7)
        self.assertEqual(s.executar(), 7)
        self.assertTrue(s.terminou())

    def test_termina_quando_nao_ha_intrusos_ativos(self):
        s = sim([drone("DR1", "A")], [intruso("IN1", "D")], duracao=50)
        s.intrusos["IN1"].estado = "capturado"
        self.assertTrue(s.terminou())
        self.assertEqual(s.executar(), 0)

    def test_intruso_nao_ativo_nao_se_move(self):
        s = sim([], [intruso("IN1", "A")])
        s.intrusos["IN1"].estado = "fugido"
        s.atribuir_percurso("IN1", ["A", "B"])
        s.passo()
        self.assertEqual(s.intrusos["IN1"].posicao, "A")
        self.assertNotIn("IN1", s.movimentos)

    def test_max_passos(self):
        s = sim([drone("DR1", "A")], [intruso("IN1", "D")], duracao=50)
        self.assertEqual(s.executar(max_passos=4), 4)


class TestRepetibilidade(unittest.TestCase):
    def test_duas_execucoes_iguais_dao_o_mesmo_registo(self):
        def correr():
            s = sim([drone("DR1", "A", 2), drone("DR2", "D", 1)], [intruso("IN1", "B")])
            s.atribuir_percurso("DR1", ["A", "B", "C"])
            s.atribuir_percurso("DR2", ["D", "C", "B"])
            s.executar(ate_percursos_acabarem=True)
            return s.registo
        self.assertEqual(correr(), correr())


class TestCenarios(unittest.TestCase):
    def test_carregar_cenarios_json(self):
        for nome, n_drones, n_intrusos in [("01_basico.json", 1, 1), ("02_dinamico.json", 3, 2)]:
            s = Simulacao.carregar(os.path.join(RAIZ, "cenarios", nome))
            self.assertEqual(len(s.drones), n_drones)
            self.assertEqual(len(s.intrusos), n_intrusos)
            self.assertGreater(s.duracao_maxima, 0)

    def test_importar_nao_executa_nada(self):
        # Garante que o módulo não tem código solto (o protótipo antigo corria ao importar)
        import importlib
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            import simulacao
            importlib.reload(simulacao)
        self.assertEqual(buf.getvalue(), "")


if __name__ == "__main__":
    unittest.main()