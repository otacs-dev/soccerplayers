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
| Jogador válido | Formação confirmada manualmente, estreia profissional pelo clube formador a partir de 2016 e pelo menos 900 minutos pelo time principal desse clube |
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
| [`davidcariboo/player-scores`](https://www.kaggle.com/datasets/davidcariboo/player-scores) (Kaggle) | Jogadores, posições, aparições, valores, transferências | Baixar `players.csv`, `appearances.csv` e `transfers.csv` para `data/raw/`; conferir os campos e a licença vigentes |
| Páginas do Transfermarkt e Wikipédia | Histórico de base (clube formador, anos na base, estreia) | Preenchimento manual em `data/manual/` |
| FBref | Referência externa para consulta de estatísticas | Não é fonte dos resultados atuais; jogos, minutos, gols e assistências vêm de `appearances.csv` do dataset Kaggle |
| Sofascore | Estatísticas por temporada (passes, dribles, duelos) | Importadas de snapshots locais autorizados; IDs Transfermarkt conferidos pelo grupo |

Respeite os termos de uso de cada fonte e mantenha a identificação da origem dos dados.

-----------------------------------------------------------------------------------------------------------------------------------------

## Metodologia

1. **Padronização por 90 minutos:** `métrica ÷ minutos × 90`, para comparar quem jogou mais com quem jogou menos.
2. **Percentil dentro da posição** (e da liga e temporada, quando possível). Os jogadores são agrupados em seis categorias: goleiro, zagueiro, lateral, meio-campista defensivo/central, meia ofensivo/ponta (inclui meias laterais) e centroavante (inclui segundo atacante). Quando uma categoria tem menos de cinco jogadores, o pipeline recorre ao grupo da posição ampla; se esse grupo ainda for pequeno, emite um aviso e mantém os dados, sem afirmar que o mínimo foi atingido.
3. **Índices técnico e explosivo:** média ponderada dos percentis das métricas de cada grupo, de 0 a 100. Os pesos são definidos previamente em `config/metricas.yaml`; quando há métricas ausentes, o índice usa os pesos disponíveis e só é publicado com cobertura mínima de 50%.
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
config/                 parâmetros, posições e pesos das métricas
data/
  raw/                  arquivos originais (não versionados)
  interim/              dados intermediários e snapshots importados
  manual/               seleção revisada e registros qualitativos
  processed/            resultados analíticos e banco SQLite local
frontend/               aplicação React/TypeScript
notebooks/              exploração e apresentação dos resultados
reports/graficos/       gráficos exportados
sql/                    esquema, consultas e verificações SQLite
src/
  coleta/               leitura de dados e importação de snapshots
  tratamento/           limpeza, integração, taxas por 90 e posições
  features/             carreira e trajetória
  analise/              índices, estatística e comparações
  visual/               gráficos e dashboard
tests/                  testes automatizados
run_pipeline.py         execução do pipeline analítico
```

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

# 4. dados de entrada
# Baixe https://www.kaggle.com/datasets/davidcariboo/player-scores
# e coloque players.csv, appearances.csv e transfers.csv em data/raw/.
# Prepare também um snapshot local autorizado com o formato documentado abaixo.
python -m src.coleta.sofascore importar caminho/para/snapshot.csv

# 5. pipeline completo
python run_pipeline.py

# 6. criar/atualizar o banco SQLite com os CSVs processados
python -m src.db
```

Execute sempre a partir da **raiz do projeto**, para os imports `src.…` funcionarem. Para os testes:

```bash
python -m pytest
```

O snapshot deve ser um CSV local autorizado com as colunas `id_tm`, `temporada`, `torneio`, `metrica` e `valor`. `id_tm` é o ID Transfermarkt conferido no projeto; cada combinação jogador-temporada-torneio-métrica deve aparecer uma única vez. Para alimentar a coorte histórica, use `--destino profissionais`; para a amostra original, o destino padrão é `amostra`:

```bash
python -m src.coleta.sofascore importar caminho/para/snapshot.csv --destino profissionais
```

O importador valida e grava o arquivo em `data/interim/`; ele não busca IDs, não acessa serviços externos e não contorna controles de acesso. A proveniência e a autorização do snapshot devem ser mantidas pelo grupo.

### Banco SQLite

O SQLite é a camada relacional consultável do trabalho: organiza jogadores, academias, formação, métricas sazonais e índices, permitindo explorar os resultados com SQL em ferramentas como DB Browser for SQLite e executar as views e verificações de qualidade. Os scripts em `sql/` definem o esquema, índices, views e consultas. Depois de executar o pipeline, carregue os dados processados no banco local com:

```bash
python -m src.db
```

O arquivo `data/processed/formacao_jogadores.sqlite3` é criado ou atualizado a partir dos CSVs de `data/processed/` e `data/interim/`. Ele é um artefato local regenerável e fica fora do Git; assim, o repositório mantém o esquema e as consultas SQL, sem acumular cópias binárias do banco. Para conferir a qualidade, execute `sql/04_qualidade_dados.sql`; as consultas de inconsistência devem retornar zero linhas. Recrie o banco com `python -m src.db` sempre que atualizar os CSVs.

Na carga atual, o banco contém os **35 jogadores analisados** (Barcelona: 15; Liverpool: 8; Manchester City: 7; Real Madrid: 5), seus índices e 436 percentis, além de cobertura de métricas, estatísticas descritivas, testes estatísticos e 78.445 estatísticas sazonais. Isso representa a amostra analisada, não o elenco completo atual desses clubes. As tabelas analíticas estão definidas em `sql/01_schema.sql`; as views de consulta ficam em `sql/03_views.sql`.

Há também uma base separada para a comparação histórica de profissionais: gere `data/processed/jogadores_profissionais.csv` com `python -m src.analise.jogadores_profissionais` e depois rode `python -m src.db` para carregá-la na tabela `jogador_profissional` e na view `vw_jogadores_profissionais`. Ela reúne 580 vínculos jogador-clube (559 jogadores únicos) observados entre 2012 e 2026 nos arquivos disponíveis; alguns jogadores atuaram por mais de um dos clubes. “Formação confirmada” marca somente os 35 atletas revisados manualmente; os demais estão como “não confirmada”, não como “não formados”.

No momento, os índices técnico/explosivo comparáveis estão disponíveis para os 35 atletas da amostra original. Para recalcular os índices posicionais em toda a coorte histórica, primeiro importe um snapshot local autorizado para a coorte profissional, depois execute:

```bash
python -m src.coleta.sofascore importar caminho/para/snapshot.csv --destino profissionais
python -m src.analise.indices_profissionais
python -m src.db
```

O cálculo usa as métricas e pesos configurados em `config/metricas.yaml`; índices só são exibidos quando pelo menos 50% das métricas do índice estão disponíveis. Jogadores sem cobertura suficiente continuam sem nota. A inclusão desses atletas muda a referência dos percentis e pode alterar também os valores dos 35 jogadores já analisados. O frontend mostra jogos × minutos e índices técnico × explosivo em gráficos separados, com botões de lupa para zoom. Esse recorte histórico não equivale aos elencos atuais.

Exemplo para consultar os jogadores e índices:

```sql
SELECT player_id, nome, academia, indice_tecnico, indice_explosivo
FROM vw_jogadores_com_indices
ORDER BY academia, nome;
```

Para consultar a base profissional:

```sql
SELECT nome, clube, position, ano_primeira_aparicao, ano_ultima_aparicao,
       jogos_profissionais, minutos_profissionais, formacao_status,
       indice_tecnico, indice_explosivo
FROM vw_jogadores_profissionais
ORDER BY clube, nome;
```

### Notebooks

Abra `notebooks/01_exploracao.ipynb` para conferir a composição da amostra, índices e cobertura. Use `notebooks/02_resultados.ipynb` para apresentar medianas, quartis, testes e gráficos PNG. Se o kernel ainda não estiver configurado, selecione o ambiente virtual `.venv` do projeto. Os notebooks leem os CSVs produzidos por `python run_pipeline.py`.

### Executar o frontend

Requisitos: Node.js e npm. Na primeira vez, instale as dependências do frontend:

```bash
cd frontend
npm install
```

Depois, sempre que quiser iniciar o dashboard, execute na raiz do projeto:

```bash
cd frontend
npm run dev
```

Abra o endereço mostrado no terminal (normalmente `http://localhost:5173`). Deixe o terminal aberto enquanto estiver usando o dashboard; para encerrar o servidor, pressione `Ctrl+C`. Para gerar a versão de produção, execute dentro de `frontend`:

```bash
npm run build
```

-----------------------------------------------------------------------------------------------------------------------------------------

### Ordem do pipeline

1. Criação do esquema (`sql/01_schema.sql`)
2. Entradas locais: arquivos do dataset em `data/raw/`, snapshots autorizados validados em `data/interim/` e conferência manual
3. Tratamento: limpeza, integração, por 90 minutos e percentis
4. Features: índices técnico e explosivo
5. Análise: descritiva, Kruskal-Wallis, Mann-Whitney e tamanho de efeito
6. Visualização: gráficos e dashboard

-----------------------------------------------------------------------------------------------------------------------------------------

## Status do projeto

**Implementado**

- [x] Seleção de jogadores confirmados manualmente; amostra atual de 35 atletas, até 15 por academia.
- [x] Preparação dos dados Transfermarkt e importação validada de snapshots locais de estatísticas.
- [x] Padronização por 90 minutos, percentis posicionais e índices configuráveis.
- [x] Estatística descritiva, Kruskal–Wallis, Mann–Whitney com Bonferroni e tamanho de efeito.
- [x] Gráficos PNG, dashboard Streamlit e frontend React.
- [x] Banco SQLite, scripts de auditoria e notebooks de exploração/resultados.
- [x] Tabela qualitativa com fonte e limite de evidência por academia.
- [x] Funções para importar temporadas de formação, resumir carreira/trajetória e calcular correlações exploratórias de Spearman.

**Entradas opcionais e próximos passos**

- A amostra processada usa estreia profissional a partir de **2016**. Nove dos 35 jogadores estrearam antes de 2020; a amostra não deve ser descrita como se usasse o corte de 2020.
- Os módulos BDFutbol e UEFA Youth League aceitam CSVs locais previamente obtidos; não fazem coleta automatizada nem substituem a conferência das fontes.
- A análise de Spearman está implementada, mas só pode ser executada quando houver temporadas de formação estruturadas e vinculadas por `player_id`.
- Aumentar a amostra e incluir outras academias exige revisar a metodologia, os dados e os parâmetros em `config/settings.py`.

-----------------------------------------------------------------------------------------------------------------------------------------

## Limitações

- **Associação, não causa.** Os testes mostram se os grupos diferem, não o motivo.
- **Amostra pequena** (até 15 por grupo). Resultado sem significância não prova ausência de diferença, pode indicar poucos dados. Por isso o tamanho de efeito recebe mais atenção que o valor-p.
- **Viés de seleção.** As quatro academias já recrutam talentos acima da média.
- **Perfil explosivo aproximado** por indicadores substitutos.
- **Métricas avançadas indisponíveis** no FBref desde janeiro de 2026.
- **Valores ausentes:** o texto informa quantos jogadores ficaram de fora de cada métrica e por quê.
- **Métodos das academias:** as fontes institucionais consultadas não descrevem o mesmo nível de detalhe; a tabela informa limites e evita atribuir estilos táticos sem evidência.

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
