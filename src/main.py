# PONTO DE ENTRADA
# Uso (a partir da pasta do projeto):
#     python3 src/main.py cenarios/02_dinamico.json
#
# NOTA: nesta fase o main só DEMONSTRA o ciclo da simulação (Fase 3, ponto 1):
#   - cada drone recebe um percurso A* até à posição inicial do primeiro intruso;
#   - cada intruso recebe um percurso A* até à saída mais próxima.
# A escolha de alvos pelos drones (coordenacao.py) será integrada na Fase 4.

import sys

from simulacao import Simulacao
from procura import a_estrela


def main():
    caminho = sys.argv[1] if len(sys.argv) > 1 else "cenarios/02_dinamico.json"
    sim = Simulacao.carregar(caminho)

    # Percursos de demonstração
    alvo = next(iter(sim.intrusos.values())).posicao
    for drone in sim.drones.values():
        r = a_estrela(sim.ambiente, drone.posicao, alvo, drone.velocidade)
        if r["sucesso"] and len(r["caminho"]) > 1:
            sim.atribuir_percurso(drone.id, r["caminho"])

    for intruso in sim.intrusos.values():
        r = a_estrela(sim.ambiente, intruso.posicao, sim.ambiente.saidas, intruso.velocidade)
        if r["sucesso"] and len(r["caminho"]) > 1:
            sim.atribuir_percurso(intruso.id, r["caminho"])

    sim.executar(mostrar=True, ate_percursos_acabarem=True)
    sim.mostrar_legenda()

    print("\n--- Registo ---")
    for tempo, texto in sim.registo:
        print(f"t={tempo:>3}  {texto}")


if __name__ == "__main__":
    main()