# Trabalho de IA 2026/27 — Estrutura mínima

**Tema:** Perseguição, interceção e coordenação de drones em labirintos dinâmicos.
**Objetivo desta pasta:** servir de ponto de partida, sem código implementado.
**Enunciado:** «2026_2027_Enunciado_TP_IA_PT_ VFinal-1.pdf» (4 páginas).

## O que vamos realmente construir

1. Um **grafo** para o edifício, com portas/barreiras, bens, saídas e recargas.
2. Um **simulador por passos temporais**, com drones e intrusos de velocidades/custos distintos,
   deteção, recolha de bens, captura, fuga e replaneamento quando o mapa muda.
3. **BFS** (não informado) e **A-star (A*)** (informado), usados como referências comparáveis.
4. **Duas heurísticas desenvolvidas pelo grupo** para apoiar a procura e testar o seu impacto.
5. Uma estratégia de **perseguição simples** e outra de **coordenação original** entre drones.
6. **Dois perfis de intrusos** (por exemplo: prioriza bens vs. prioriza fuga).
7. **Três hipóteses** testadas por experiências repetidas em cenários diferentes.

## Estrutura

- `src/` — oito módulos Python; por enquanto **só comentários** (nenhum algoritmo escrito).
- `cenarios/` — três ficheiros JSON válidos, **esqueletos incompletos** com campos por preencher.
- `testes/` — dois ficheiros Python apenas com instruções para futuros testes.
- `relatorio/GUIA_RELATORIO.md` — tópicos obrigatórios do relatório/apresentação.
- `PLANO_FASES.txt` — checklist por fases, em sequência, para uma pessoa desenvolver o projeto de ponta a ponta.

## Escolhas para manter o trabalho pequeno

- Começar com **um mapa pequeno**, um intruso e um drone; adicionar complexidade depois.
- Representar portas/barreiras como ligações que abrem/fecham, sem física 3D ou interface gráfica.
- Usar um ciclo de simulação simples, sem threads, servidor, base de dados ou interface web.
- Gerar dados e gráficos apenas se forem úteis à comparação; não criar infraestrutura extra.
- Escolher **uma** estratégia original e **duas** heurísticas próprias: não multiplicar variantes.
- Fazer **três cenários representativos** e repetições com sementes controladas.

## Decisões que temos de tomar antes de programar

- O que é uma posição/estado e qual é a ordem das ações em cada passo temporal?
- Como tratar velocidades diferentes, autonomia, recarga e custo operacional?
- Quando é que um intruso fica detetado, capturado ou consegue fugir?
- Como garantir que um cenário tem sempre rota de evacuação válida, como pede o enunciado?
- Qual é a função de custo comum às comparações? Que métricas não entram no custo?
- Como definir a coordenação original e as duas heurísticas sem confundi-las com BFS/A*?
- Que bibliotecas usar? Python standard chega para o núcleo; terceiros são opcionais.

## Limites de âmbito

**Não exigido pelo enunciado:** Ollama, LLMs, Prolog, aplicação web, GUI 3D, otimização
meta-heurística ou implementação de todos os algoritmos estudados em IA.
Esses conteúdos da cadeira podem ser úteis para ideias, mas não são necessários para
cumprir o trabalho.

**Nota:** esta estrutura é de planeamento, ainda não é um programa executável.
