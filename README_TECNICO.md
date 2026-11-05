# Guia técnico do repositório

Este documento descreve a implementação atual do projeto, o papel das pastas e arquivos principais, o fluxo dos dados e o que ainda precisa de atenção. O README principal apresenta o estudo; este guia serve como mapa técnico para manutenção e apresentação do código.

## Estado geral

O fluxo analítico principal está implementado: a partir da seleção validada e das bases disponíveis, `run_pipeline.py` calcula métricas por 90 minutos, percentis, índices, estatísticas descritivas, testes não paramétricos e gráficos PNG. O banco SQLite é carregado com `python -m src.db`; os notebooks apresentam a exploração e os resultados.

O pipeline também gera a base profissional histórica separada, atualmente com 580 vínculos jogador-clube e 559 jogadores únicos observados entre 2012 e 2026. O frontend mostra essa população em um gráfico interativo de jogos × minutos; formação é marcada como confirmada apenas para os 35 atletas revisados, e índices não são inferidos para os demais.

As estatísticas por temporada entram por snapshots CSV locais cuja obtenção e reutilização estejam autorizadas. O projeto não automatiza consultas ao Sofascore nem tenta contornar controles de acesso.

Os importadores de trajetória e a análise de Spearman são recursos opcionais: dependem de arquivos locais de temporadas conferidos. O quadro **O que falta** registra as limitações remanescentes.

## Arquitetura em uma visão

```text
Fontes externas e conferência manual
                |
                v
       data/raw/ + data/manual/
                |
                v
        run_pipeline.py
        |       |       |
        v       v       v
   tratamento features análise
        |               |
        +-------+-------+
                v
         data/processed/
                |
        +-------+--------+
        v                v
  reports/graficos/   notebooks/
        |
        v
  frontend/ (lê CSVs processados)

Pós-pipeline opcional: python -m src.db -> SQLite + scripts em sql/
```

O identificador do jogador do Transfermarkt (`player_id`) é a chave de integração entre as bases. O `run_pipeline.py` é o orquestrador analítico. A criação e a atualização do SQLite são uma etapa separada, executada depois do pipeline.

## Estrutura detalhada

### Arquivos da raiz

| Arquivo | Responsabilidade |
|---|---|
| `README.md` | Apresentação do problema, escopo, fontes, metodologia e instruções resumidas. |
| `README_TECNICO.md` | Este guia: arquitetura, descrição dos módulos, comandos e situação de implementação. |
| `run_pipeline.py` | Executa o fluxo analítico completo, valida entradas, gera dados processados e exporta gráficos PNG. Não cria nem atualiza o SQLite. |
| `requirements.txt` | Dependências Python do pipeline, testes, visualização, notebooks e exportação PNG, incluindo SciPy, pandas, Plotly, Kaleido e nbformat. |
| `.env.example` | Informa que o fluxo atual não exige variáveis de ambiente. |
| `.gitignore` | Exclui dados brutos e intermediários, ambiente virtual, caches Python e resultados locais indicados. |

### `config/`

| Arquivo | Responsabilidade |
|---|---|
| `settings.py` | Raiz do projeto, caminhos de dados, IDs dos quatro clubes, padrões usados na busca de jogadores formados e critérios de seleção. |
| `metricas.yaml` | Definição prévia dos índices técnico e explosivo, métricas que entram em cada um, fontes e pesos. |
| `posicoes.yaml` | Mapeia as posições originais para seis categorias funcionais e declara grupos de fallback. |

**Critério vigente:** o corte de estreia profissional pelo clube formador é 2016, conforme `config/settings.py`, `README.md` e a tela de metodologia do frontend. A amostra processada atual tem 35 jogadores, dos quais nove estrearam antes de 2020.

### `data/`

Contém dados de entrada e artefatos tabulares. Confira os termos de uso e a proveniência de cada fonte antes de reutilizar ou redistribuir os dados.

#### `data/raw/`

- `players.csv`, `appearances.csv` e `transfers.csv`: tabelas originais do conjunto `davidcariboo/player-scores` no Kaggle, baseado em dados Transfermarkt.
- `sofascore/*.json`: arquivos legados de cache, se presentes; o fluxo atual não coleta nem lê esses arquivos.
- `info.txt` e `.gitkeep`: notas e preservação da estrutura da pasta.

#### `data/manual/`

| Arquivo | Responsabilidade |
|---|---|
| `jogadores_validos.csv` | Planilha de candidatos revisada pelo grupo, com confirmação de formação e fonte/justificativa de conferência. |
| `ids_sofascore.csv` | Mapeamento histórico de IDs conferidos; a importação atual usa `id_tm` já associado no snapshot local. |
| `ids_sofascore_profissionais.csv` | Mapeamento histórico da coorte profissional; não é consumido pelo importador atual. |
| `metodos_academias.csv` | Descrição qualitativa dos métodos de formação das quatro academias. As fontes registradas precisam ser conferidas e especificadas por linha para uma entrega bibliográfica rigorosa. |

#### `data/interim/`

- `candidatos_formados.csv`: candidatos iniciais gerados a partir de aparições e transferências para revisão humana.
- `sofascore_temporada.csv`: snapshot local validado, organizado por jogador, temporada, torneio e métrica.
- `sofascore_profissionais.csv`: snapshot local validado para a coorte histórica ampliada.
- `por90_appearances.csv`: métricas de aparições agregadas por jogador e temporada, incluindo minutos e taxas por 90.
- `por90_sofascore.csv`: métricas do Sofascore com minutos, tipo da métrica e valor por 90 quando aplicável.
- `info.txt` e `.gitkeep`: notas e estrutura da pasta.

#### `data/processed/`

| Arquivo | Responsabilidade |
|---|---|
| `jogadores_validos.csv` | Seleção final que o pipeline usa. Deve corresponder à revisão manual aprovada. |
| `percentis_metricas.csv` | Métricas observadas, grupo de comparação posicional, percentil e peso por jogador. |
| `indices_jogadores.csv` | Índices técnico e explosivo por jogador, cobertura, posição e dados contextuais. |
| `jogadores_profissionais.csv` | Resumo histórico por vínculo jogador-clube desde 2012, com anos observados, jogos, minutos e status de confirmação da formação. |
| `indices_profissionais.csv` | Índices posicionais técnico/explosivo da coorte histórica, com coberturas e contagem de métricas válidas. Exige ao menos 50% de cobertura por índice. |
| `carreira_jogadores.csv` | Jogos, minutos, gols, assistências, temporadas observadas e idade de estreia por jogador. |
| `cobertura_metricas.csv` | Quantidade e proporção de jogadores com dado disponível por métrica. |
| `descritiva_academias.csv` | `n`, ausências, mediana, quartis, mínimo e máximo por academia e índice. |
| `kruskal_wallis.csv` | Estatística e valor-p dos testes globais dos dois índices. |
| `mann_whitney_bonferroni.csv` | Testes pareados, p-valor bruto e ajustado, diferença de medianas e rank-biserial. |
| `formacao_jogadores.sqlite3` | Banco SQLite local criado/atualizado por `python -m src.db`; é a camada relacional para consultas e validações SQL, regenerável dos CSVs e ignorado pelo Git. |
| `info.txt` e `.gitkeep` | Notas e estrutura da pasta. |

### `src/`

Código Python do projeto, dividido por responsabilidade.

#### `src/coleta/`

- `transfermarkt.py`: lê `players.csv`, `appearances.csv` e `transfers.csv`; monta candidatos; atualiza a planilha manual sem apagar conferências existentes; gera a seleção final segundo `settings.py`.
- `sofascore.py`: valida e importa snapshots CSV locais autorizados para a amostra ou a coorte profissional; não faz requisições externas.
- `bdfutbol.py`: valida e normaliza temporadas de formação em um CSV local previamente obtido; não faz scraping.
- `uefa_youth.py`: valida e normaliza participações da UEFA Youth League em um CSV local previamente obtido; não faz scraping.
- `__init__.py`: marca o pacote Python.

#### `src/tratamento/`

- `por90.py`: cria as tabelas intermediárias de aparições e Sofascore, calcula taxas por 90 e marca amostras abaixo do mínimo de minutos.
- `percentis.py`: converte combinações conhecidas de posição e subposição em categorias funcionais; rejeita posições desconhecidas.
- `integracao.py`: junta tabelas pelo `player_id` Transfermarkt, com validação explícita da cardinalidade; usado por `run_pipeline.py` e pelas features.
- `limpeza.py`: normaliza colunas, textos e IDs sem descartar observações; rejeita IDs inválidos ou duplicados. Chamado pelo pipeline.
- `__init__.py`: marca o pacote Python.

#### `src/features/`

- `trajetoria.py`: resume temporadas de formação por jogador e academia; conta temporadas observadas e não presume continuidade em lacunas da fonte.
- `carreira.py`: calcula jogos, minutos, gols, assistências, temporadas com aparições e idade de estreia; chamado pelo pipeline e exportado em `carreira_jogadores.csv`.
- `__init__.py`: marca o pacote Python.

#### `src/analise/`

- `descritiva.py`: resumos por academia, incluindo contagens, medianas, quartis e proporções.
- `testes.py`: Kruskal–Wallis, Mann–Whitney com Bonferroni e efeitos por diferença de medianas/rank-biserial.
- `efeito.py`: utilitários de tamanho de efeito usados pela análise.
- `correlacao.py`: calcula correlações de Spearman entre features de trajetória e carreira, com tamanho mínimo de amostra e ajuste de Bonferroni. É exploratória e requer dados de trajetória estruturados.
- `jogadores_profissionais.py`: agrega aparições históricas dos quatro clubes, identifica apenas formações confirmadas na seleção manual e anexa índices já calculados sem imputar valores. Gere com `python -m src.analise.jogadores_profissionais`.
- `indices_profissionais.py`: recalcula os índices ponderados configurados em `metricas.yaml` usando percentis posicionais na coorte profissional; requer um snapshot local e conserva como ausentes índices com menos de 50% de cobertura.
- `lacunas_profissionais.py`: gera `data/processed/lacunas_estatisticas_profissionais.csv`, uma linha por jogador com presença por métrica, índices disponíveis e lista de lacunas. Gere com `python -m src.analise.lacunas_profissionais`. Presença de uma métrica indica pelo menos um valor local e não garante amostra suficiente para pontuação.
- `__init__.py`: marca o pacote Python.

#### `src/qualitativo/`

- `metodos_academias.py`: gera `data/manual/metodos_academias.csv` com fonte institucional, aspecto documentado e limite da evidência. Não atribui estilos táticos quando a fonte não os sustenta. Regere com `python -m src.qualitativo.metodos_academias`.
- `__init__.py`: marca o pacote Python.

#### `src/visual/`

- `graficos.py`: prepara dados visuais e cria dispersão, boxplots, contagem de jogadores e idade média de estreia com Plotly.
- `dashboard.py`: interface Streamlit exploratória; lê os índices processados ou aceita um CSV carregado.
- `__init__.py`: marca o pacote Python.

#### `src/db.py`

Cria/conecta ao SQLite, executa os scripts de esquema/índices/views e importa as bases processadas e intermediárias. É executado separadamente do `run_pipeline.py`.

### `sql/`

Scripts destinados ao SQLite local criado por `src/db.py`.

| Arquivo | Responsabilidade |
|---|---|
| `01_schema.sql` | Define `clube`, `jogador`, `passagem_base`, `jogador_profissional`, `estatistica_temporada`, `indice_jogador`, `percentil_metrica`, `cobertura_metrica`, `descritiva_academia`, `teste_kruskal_wallis`, `teste_mann_whitney` e `carreira_jogador`, com chaves e verificações de faixa. |
| `02_indices.sql` | Cria índices para consultas por academia, jogador/temporada, métrica e estreia. |
| `03_views.sql` | Cria views de jogadores com índices, profissionais históricos, resumos por academia, estatísticas sazonais, resultados estatísticos e métricas individuais. |
| `04_qualidade_dados.sql` | Consultas de auditoria para formações ausentes, duplicidades, faixas inválidas e estatísticas sem vínculo, além de contagens gerais. |

Executar `python -m src.db` aplica os três primeiros scripts e importa os CSVs. `04_qualidade_dados.sql` é uma lista de consultas de verificação para executar no SQLite; as consultas de inconsistência devem retornar zero linhas.

A base atual contém 4 academias, 35 jogadores com índices, 436 percentis, 13 linhas de cobertura, 8 resumos descritivos, 2 testes de Kruskal–Wallis, 12 comparações de Mann–Whitney, 78.445 estatísticas por temporada e 580 vínculos históricos jogador-clube. O recorte depende da cobertura de `appearances.csv` (2012–2026) e não representa os elencos atuais. A tabela de carreira só recebe linhas quando `carreira_jogadores.csv` está disponível.

### `notebooks/`

- `01_exploracao.ipynb`: carrega os CSVs processados; mostra composição por academia/posição, boxplots, dispersão técnico × explosivo e cobertura das métricas. É exploratório e não recalcula os índices.
- `02_resultados.ipynb`: apresenta estatística descritiva, Kruskal–Wallis, comparações Mann–Whitney ajustadas e os PNGs gerados pelo pipeline; inclui interpretação e limitações.

Os notebooks usam o ambiente `.venv` e os caminhos relativos à raiz do projeto. Antes de abrir, gere os arquivos processados executando `python run_pipeline.py`.

### `reports/graficos/`

Imagens PNG de alta resolução produzidas ao final do pipeline:

- `dispersao_tecnico_explosivo.png`: cada ponto representa um jogador, colorido por academia.
- `boxplots_indices.png`: distribuição dos dois índices por academia.
- `jogadores_revelados.png`: contagem de jogadores da amostra por academia.
- `idade_estreia.png`: idade média na estreia profissional, quando os dados estão disponíveis.

### `tests/`

- `test_pipeline.py`: valida regras e saídas do fluxo analítico.
- `test_por90.py`: testa taxas por 90, períodos e critérios mínimos de minutos.
- `test_percentis.py`: testa a classificação de posições válidas e a rejeição de entradas desconhecidas; `test_pipeline.py` cobre o cálculo dos percentis.
- `test_descritiva.py`: testa os resumos por academia.
- `test_estatistica.py`: testa os testes não paramétricos e efeitos.
- `test_graficos.py`: testa preparação dos dados e construção das figuras.
- `test_sofascore.py`: testa validação e importação de snapshots locais.
- `test_tratamento_trajetoria_carreira.py`: testa limpeza, junções por ID, importação de temporadas, features e correlação de Spearman.

Executar da raiz: `python -m pytest`.

### `frontend/`

Aplicação React + TypeScript construída com Vite. Consome diretamente CSVs de `data/processed/` durante o build/desenvolvimento.

- `src/App.tsx`: páginas do painel, jogadores, metodologia, fontes e apresentação interativa do projeto.
- `src/App.css` e `src/index.css`: componentes, responsividade, cores e quadrícula de fundo.
- `src/main.tsx`: ponto de entrada React.
- `public/logos/`: escudos SVG usados nos filtros das academias.
- `public/favicon.svg`, `public/icons.svg`: recursos estáticos do frontend.
- `package.json` e `package-lock.json`: dependências e comandos npm.
- `vite.config.ts`, `tsconfig*.json`, `.oxlintrc.json`: configuração de build, TypeScript e lint.
- `dist/`: build de produção gerado; não é fonte do aplicativo.

Comandos, executados dentro de `frontend/`:

```bash
npm install
npm run dev
npm run build
```

## Fluxos de execução

### Recalcular análises e PNGs

Na raiz do projeto, com `.venv` ativo e os dados de entrada presentes:

```bash
python run_pipeline.py
```

O script exige `data/processed/jogadores_validos.csv`, `data/raw/appearances.csv` e `data/interim/sofascore_temporada.csv`. Recria tabelas por 90, percentis, índices, análises estatísticas e os PNGs. Não coleta novamente as fontes e não atualiza o SQLite.

### Atualizar o SQLite

Depois do pipeline:

```bash
python -m src.db
```

O comando cria/atualiza `data/processed/formacao_jogadores.sqlite3` a partir dos CSVs. O arquivo fica local e não é versionado; o esquema e as consultas permanecem versionados em `sql/`. Para executar as verificações SQL, abra o banco com uma ferramenta SQLite e rode `sql/04_qualidade_dados.sql`.

### Importar um snapshot local de estatísticas

O projeto não consulta a API do Sofascore nem tenta contornar controles de acesso. Obtenha um snapshot de fonte cuja reutilização esteja autorizada, associe cada jogador ao seu `id_tm` Transfermarkt conferido e use as colunas `id_tm`, `temporada`, `torneio`, `metrica` e `valor`.

```bash
python -m src.coleta.sofascore importar caminho/para/snapshot.csv
# Para a coorte histórica:
python -m src.coleta.sofascore importar caminho/para/snapshot.csv --destino profissionais
```

O importador valida campos, tipos e duplicatas antes de gravar em `data/interim/sofascore_temporada.csv` ou `data/interim/sofascore_profissionais.csv`. A origem e a permissão de uso dos dados devem ser documentadas pelo grupo.

Para auditar os dados existentes e identificar métricas ausentes por jogador:

```bash
python -m src.analise.lacunas_profissionais
```

O relatório é regenerável a partir dos CSVs locais. `tem_<métrica>` significa que foi encontrado ao menos um valor para o atleta; `tem_snapshot_sofascore` indica qualquer registro no snapshot, enquanto `tem_metrica_sofascore_configurada` indica presença de ao menos uma métrica usada nos índices. A elegibilidade do índice é indicada separadamente pelas colunas de disponibilidade e cobertura.

### Importar temporadas de formação e analisar trajetória

Os módulos BDFutbol e UEFA Youth League não automatizam acesso a sites. Prepare arquivos locais autorizados e com IDs Transfermarkt já conferidos. Para BDFutbol, o CSV precisa conter `player_id`, `academia` e `temporada`; para UEFA, inclua também `competicao`. Os rótulos de temporada aceitos são `2018/19`, `2018-2019` ou `2018`.

```bash
python -m src.coleta.bdfutbol caminho/temporadas.csv
python -m src.coleta.uefa_youth caminho/participacoes.csv
```

Cada comando grava um CSV normalizado em `data/interim/`. Combine os arquivos, se necessário, e passe a tabela com `player_id`, `academia` e `ano_temporada` para `src.features.trajetoria.resumir_trajetoria()`. Use o resultado e `data/processed/carreira_jogadores.csv` em `src.analise.correlacao.correlacionar_trajetoria_carreira()`. A função ajusta os p-valores por Bonferroni; a análise permanece exploratória e não permite inferência causal.

## O que falta ou merece revisão antes da entrega

1. **Dados de trajetória:** os importadores estão implementados, mas dependem de arquivos locais com temporadas e IDs conferidos; a análise de Spearman não deve ser apresentada como resultado enquanto essa entrada não existir.
2. **Evidência qualitativa:** a tabela registra diferenças de detalhe entre as fontes. Complemente-a se houver fontes primárias adicionais, sem inferir a metodologia de treino a partir do estilo do time profissional.
3. **Revisão acadêmica:** conferir referências bibliográficas, critérios de inclusão, interpretação do índice explosivo e limitações com a orientação antes de apresentar.

Assim, o pipeline analítico, os recursos de carreira/trajetória, os notebooks, os gráficos e o carregamento SQLite estão implementados. A análise de trajetória depende de dados externos estruturados e conferidos.