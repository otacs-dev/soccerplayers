# Formação de Jogadores: análise comparativa de quatro academias

Projeto Integrador do curso de **Ciência de Dados** da **FATEC Baixada Santista – Rubens Lara** (2026).

--> Pergunta central: **a academia de formação ajuda a explicar o perfil técnico e explosivo dos jogadores que ela revela?**

-->O estudo compara as categorias de base de quatro clubes e usa estatística não paramétrica para verificar se os grupos diferem. Os resultados indicam **associação, não causa**.

---

## Sumário

1. [Escopo](#escopo)
2. [Desenho do estudo](#desenho-do-estudo)
3. [Fontes de dados](#fontes-de-dados)
4. [Metodologia](#metodologia)
5. [Estrutura do repositório](#estrutura-do-repositório)
6. [Como executar](#como-executar)
7. [Status do projeto](#status-do-projeto)
8. [Limitações](#limitações)
9. [Referências](#referências)
10. [Equipe](#equipe)

---

-----------------------------------------------------------------------------------------------------------------------------------------

## Escopo

| Grupo | Academia |
|---|---|
| Barcelona | La Masia |
| Real Madrid | La Fábrica |
| Manchester City | City Football Academy |
| Liverpool | The Academy |

Os métodos de treino de cada academia entram apenas como **descrição qualitativa**. Com quatro academias, o método de treino tem n = 4, o que não permite correlacioná-lo estatisticamente com a carreira dos jogadores.

-----------------------------------------------------------------------------------------------------------------------------------------

## Desenho do estudo

| Item | Regra |
|---|---|
| Unidade de análise | Jogador formado por uma das quatro academias |
| Jogador válido | Formado no clube (critério do CIES), com estreia no profissional do clube formador a partir de 2020 e 900 minutos ou mais no time principal do clube formador |
| Amostra | Até 15 jogadores por grupo, os de mais minutos |
| Dados usados | Apenas métricas que compõem os perfis técnico e explosivo |
| Análise | Mediana e quartis, Kruskal-Wallis, Mann-Whitney com Bonferroni e tamanho de efeito |

-----------------------------------------------------------------------------------------------------------------------------------------

### Perfis

- **Técnico:** precisão, controle e inteligência com a bola (volume e qualidade de passes, participação na construção das jogadas).
- **Explosivo:** capacidade física, velocidade e força (dribles, duelos ganhos, finalizações).

Velocidade e força não constam em dados de eventos. Por isso o perfil explosivo usa **indicadores substitutos** (altura, peso, duelos aéreos e terrestres ganhos), e a conclusão sobre ele é aproximada.

As métricas de cada índice estão em `config/metricas.yaml` e foram **definidas antes de olhar os resultados**, para não escolher as que "dão certo".

-----------------------------------------------------------------------------------------------------------------------------------------

## Fontes de dados

| Fonte | Uso | Observação |
|---|---|---|
| `transfermarkt-datasets` (GitHub/Kaggle) | Jogadores, posições, aparições, valores, transferências | Pode não trazer o clube formador pronto; conferir as colunas reais |
| Páginas do Transfermarkt e Wikipédia | Histórico de base (clube formador, anos na base, estreia) | Preenchimento manual em `data/manual/` |
| FBref | Dados básicos: jogos, minutos, gols, assistências | Perdeu as estatísticas avançadas (xG, passes progressivos); usamos só o básico |

Respeite os termos de uso de cada fonte. Os dados brutos **não são versionados** (ver `.gitignore`).

-----------------------------------------------------------------------------------------------------------------------------------------

## Metodologia

1. **Padronização por 90 minutos:** `métrica ÷ minutos × 90`, para comparar quem jogou mais com quem jogou menos.
2. **Percentil dentro da posição** (e da liga e temporada, quando possível). Os jogadores são agrupados em seis categorias: goleiro, zagueiro, lateral, meio-campista defensivo/central, meia ofensivo/ponta e centroavante.
3. **Índices técnico e explosivo:** média dos percentis das métricas de cada grupo, de 0 a 100.
4. **Estatística descritiva por academia:** contagem (n), mediana, quartis e proporções por posição.
5. **Testes de comparação** (não paramétricos, nível de significância de 0,05):
   - **Kruskal-Wallis** compara as quatro academias de uma vez.
   - **Mann-Whitney U** compara os pares, com correção de **Bonferroni** (0,05 dividido pelo número de comparações).
   - **Tamanho de efeito** (diferença de medianas e rank-biserial a partir do U), que com amostras pequenas importa mais do que o valor-p.
6. **Visualização:** dispersão técnico × explosivo (uma cor por academia), boxplot dos índices e barras de revelados e idade média de estreia.

A integração entre fontes usa o **identificador do Transfermarkt como chave**, e não o nome do jogador, que varia entre bases.


-----------------------------------------------------------------------------------------------------------------------------------------

## Estrutura do repositório

```
# caminhos, lista de clubes, ano inicial
# métricas de cada índice
# categorias posicionais
# dados brutos (não versionados)
# dados intermediários (não versionados)
# base padronizada
# jogadores_validos.csv, metodos_academias.csv
# tabelas
# views de análise
# contagem de ausentes por métrica e jogador
# conexão com o banco
# limpeza, integracao, por90, percentis
# indices, trajetoria, carreira
# descritiva, testes, efeito, correlacao
# metodos_academias
# graficos, dashboard
# test_por90, test_percentis, test_indice
# executa o pipeline na ordem
'''


### Modelo de dados

Banco relacional com as entidades `jogador`, `clube`, `passagem_base`, `estatistica_temporada` e `indice_jogador`. Essa separação permite consultar o histórico de formação, o desempenho por temporada e os índices de forma independente.

-----------------------------------------------------------------------------------------------------------------------------------------

## Como executar

Requisitos: Python 3.10 ou superior.

```bash
# 1. clonar
git clone https://github.com/otacs-dev/soccerplayers.git
cd soccerplayers

# 2. ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. dependências
pip install -r requirements.txt

# 4. variáveis de ambiente
cp .env.example .env             # ajuste os valores, se necessário

# 5. pipeline completo
python run_pipeline.py
```

Execute sempre a partir da **raiz do projeto**, para os imports `src.…` funcionarem. Para os testes:

```bash
python -m pytest
```

-----------------------------------------------------------------------------------------------------------------------------------------

### Ordem do pipeline

1. Criação do esquema (`sql/01_schema.sql`)
2. Coleta (`src/coleta/`), salva em `data/raw/`
3. Tratamento: limpeza, integração, por 90 minutos e percentis
4. Features: índices técnico e explosivo
5. Análise: descritiva, Kruskal-Wallis, Mann-Whitney e tamanho de efeito
6. Visualização: gráficos e dashboard

-----------------------------------------------------------------------------------------------------------------------------------------

## Status do projeto

**Escopo mínimo**

- [ ] Esquema SQL e `db.py`
- [ ] `jogadores_validos.csv` (até 15 por academia)
- [ ] Coleta: Transfermarkt e FBref
- [ ] Por 90, percentis e índices
- [ ] Descritiva por academia
- [ ] Kruskal-Wallis com tamanho de efeito
- [ ] Mann-Whitney entre pares
- [ ] Gráficos
- [ ] `metodos_academias.csv` (qualitativo, com fonte em cada linha)

**Fora do escopo mínimo (trabalhos futuros)**

- [ ] Coleta do Sofascore, UEFA Youth League e BDFutbol
- [ ] Correlação (Spearman) entre trajetória na base e carreira
- [ ] Dashboard interativo
- [ ] Inclusão de outras academias (por exemplo Ajax), adicionando o clube em `config/settings.py`

-----------------------------------------------------------------------------------------------------------------------------------------

## Limitações

- **Associação, não causa.** Os testes mostram se os grupos diferem, não o motivo.
- **Amostra pequena** (até 15 por grupo). Resultado sem significância não prova ausência de diferença, pode indicar poucos dados. Por isso o tamanho de efeito recebe mais atenção que o valor-p.
- **Viés de seleção.** As quatro academias já recrutam talentos acima da média.
- **Perfil explosivo aproximado** por indicadores substitutos.
- **Métricas avançadas indisponíveis** no FBref desde janeiro de 2026.
- **Valores ausentes:** o texto informa quantos jogadores ficaram de fora de cada métrica e por quê.
- **Método de treino com n = 4:** tratado apenas de forma descritiva.

-----------------------------------------------------------------------------------------------------------------------------------------

## Referências

- FORD, Paul R.; WILLIAMS, A. Mark. The developmental activities engaged in by elite youth soccer players who progressed to professional status compared to those who did not. *Psychology of Sport and Exercise*, v. 13, n. 3, p. 349–352, 2012.
- GLEDHILL, Adam; HARWOOD, Chris; FORSDYKE, Dale. Psychosocial factors associated with talent development in football: a systematic review. *Psychology of Sport and Exercise*, v. 31, p. 93–112, 2017.
- SATISH, Krishna et al. Possession football: the playing style that defined FC Barcelona's success and the Spanish national football team's golden generation. *Managing Sport and Leisure*, 2025.

A bibliografia completa está no relatório do projeto.

-----------------------------------------------------------------------------------------------------------------------------------------

## Equipe
- Arthur Martins
- Guilherme Onorio
- Octavio Teodoro
- Peterson Carara
FATEC Baixada Santista – Rubens Lara, Ciência de Dados, Santos – SP, 2026.