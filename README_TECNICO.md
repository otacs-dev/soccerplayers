# Guia técnico do repositório

Este documento descreve a implementação atual do projeto, o papel das pastas e arquivos principais, o fluxo dos dados e o que ainda precisa de atenção. O README principal apresenta o estudo; este guia serve como mapa técnico para manutenção e apresentação do código.

## Estado geral

O fluxo analítico principal está implementado: a partir da seleção validada e das bases disponíveis, `run_pipeline.py` calcula métricas por 90 minutos, percentis, índices, estatísticas descritivas, testes não paramétricos e gráficos PNG. A suíte automatizada passou com 20 testes. O banco SQLite pode ser montado com `python -m src.db`; os dois notebooks estão preenchidos e suas células foram executadas.

Isso não significa que cada módulo listado no repositório esteja concluído. Há arquivos vazios reservados para funcionalidades futuras, e existem divergências entre a documentação antiga e as regras executadas pelo código. O quadro **O que falta** registra essas ressalvas.

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
| `README.md` | Apresentação do problema, escopo, fontes, metodologia e instruções resumidas. Seu checklist e parte do texto metodológico precisam ser alinhados ao estado atual; ver **O que falta**. |
| `README_TECNICO.md` | Este guia: arquitetura, descrição dos módulos, comandos e situação de implementação. |
| `run_pipeline.py` | Executa o fluxo analítico completo, valida entradas, gera dados processados e exporta gráficos PNG. Não cria nem atualiza o SQLite. |
| `requirements.txt` | Dependências Python do pipeline, testes, visualização, notebooks e exportação PNG, incluindo SciPy, pandas, Plotly, Kaleido e nbformat. |
| `.env.example` | Modelo de variáveis de ambiente opcionais. Não contém credenciais válidas. |
| `.gitignore` | Exclui dados brutos e intermediários, ambiente virtual, caches Python e resultados locais indicados. |

### `config/`

| Arquivo | Responsabilidade |
|---|---|
| `settings.py` | Raiz do projeto, caminhos de dados, IDs dos quatro clubes, padrões usados na busca de jogadores formados e critérios de seleção. |
| `metricas.yaml` | Definição prévia dos índices técnico e explosivo, métricas que entram em cada um, fontes e pesos. |
| `posicoes.yaml` | Mapeia as posições originais para seis categorias funcionais e declara grupos de fallback. |

**Atenção:** `settings.py` define o corte final de estreia em 2016. O README principal ainda descreve estreia a partir de 2020. A regra adotada deve ser confirmada com a orientação e unificada na documentação antes da entrega.

### `data/`

Contém dados de entrada e artefatos tabulares. Dados originais podem estar sujeitos a termos de uso e não são versionados quando cobertos pelo `.gitignore`.

#### `data/raw/`

- `players.csv`, `appearances.csv` e `transfers.csv`: tabelas originais do conjunto `davidcariboo/player-scores` no Kaggle, baseado em dados Transfermarkt.
- `sofascore/*.json`: respostas em cache da coleta por jogador, temporada e competição. São arquivos brutos de apoio; não devem ser editados manualmente.
- `info.txt` e `.gitkeep`: notas e preservação da estrutura da pasta.

#### `data/manual/`

| Arquivo | Responsabilidade |
|---|---|
| `jogadores_validos.csv` | Planilha de candidatos revisada pelo grupo, com confirmação de formação e fonte/justificativa de conferência. |
| `ids_sofascore.csv` | Associação entre `player_id` do projeto e ID de jogador no Sofascore. |
| `metodos_academias.csv` | Descrição qualitativa dos métodos de formação das quatro academias. As fontes registradas precisam ser conferidas e especificadas por linha para uma entrega bibliográfica rigorosa. |

#### `data/interim/`

- `candidatos_formados.csv`: candidatos iniciais gerados a partir de aparições e transferências para revisão humana.
- `sofascore_temporada.csv`: estatísticas brutas organizadas por jogador, temporada, torneio e métrica.
- `por90_appearances.csv`: métricas de aparições agregadas por jogador e temporada, incluindo minutos e taxas por 90.
- `por90_sofascore.csv`: métricas do Sofascore com minutos, tipo da métrica e valor por 90 quando aplicável.
- `info.txt` e `.gitkeep`: notas e estrutura da pasta.

#### `data/processed/`

| Arquivo | Responsabilidade |
|---|---|
| `jogadores_validos.csv` | Seleção final que o pipeline usa. Deve corresponder à revisão manual aprovada. |
| `percentis_metricas.csv` | Métricas observadas, grupo de comparação posicional, percentil e peso por jogador. |
| `indices_jogadores.csv` | Índices técnico e explosivo por jogador, cobertura, posição e dados contextuais. |
| `cobertura_metricas.csv` | Quantidade e proporção de jogadores com dado disponível por métrica. |
| `descritiva_academias.csv` | `n`, ausências, mediana, quartis, mínimo e máximo por academia e índice. |
| `kruskal_wallis.csv` | Estatística e valor-p dos testes globais dos dois índices. |
| `mann_whitney_bonferroni.csv` | Testes pareados, p-valor bruto e ajustado, diferença de medianas e rank-biserial. |
| `formacao_jogadores.sqlite3` | Banco SQLite local criado/atualizado por `python -m src.db`; é um artefato regenerável dos CSVs. |
| `info.txt` e `.gitkeep` | Notas e estrutura da pasta. |

### `src/`

Código Python do projeto, dividido por responsabilidade.

#### `src/coleta/`

- `transfermarkt.py`: lê `players.csv`, `appearances.csv` e `transfers.csv`; monta candidatos; atualiza a planilha manual sem apagar conferências existentes; gera a seleção final segundo `settings.py`.
- `sofascore.py`: resolve IDs e coleta estatísticas por temporada, usando cache local e pausas entre requisições. A API usada não é oficial e pode mudar.
- `uefa_youth.py`: arquivo vazio no estado atual; reservado para uma coleta complementar da UEFA Youth League.
- `bdfutbol.py`: arquivo vazio no estado atual; reservado para dados complementares do BDFutbol.
- `__init__.py`: marca o pacote Python.

#### `src/tratamento/`

- `por90.py`: cria as tabelas intermediárias de aparições e Sofascore, calcula taxas por 90 e marca amostras abaixo do mínimo de minutos.
- `percentis.py`: converte posições para categorias funcionais e contém utilitários de percentis/categorização.
- `integracao.py`: arquivo vazio no estado atual; a integração usada pelo fluxo principal está implementada diretamente em `run_pipeline.py` e nos módulos que agregam as fontes.
- `limpeza.py`: arquivo vazio no estado atual; não é chamado pelo pipeline ativo.
- `__init__.py`: marca o pacote Python.

#### `src/features/`

- `indices.py`: funções reutilizáveis para ler a configuração de métricas e agregar percentis em índices. O cálculo principal executado atualmente está na função `construir_indices()` de `run_pipeline.py`.
- `trajetoria.py`: arquivo vazio; reservado para análise de trajetória na formação.
- `carreira.py`: arquivo vazio; reservado para características de carreira.
- `__init__.py`: marca o pacote Python.

#### `src/analise/`

- `descritiva.py`: resumos por academia, incluindo contagens, medianas, quartis e proporções.
- `testes.py`: Kruskal–Wallis, Mann–Whitney com Bonferroni e efeitos por diferença de medianas/rank-biserial.
- `efeito.py`: utilitários de tamanho de efeito usados pela análise.
- `correlacao.py`: arquivo vazio; a análise de Spearman prevista ainda não está implementada.
- `__init__.py`: marca o pacote Python.

#### `src/qualitativo/`

- `metodos_academias.py`: monta e salva uma tabela qualitativa para os métodos das academias. A descrição atual é geral; para a versão final, substituir referências genéricas por fontes verificáveis e específicas por afirmação.
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
| `01_schema.sql` | Define tabelas `clube`, `jogador`, `passagem_base`, `estatistica_temporada` e `indice_jogador`, com chaves e verificações de faixa. |
| `02_indices.sql` | Cria índices para consultas por academia, jogador/temporada, métrica e estreia. |
| `03_views.sql` | Cria views de jogadores com índices, resumo por academia e estatísticas por temporada. |
| `04_qualidade_dados.sql` | Consultas de auditoria para formações ausentes, duplicidades, faixas inválidas e estatísticas sem vínculo, além de contagens gerais. |

Executar `python -m src.db` aplica os três primeiros scripts e importa os CSVs. `04_qualidade_dados.sql` é uma lista de consultas de verificação para executar no SQLite; as consultas de inconsistência devem retornar zero linhas.

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
- `test_percentis.py`: testa categorização posicional e percentis.
- `test_indices.py`: testa agregação dos índices.
- `test_descritiva.py`: testa os resumos por academia.
- `test_estatistica.py`: testa os testes não paramétricos e efeitos.
- `test_graficos.py`: testa preparação dos dados e construção das figuras.
- `test_sofascore.py`: testa rotinas de identificação e tratamento do Sofascore.

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

O comando cria/atualiza `data/processed/formacao_jogadores.sqlite3` a partir dos CSVs. Para executar as verificações SQL, abra esse banco com uma ferramenta SQLite e rode `sql/04_qualidade_dados.sql`.

### Recriar a coleta do Sofascore

Somente quando precisar atualizar estatísticas ou reconstruir a base intermediária:

```bash
python -m src.coleta.sofascore coletar
```

Respeite os termos e limites de acesso do Sofascore. A coleta usa uma API não oficial e pode parar de funcionar se o serviço mudar.

## O que falta ou merece revisão antes da entrega

1. **Critério de estreia:** há divergência entre o texto do README principal (2020) e o corte executável em `config/settings.py` (2016). Confirmar a regra final com a orientação, atualizar a documentação e, se necessário, regenerar a seleção e os resultados.
2. **Módulos vazios:** `src/coleta/bdfutbol.py`, `src/coleta/uefa_youth.py`, `src/tratamento/integracao.py`, `src/tratamento/limpeza.py`, `src/features/trajetoria.py`, `src/features/carreira.py` e `src/analise/correlacao.py` existem, mas estão vazios. Não fazem parte do fluxo executável atual; preenchê-los só se estiverem no escopo exigido.
3. **Fontes qualitativas:** revisar `data/manual/metodos_academias.csv` para que cada afirmação sobre método de formação tenha uma fonte primária ou bibliográfica identificável.
4. **README principal:** atualizar o checklist, que ainda marca SQL, percentis, índices, análises e dashboard como pendentes, apesar de esses artefatos já existirem. Confirmar também a contagem de linhas coletadas, que varia conforme o estágio/base.
5. **Banco:** o SQLite é um produto local regenerável e sua carga é manual, após o pipeline. Confirmar se a banca espera apenas o modelo/documentação ou também os dados carregados e consultas executadas ao vivo.
6. **Revisão acadêmica:** conferir referências bibliográficas, critérios de inclusão, interpretação do índice explosivo e limitações com a orientação antes de apresentar.

Assim, o núcleo de análise, os notebooks, os gráficos e o carregamento SQLite estão implementados e validados, mas a conclusão acadêmica do trabalho depende de resolver as divergências documentais e confirmar os itens exigidos pela disciplina.