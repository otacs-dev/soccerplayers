import { useMemo, useState } from 'react'
import { Activity, ArrowLeft, ArrowDown, ArrowUpRight, BookOpen, ChevronDown, CircleHelp, Code2, Database, Download, ExternalLink, FileBarChart, FileCode2, Filter, GraduationCap, LayoutDashboard, Search, ShieldCheck, Users } from 'lucide-react'
import { CartesianGrid, Cell, ComposedChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'
import Papa from 'papaparse'
import indicesSource from '../../data/processed/indices_jogadores.csv?raw'
import descriptiveSource from '../../data/processed/descritiva_academias.csv?raw'
import kruskalSource from '../../data/processed/kruskal_wallis.csv?raw'
import './App.css'

type Player = { clube: string; nome: string; categoria: string; indice_tecnico: number; indice_explosivo: number; minutos: number; url: string }
type Summary = { academia: string; metrica: string; n: number; mediana: number; q1: number; q3: number }
type TestResult = { metrica: string; p_value: number }
const colors: Record<string, string> = { Barcelona: '#d94b43', Liverpool: '#c53d48', 'Manchester City': '#3298ad', 'Real Madrid': '#d1a342' }
const labels: Record<string, string> = { Barcelona: 'Barcelona', Liverpool: 'Liverpool', 'Manchester City': 'Man. City', 'Real Madrid': 'Real Madrid' }
const academyLogos: Record<string, string> = { Barcelona: 'barcelona.svg', Liverpool: 'liverpool.svg', 'Manchester City': 'manchester-city.svg', 'Real Madrid': 'real-madrid.svg' }
const csv = <T,>(source: string) => Papa.parse<T>(source, { header: true, dynamicTyping: true, skipEmptyLines: true }).data
const players = csv<Player>(indicesSource)
const summaries = csv<Summary>(descriptiveSource)
const tests = csv<TestResult>(kruskalSource)
const number = (value: number, digits = 1) => new Intl.NumberFormat('pt-BR', { maximumFractionDigits: digits }).format(value)

function MethodologyPage({ onBack }: { onBack: () => void }) {
  const academies = Object.keys(colors)
  const technicalTest = tests.find((test) => test.metrica === 'indice_tecnico')
  const explosiveTest = tests.find((test) => test.metrica === 'indice_explosivo')

  return <section className="method-page">
    <div className="method-hero">
      <div className="eyebrow"><i /> GUIA DO ESTUDO · MÉTODOS E RESULTADOS</div>
      <h1>Como lemos os dados<br /><em>e o que eles permitem dizer.</em></h1>
      <p>Este estudo compara os perfis de 35 jogadores formados em quatro academias. A análise descreve diferenças observadas; não identifica causas.</p>
      <button className="back-button" onClick={onBack}><ArrowLeft size={15} /> Voltar ao painel</button>
      <div className="method-hero-mark"><BookOpen size={27} /></div>
    </div>

    <div className="method-result-strip">
      <article><span>AMOSTRA</span><strong>35 <small>jogadores</small></strong><p>Barcelona 15 · Liverpool 8 · City 7 · Real Madrid 5</p></article>
      <article><span>ÍNDICE TÉCNICO</span><strong>p = {number(technicalTest?.p_value ?? 0, 3)}</strong><p>Kruskal–Wallis · sem diferença significativa</p></article>
      <article><span>ÍNDICE EXPLOSIVO</span><strong>p = {number(explosiveTest?.p_value ?? 0, 3)}</strong><p>Kruskal–Wallis · sem diferença significativa</p></article>
    </div>

    <section className="method-section">
      <div className="method-section-heading"><span>01 — DESENHO DA ANÁLISE</span><h2>Da seleção ao teste estatístico</h2><p>As regras definem quem entra na amostra e como as métricas são comparadas.</p></div>
      <div className="method-steps">
        <article><span className="step-number">01</span><h3>Quem foi incluído</h3><p>Jogadores formados por Barcelona, Real Madrid, Manchester City ou Liverpool, com estreia profissional pelo clube formador a partir de 2020 e pelo menos 900 minutos. Foram selecionados até 15 por academia, priorizando minutos.</p></article>
        <article><span className="step-number">02</span><h3>Métricas comparáveis</h3><p>Estatísticas de eventos são padronizadas por 90 minutos. Os valores são convertidos em percentis dentro da categoria posicional, com grupo mais amplo quando há poucos casos.</p></article>
        <article><span className="step-number">03</span><h3>Dois índices, 0 a 100</h3><p>Cada índice é a média ponderada dos percentis das métricas previamente definidas. O técnico reúne passe, criação, drible e participação ofensiva.</p></article>
        <article><span className="step-number">04</span><h3>Comparação não paramétrica</h3><p>Kruskal–Wallis compara as quatro academias. Mann–Whitney compara os pares com correção de Bonferroni. O nível de significância adotado é 0,05.</p></article>
      </div>
    </section>

    <section className="method-section results-section">
      <div className="method-section-heading"><span>02 — RESULTADOS DESCRITIVOS</span><h2>Medianas por academia</h2><p>O intervalo entre parênteses mostra o primeiro e o terceiro quartil. O tamanho desigual dos grupos pede cautela.</p></div>
      <div className="results-table-wrap"><table className="results-table"><thead><tr><th>ACADEMIA</th><th>N</th><th>ÍNDICE TÉCNICO<br /><small>MEDIANA (Q1–Q3)</small></th><th>ÍNDICE EXPLOSIVO<br /><small>MEDIANA (Q1–Q3)</small></th></tr></thead><tbody>
        {academies.map((academyName) => {
          const technical = summaries.find((row) => row.academia === academyName && row.metrica === 'indice_tecnico')
          const explosive = summaries.find((row) => row.academia === academyName && row.metrica === 'indice_explosivo')
          return <tr key={academyName}><td><span className="table-club"><i style={{ backgroundColor: colors[academyName] }} />{academyName}</span></td><td>{technical?.n ?? 0}</td><td><strong>{number(technical?.mediana ?? 0)}</strong><small>{number(technical?.q1 ?? 0)}–{number(technical?.q3 ?? 0)}</small></td><td><strong>{number(explosive?.mediana ?? 0)}</strong><small>{number(explosive?.q1 ?? 0)}–{number(explosive?.q3 ?? 0)}</small></td></tr>
        })}
      </tbody></table></div>
    </section>

    <section className="conclusion-grid">
      <article className="conclusion-card"><span>03 — O QUE PODEMOS CONCLUIR</span><h2>Não encontramos evidência estatística de diferença entre as academias nesta amostra.</h2><p>Os valores de p foram superiores a 0,05 nos dois índices. As comparações par a par também não foram significativas após Bonferroni. Isso não prova que os grupos sejam iguais: amostras pequenas reduzem o poder para detectar diferenças.</p></article>
      <article className="caution-card"><span><ShieldCheck size={16} /> LIMITES DA INTERPRETAÇÃO</span><ul><li>Associação observada não demonstra efeito causal da academia.</li><li>Os grupos são pequenos e desiguais (n de 5 a 15).</li><li>O índice explosivo usa substitutos físicos e de disputa; não mede diretamente velocidade ou força.</li><li>Os resultados se aplicam aos jogadores selecionados, não a todos os atletas formados.</li></ul></article>
    </section>
    <p className="method-source">Métricas definidas previamente em <code>config/metricas.yaml</code>. Resultados carregados das tabelas processadas do projeto.</p>
  </section>
}

function SourcesPage({ onBack }: { onBack: () => void }) {
  return <section className="sources-page">
    <div className="sources-hero">
      <div className="eyebrow"><i /> TRANSPARÊNCIA · ORIGEM DOS DADOS</div>
      <h1>De onde vêm<br /><em>as informações.</em></h1>
      <p>As bases foram combinadas por identificador do jogador e revisadas para formar a amostra comparativa das quatro academias.</p>
      <button className="back-button" onClick={onBack}><ArrowLeft size={15} /> Voltar ao painel</button>
      <span className="sources-hero-mark"><Database size={25} /></span>
    </div>

    <div className="source-cards">
      <article className="source-card source-featured">
        <div className="source-card-top"><span className="source-icon"><Database size={18} /></span><span className="source-tag">BASE ESTRUTURADA</span></div>
        <h2>Transfermarkt via Kaggle</h2>
        <p>O conjunto <em>player-scores</em> fornece jogadores, posições, partidas, minutos e histórico de transferências. Foi usado para preparar a seleção inicial e a base de aparições.</p>
        <a href="https://www.kaggle.com/datasets/davidcariboo/player-scores" target="_blank" rel="noreferrer">Abrir dataset no Kaggle <ExternalLink size={14} /></a>
        <small>Responsável pela seleção inicial: <code>src/coleta/transfermarkt.py</code></small>
      </article>
      <article className="source-card">
        <div className="source-card-top"><span className="source-icon"><Activity size={18} /></span><span className="source-tag">ESTATÍSTICAS POR TEMPORADA</span></div>
        <h2>Sofascore</h2>
        <p>Estatísticas de passes, dribles e duelos foram coletadas por temporada. Os IDs do Sofascore foram associados ao identificador do Transfermarkt e conferidos em uma tabela manual.</p>
        <a href="https://www.sofascore.com/" target="_blank" rel="noreferrer">Acessar Sofascore <ExternalLink size={14} /></a>
        <small>IDs revisados em <code>data/manual/ids_sofascore.csv</code></small>
      </article>
      <article className="source-card">
        <div className="source-card-top"><span className="source-icon"><Users size={18} /></span><span className="source-tag">CONFERÊNCIA DOS ATLETAS</span></div>
        <h2>Perfis do Transfermarkt</h2>
        <p>Os perfis individuais ajudam a conferir clube, trajetória e histórico. A URL do perfil de cada jogador fica registrada na base validada, junto da justificativa de formação.</p>
        <a href="https://www.transfermarkt.com/" target="_blank" rel="noreferrer">Acessar Transfermarkt <ExternalLink size={14} /></a>
        <small>Revisão registrada em <code>data/manual/jogadores_validos.csv</code></small>
      </article>
      <article className="source-card">
        <div className="source-card-top"><span className="source-icon"><BookOpen size={18} /></span><span className="source-tag">CHECAGEM COMPLEMENTAR</span></div>
        <h2>Wikipédia e fontes citadas</h2>
        <p>Quando necessário, páginas biográficas e outras fontes públicas registradas na coluna de conferência ajudam a checar datas e passagens pela base. A fonte pode variar por atleta.</p>
        <a href="https://www.wikipedia.org/" target="_blank" rel="noreferrer">Acessar Wikipédia <ExternalLink size={14} /></a>
        <small>Consulte a coluna <code>fonte_conferencia</code> na base manual.</small>
      </article>
    </div>

    <section className="source-notes">
      <div><span>COMO OS DADOS SE CONECTAM</span><h2>Uma chave comum, fontes diferentes.</h2><p>O identificador do Transfermarkt é a chave de integração. Estatísticas do Sofascore são associadas a esse ID depois da conferência dos IDs de jogador; nome, sozinho, não é usado como chave.</p></div>
      <div className="source-caveat"><span>NOTA SOBRE FBREF</span><p>O README menciona o FBref como referência para dados básicos. Porém, a extração automatizada atualmente documentada no pipeline usa appearances do dataset Kaggle/Transfermarkt e estatísticas do Sofascore. Por isso, o painel não atribui métricas do resultado ao FBref.</p><a href="https://fbref.com/" target="_blank" rel="noreferrer">Abrir FBref <ExternalLink size={13} /></a></div>
    </section>
    <section className="source-bibliography"><div><span>REFERÊNCIAS DO ESTUDO</span><h2>Leituras que fundamentam o projeto</h2></div><ul><li>Ford, P. R. e Williams, A. M. (2012). <em>The developmental activities engaged in by elite youth soccer players who progressed to professional status compared to those who did not.</em> Psychology of Sport and Exercise, 13(3), 349–352.</li><li>Gledhill, A., Harwood, C. e Forsdyke, D. (2017). <em>Psychosocial factors associated with talent development in football: a systematic review.</em> Psychology of Sport and Exercise, 31, 93–112.</li><li>Satish, K. et al. (2025). <em>Possession football: the playing style that defined FC Barcelona's success and the Spanish national football team's golden generation.</em> Managing Sport and Leisure.</li></ul></section>
    <div className="source-ethics"><ShieldCheck size={16} /><p>As fontes têm termos de uso próprios. O Sofascore é coletado por uma API não oficial, que pode mudar; a coleta deve respeitar os limites e as condições de cada serviço.</p></div>
  </section>
}

const projectSections = [
  {
    id: 'dados', icon: Database, title: 'Dados e configuração', subtitle: 'A fundação: fontes, regras e arquivos do estudo.', color: 'blue',
    items: [
      ['config/', 'Parâmetros centrais do projeto: clubes analisados, caminhos de dados e categorias posicionais.'],
      ['config/metricas.yaml', 'Define os índices técnico e explosivo e os pesos das métricas antes da comparação.'],
      ['config/posicoes.yaml', 'Organiza as posições em grupos comparáveis para o cálculo de percentis.'],
      ['config/settings.py', 'Concentra caminhos, clubes, critérios de seleção e parâmetros usados pelo pipeline.'],
      ['data/raw/', 'Arquivos originais obtidos das fontes. Preservados sem alterações para rastreabilidade.'],
      ['data/raw/players.csv, appearances.csv e transfers.csv', 'Tabelas de atletas, partidas e transferências do conjunto player-scores.'],
      ['data/raw/sofascore/*.json', 'Respostas originais em cache das estatísticas por jogador, temporada e competição.'],
      ['data/manual/', 'Tabelas revisadas pelo grupo: jogadores válidos, IDs do Sofascore e conferência das academias.'],
      ['data/manual/jogadores_validos.csv', 'Seleção revisada de atletas, com clube formador, estreia, minutos e fonte de conferência.'],
      ['data/manual/ids_sofascore.csv', 'Correspondência entre o ID do jogador no projeto e o ID usado pelo Sofascore.'],
      ['data/manual/metodos_academias.csv', 'Registro qualitativo dos métodos das academias e das fontes consultadas.'],
      ['data/interim/ e data/processed/', 'Resultados intermediários e tabelas finais, limpas e prontas para análise.'],
      ['data/interim/candidatos_formados.csv', 'Lista ampla de possíveis jogadores formados, preparada para conferência manual.'],
      ['data/interim/por90_*.csv', 'Métricas convertidas para uma escala comum por 90 minutos.'],
      ['data/processed/jogadores_validos.csv', 'Amostra final validada que alimenta as análises.'],
      ['data/processed/percentis_metricas.csv', 'Percentis por métrica e grupo posicional usados na montagem dos índices.'],
      ['data/processed/indices_jogadores.csv', 'Índices técnico e explosivo, cobertura e dados de cada atleta.'],
      ['data/processed/descritiva_academias.csv', 'Tamanho dos grupos, medianas, quartis e extremos por academia.'],
      ['data/processed/kruskal_wallis.csv e mann_whitney_bonferroni.csv', 'Testes globais e comparações par a par com ajuste de Bonferroni.'],
      ['data/processed/cobertura_metricas.csv', 'Mostra quantos jogadores possuem valor disponível para cada métrica.'],
    ],
  },
  {
    id: 'pipeline', icon: Code2, title: 'Pipeline e tratamento', subtitle: 'O caminho que transforma fontes em indicadores.', color: 'cyan',
    items: [
      ['run_pipeline.py', 'Orquestra as etapas analíticas e grava os resultados processados e gráficos.'],
      ['src/coleta/', 'Módulos de coleta e preparação de jogadores, estatísticas e dados complementares.'],
      ['src/coleta/transfermarkt.py', 'Lê os CSVs do Kaggle e monta candidatos à amostra de jogadores formados.'],
      ['src/coleta/sofascore.py', 'Localiza IDs e coleta estatísticas sazonais, mantendo cópias em cache.'],
      ['src/coleta/uefa_youth.py e bdfutbol.py', 'Módulos de apoio para informações de competições e trajetórias de base.'],
      ['src/tratamento/', 'Integra bases, trata valores ausentes, padroniza por 90 minutos e calcula percentis.'],
      ['src/tratamento/integracao.py e limpeza.py', 'Unificam fontes pela chave do jogador e aplicam regras de qualidade.'],
      ['src/tratamento/por90.py e percentis.py', 'Padronizam as taxas de jogo e posicionam os valores dentro dos grupos.'],
      ['src/features/', 'Constrói índices e características da trajetória dos jogadores.'],
      ['src/features/indices.py, carreira.py e trajetoria.py', 'Calculam os índices e descrevem a carreira e o percurso de formação.'],
      ['src/db.py e sql/01_schema.sql', 'Conectam ao banco e definem as tabelas relacionais do projeto.'],
      ['sql/02_indices.sql e 03_views.sql', 'Consultam índices e organizam visões prontas para análise.'],
      ['sql/04_qualidade_dados.sql', 'Reúne verificações de consistência dos registros no banco.'],
      ['requirements.txt', 'Dependências do pipeline Python para análise, visualização e configuração.'],
    ],
  },
  {
    id: 'analise', icon: FileBarChart, title: 'Análise e resultados', subtitle: 'Como a pergunta de pesquisa vira evidência.', color: 'violet',
    items: [
      ['src/analise/', 'Estatística descritiva, correlação, testes entre academias e tamanho de efeito.'],
      ['src/analise/descritiva.py e correlacao.py', 'Resumem os grupos e investigam relações entre variáveis.'],
      ['src/analise/testes.py e efeito.py', 'Executam testes não paramétricos e calculam o tamanho das diferenças.'],
      ['src/qualitativo/metodos_academias.py', 'Organiza a comparação descritiva dos métodos de formação.'],
      ['src/visual/', 'Gráficos e dashboard para explorar os perfis e comparar os grupos.'],
      ['src/visual/graficos.py e dashboard.py', 'Produzem visualizações e a visão exploratória do estudo.'],
      ['notebooks/01_exploracao.ipynb', 'Caderno para explorar, conferir e compreender os dados.'],
      ['notebooks/02_resultados.ipynb', 'Caderno que apresenta os resultados da análise de forma organizada.'],
      ['data/processed/indices_jogadores.csv', 'Índices técnico e explosivo calculados para cada jogador da amostra.'],
      ['data/processed/kruskal_wallis.csv', 'Resultado do teste global das quatro academias para cada índice.'],
      ['reports/graficos/', 'Visualizações exportadas para consulta e apresentação do projeto.'],
      ['reports/graficos/*.html', 'Dispersões, boxplots, idades de estreia e jogadores revelados em gráficos interativos.'],
    ],
  },
  {
    id: 'qualidade', icon: ShieldCheck, title: 'Qualidade e documentação', subtitle: 'Confiabilidade, repetição e comunicação do trabalho.', color: 'gold',
    items: [
      ['tests/', 'Testes automatizados que protegem cálculos, tratamento e funcionamento do pipeline.'],
      ['tests/test_pipeline.py e test_estatistica.py', 'Conferem a execução do fluxo e os resultados das análises estatísticas.'],
      ['tests/test_por90.py e test_percentis.py', 'Verificam padronização por minutos e cálculo dos percentis.'],
      ['tests/test_indices.py, test_descritiva.py e test_graficos.py', 'Protegem a construção dos índices, resumos e visualizações.'],
      ['tests/test_sofascore.py', 'Confere as rotinas de tratamento e leitura das estatísticas coletadas.'],
      ['README.md', 'Guia do projeto: pergunta, escopo, fontes, metodologia, execução e limitações.'],
      ['frontend/', 'Interface React + TypeScript para explorar indicadores, atletas, metodologia e fontes.'],
      ['frontend/src/App.tsx e App.css', 'Implementam as páginas, interações e apresentação visual do dashboard.'],
      ['frontend/package.json', 'Declara os pacotes e comandos para desenvolvimento, verificação e build.'],
      ['.gitignore', 'Evita versionar ambientes, caches e dados brutos que não devem ir ao repositório.'],
    ],
  },
]

function ProjectPage({ onBack }: { onBack: () => void }) {
  const [expanded, setExpanded] = useState('dados')
  const [activeStep, setActiveStep] = useState(0)
  const steps = [
    { number: '01', title: 'Selecionar', description: '35 jogadores validados em quatro academias.', section: 'dados', files: [['data/manual/jogadores_validos.csv', 'A lista revisada de atletas que atende aos critérios do estudo.'], ['src/coleta/transfermarkt.py', 'Gera os candidatos iniciais a partir de jogadores, aparições e transferências.'], ['config/settings.py', 'Registra os clubes e os critérios de estreia e minutos usados na seleção.']] },
    { number: '02', title: 'Integrar', description: 'Conectar fontes por identificador do jogador.', section: 'pipeline', files: [['data/manual/ids_sofascore.csv', 'Relaciona os IDs do projeto aos IDs encontrados no Sofascore.'], ['src/tratamento/integracao.py', 'Combina as bases usando o identificador do jogador, não apenas o nome.'], ['data/raw/players.csv e transfers.csv', 'Complementam a seleção com perfil e histórico de transferências.']] },
    { number: '03', title: 'Padronizar', description: 'Comparar métricas por 90 minutos e posição.', section: 'pipeline', files: [['src/tratamento/por90.py', 'Coloca estatísticas de jogo na escala comum por 90 minutos.'], ['src/tratamento/percentis.py', 'Calcula percentis comparáveis dentro das categorias posicionais.'], ['config/metricas.yaml e posicoes.yaml', 'Definem métricas dos índices e agrupamentos de posição.']] },
    { number: '04', title: 'Analisar', description: 'Índices, estatística descritiva e testes.', section: 'analise', files: [['src/features/indices.py', 'Monta os índices técnico e explosivo a partir dos percentis.'], ['src/analise/descritiva.py e testes.py', 'Resume os grupos e testa diferenças entre academias.'], ['data/processed/kruskal_wallis.csv', 'Guarda o resultado do teste global para os dois índices.']] },
    { number: '05', title: 'Comunicar', description: 'Dashboard, gráficos e documentação.', section: 'qualidade', files: [['frontend/src/App.tsx e App.css', 'Apresentam o dashboard e as páginas interativas do projeto.'], ['reports/graficos/', 'Reúne gráficos exportados para explorar e apresentar os resultados.'], ['README.md e notebooks/', 'Documentam a execução e comunicam o processo e os resultados.']] },
  ] as const

  function selectStep(index: number) {
    setActiveStep(index)
    setExpanded(steps[index].section)
  }

  return <section className="project-page">
    <div className="project-hero">
      <div className="eyebrow"><i /> PROJETO INTEGRADOR · CIÊNCIA DE DADOS</div>
      <h1>Do dado ao campo:<br /><em>um projeto por dentro.</em></h1>
      <p>Uma visita guiada pelo estudo que compara os perfis de jogadores formados em quatro academias europeias.</p>
      <button className="back-button" onClick={onBack}><ArrowLeft size={15} /> Voltar ao painel</button>
      <span className="project-hero-mark"><Code2 size={26} /></span>
    </div>

    <section className="project-question">
      <span>A PERGUNTA QUE GUIA O TRABALHO</span>
      <h2>A academia de formação ajuda a explicar o perfil técnico e explosivo dos jogadores que revela?</h2>
      <p>Comparamos Barcelona, Real Madrid, Manchester City e Liverpool. A resposta é tratada como associação estatística, nunca como prova de causa e efeito.</p>
    </section>

    <section className="project-journey">
      <div className="project-section-head"><span>O PROJETO EM 5 ETAPAS</span><p>Clique em uma etapa para ver o foco de cada parte.</p></div>
      <div className="journey-track">{steps.map((step, index) => <button key={step.number} className={activeStep === index ? 'journey-step active' : 'journey-step'} onClick={() => selectStep(index)} aria-pressed={activeStep === index}><span>{step.number}</span><strong>{step.title}</strong></button>)}</div>
      <div className="journey-detail"><span>{steps[activeStep].number}</span><p><strong>{steps[activeStep].title}:</strong> {steps[activeStep].description}</p><ArrowDown size={16} /></div>
      <div className="journey-files" key={steps[activeStep].number}><div className="journey-files-heading"><span>ARQUIVOS DESTA ETAPA</span><small>{steps[activeStep].files.length} arquivos em foco</small></div><div className="journey-file-list">{steps[activeStep].files.map(([path, description]) => <article className="journey-file" key={path}><FileCode2 size={15} /><code>{path}</code><p>{description}</p></article>)}</div></div>
    </section>

    <section className="project-map">
      <div className="project-section-head"><span>MAPA DO REPOSITÓRIO</span><p>Abra cada módulo para descobrir o papel de suas pastas e arquivos.</p></div>
      <div className="project-accordion">{projectSections.map((section) => {
        const Icon = section.icon
        const isOpen = expanded === section.id
        return <article className={`project-module ${section.color} ${isOpen ? 'open' : ''}`} key={section.id}>
          <button className="module-trigger" onClick={() => setExpanded(isOpen ? '' : section.id)} aria-expanded={isOpen}>
            <span className="module-icon"><Icon size={18} /></span><span className="module-title"><strong>{section.title}</strong><small>{section.subtitle}</small></span><span className="module-count">{section.items.length} ITENS</span><ChevronDown size={16} className="module-chevron" />
          </button>
          {isOpen && <div className="module-content">{section.items.map(([path, description]) => <div className="file-explainer" key={path}><span className="file-icon"><FileCode2 size={14} /></span><code>{path}</code><p>{description}</p></div>)}</div>}
        </article>
      })}</div>
    </section>

    <section className="project-finale"><div><span>O QUE FICA DO ESTUDO</span><h2>Um retrato consistente, com limites à vista.</h2><p>Os resultados não mostraram diferença estatisticamente significativa nos índices nesta amostra. O processo documentado permite revisar as fontes, reproduzir os cálculos e expandir o estudo em trabalhos futuros.</p></div><div className="project-team"><span>GRUPO DE PESQUISA</span><strong>Arthur Martins</strong><strong>Guilherme Onorio</strong><strong>Octavio Teodoro</strong><strong>Peterson Carara</strong><small>Orientação: Prof. Pazetti</small></div></section>
  </section>
}

function App() {
  const [metric, setMetric] = useState<'indice_tecnico' | 'indice_explosivo'>('indice_tecnico')
  const [academy, setAcademy] = useState('Todas as academias')
  const [query, setQuery] = useState('')
  const [view, setView] = useState<'overview' | 'players' | 'methodology' | 'sources' | 'project'>('overview')
  const filtered = useMemo(() => players.filter((player) => academy === 'Todas as academias' || player.clube === academy)
    .filter((player) => player.nome.toLocaleLowerCase('pt-BR').includes(query.trim().toLocaleLowerCase('pt-BR')))
    .sort((a, b) => b[metric] - a[metric]), [academy, metric, query])
  const chartData = summaries.filter((row) => row.metrica === metric && (academy === 'Todas as academias' || row.academia === academy))
  const scopedPlayers = players.filter((player) => academy === 'Todas as academias' || player.clube === academy)
  const groups = Object.keys(colors).filter((name) => academy === 'Todas as academias' || name === academy).map((name) => ({
    name, data: players.filter((player) => player.clube === name).map((player) => ({ x: player.indice_tecnico, y: player.indice_explosivo, nome: player.nome })),
  }))
  const pValue = tests.find((row) => row.metrica === metric)?.p_value ?? 0
  const sortedScores = scopedPlayers.map((player) => player[metric]).sort((a, b) => a - b)
  const middle = Math.floor(sortedScores.length / 2)
  const median = sortedScores.length ? sortedScores.length % 2 ? sortedScores[middle] : (sortedScores[middle - 1] + sortedScores[middle]) / 2 : 0

  function exportCsv() {
    const data = Papa.unparse(filtered.map(({ nome, clube, categoria, indice_tecnico, indice_explosivo, minutos }) => ({ nome, academia: clube, posicao: categoria, indice_tecnico, indice_explosivo, minutos })))
    const url = URL.createObjectURL(new Blob([data], { type: 'text/csv;charset=utf-8;' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'jogadores-academias.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="#inicio" aria-label="Formação em campo"><span className="brand-mark"><Activity size={19} /></span><span className="brand-name">FORMAÇÃO<span>EM CAMPO</span></span></a>
      <div className="sidebar-label">ANÁLISE</div>
      <nav className="side-nav" aria-label="Navegação">
        <button className={view === 'overview' ? 'nav-item active' : 'nav-item'} onClick={() => setView('overview')}><LayoutDashboard size={17} /> Visão geral</button>
        <button className={view === 'players' ? 'nav-item active' : 'nav-item'} onClick={() => setView('players')}><Users size={17} /> Jogadores <span className="nav-count">{filtered.length}</span></button>
      </nav>
      <div className="sidebar-label academies-label">ACADEMIAS</div>
      <div className="academy-list">{Object.keys(colors).map((name) => <button key={name} className={academy === name ? 'academy-link selected' : 'academy-link'} onClick={() => setAcademy(academy === name ? 'Todas as academias' : name)} title={name} aria-label={`Filtrar por ${name}`} aria-pressed={academy === name}><span className="academy-logo-wrap"><img className="academy-logo" src={`/logos/${academyLogos[name]}`} alt="" /></span><span>{name}</span><small>{players.filter((player) => player.clube === name).length}</small></button>)}</div>
      <div className="sidebar-bottom"><button className="season-chip" onClick={() => setView('sources')} title="Ver fontes da pesquisa" aria-label="Ver fontes da pesquisa"><Database size={14} /> <span>FONTES DA PESQUISA</span><ArrowUpRight size={13} /></button><div className="project-credit"><GraduationCap size={16} /><span>Projeto Integrador<br /><strong>Ciência de Dados · FATEC</strong></span></div></div>
    </aside>

    <main className="main-content" id="inicio">
      <header className="topbar"><div className="breadcrumb">ESTUDO COMPARATIVO <span>/</span> <strong>{view === 'overview' ? 'PAINEL DE DESEMPENHO' : view === 'players' ? 'ATLETAS FORMADOS' : view === 'methodology' ? 'METODOLOGIA E CONCLUSÕES' : view === 'sources' ? 'FONTES DA PESQUISA' : 'SOBRE O PROJETO'}</strong></div><div className="topbar-actions"><small>DADOS PROCESSADOS</small><button onClick={() => setView(view === 'methodology' ? 'overview' : 'methodology')} title={view === 'methodology' ? 'Voltar ao painel' : 'Metodologia e conclusões'} aria-label={view === 'methodology' ? 'Voltar ao painel' : 'Metodologia e conclusões'}>{view === 'methodology' ? <ArrowLeft size={17} /> : <CircleHelp size={17} />}</button><div className="team-tooltip"><button className="avatar" onClick={() => setView('project')} title="Sobre o projeto" aria-label="Sobre o projeto e a equipe">PI</button><div className="team-tooltip-card"><strong>Projeto Integrador</strong><span>Arthur Martins</span><span>Guilherme Onorio</span><span>Octavio Teodoro</span><span>Peterson Carara</span><span className="team-tooltip-role">Orientação: Prof. Pazetti</span></div></div></div></header>
      <div className="page-wrap">
        <section className={view === 'overview' || view === 'players' ? 'page-heading' : 'page-heading hidden'}><div><div className="eyebrow"><i /> FUTEBOL · DESENVOLVIMENTO DE TALENTOS</div><h1>{view === 'overview' ? <>O que forma<br /><em>um jogador?</em></> : <>Talentos<br /><em>revelados.</em></>}</h1><p className="intro">Uma leitura comparativa dos atletas revelados por quatro das principais academias europeias.</p></div><aside className="heading-aside"><div>ESTUDO <span>01 / 04</span></div><i /><p>Associação observada.<br /><strong>Causalidade não inferida.</strong></p></aside></section>

        <section className={view === 'overview' || view === 'players' ? 'control-row' : 'control-row hidden'}><div className="view-toggle" role="group" aria-label="Índice"><button className={metric === 'indice_tecnico' ? 'toggle-option selected' : 'toggle-option'} onClick={() => setMetric('indice_tecnico')}><b>T</b> Técnico</button><button className={metric === 'indice_explosivo' ? 'toggle-option selected' : 'toggle-option'} onClick={() => setMetric('indice_explosivo')}><b>E</b> Explosivo</button></div><div className="filter-group"><span><Filter size={13} /> FILTROS</span><label className="select-wrap"><span className="sr-only">Filtrar por academia</span><select value={academy} onChange={(event) => setAcademy(event.target.value)}><option>Todas as academias</option>{Object.keys(colors).map((name) => <option key={name}>{name}</option>)}</select><ChevronDown size={14} /></label><button className="export-button" onClick={exportCsv} title="Exportar jogadores"><Download size={15} /><span>Exportar</span></button></div></section>

        {view === 'project' ? <ProjectPage onBack={() => setView('overview')} /> : view === 'sources' ? <SourcesPage onBack={() => setView('overview')} /> : view === 'methodology' ? <MethodologyPage onBack={() => setView('overview')} /> : view === 'overview' ? <>
          <section className="stats-grid"><article className="stat-block"><div className="stat-top">ATLETAS NA AMOSTRA <Users size={16} /></div><div className="stat-value">{scopedPlayers.length}<span> atletas</span></div><div className="stat-foot">{academy === 'Todas as academias' ? 'Quatro academias observadas' : academy}</div></article><article className="stat-block"><div className="stat-top">MEDIANA DO ÍNDICE <Activity size={15} /></div><div className="stat-value">{number(median)}<span> / 100</span></div><div className="stat-foot">Perfil {metric === 'indice_tecnico' ? 'técnico' : 'explosivo'}</div></article><article className="stat-block"><div className="stat-top">MINUTOS ANALISADOS <GraduationCap size={16} /></div><div className="stat-value">{number(scopedPlayers.reduce((sum, player) => sum + (player.minutos || 0), 0) / 1000, 0)}<span> mil</span></div><div className="stat-foot">Equipes principais</div></article><article className="stat-block"><div className="stat-top">KRUSKAL–WALLIS <ShieldCheck size={16} /></div><div className="stat-value">p = {number(pValue, 3)}</div><div className="stat-foot"><span className="status-pill">Sem diferença significativa</span></div></article></section>
          <section className="analysis-grid">
            <article className="panel"><div className="panel-heading"><div><small>COMPARAÇÃO ENTRE GRUPOS</small><h2>Índice por academia</h2></div><span className="unit-label">MEDIANA · 0—100</span></div><div className="chart-legend">{Object.entries(colors).map(([name, color]) => <span key={name}><i style={{ backgroundColor: color }} />{labels[name]}</span>)}</div><div className="median-chart"><ResponsiveContainer width="100%" height="100%"><ComposedChart data={chartData} margin={{ top: 10, right: 12, bottom: 1, left: -20 }}><CartesianGrid vertical={false} stroke="#e9e9e2" strokeDasharray="3 5" /><XAxis dataKey="academia" axisLine={false} tickLine={false} tick={{ fill: '#777d75', fontSize: 11 }} tickFormatter={(value: string) => labels[value] ?? value} dy={9} /><YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} axisLine={false} tickLine={false} tick={{ fill: '#969b94', fontSize: 10 }} /><Tooltip content={({ active, payload }) => active && payload?.length ? <div className="chart-tooltip"><strong>{labels[String(payload[0].payload.academia)]}</strong><span>Mediana <b>{number(Number(payload[0].value))}</b></span><span>Atletas <b>{payload[0].payload.n}</b></span></div> : null} /><Scatter dataKey="mediana" r={7}>{chartData.map((entry) => <Cell key={entry.academia} fill={colors[entry.academia]} stroke="#fff" strokeWidth={2} />)}</Scatter></ComposedChart></ResponsiveContainer></div><div className="panel-footnote">ⓘ Amostras pequenas; leia as medianas junto aos quartis e ao valor-p.</div></article>
            <article className="panel"><div className="panel-heading"><div><small>PERFIL DOS JOGADORES</small><h2>Técnica × explosividade</h2></div><span className="unit-label">{filtered.length} atletas</span></div><div className="scatter-chart"><ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{ top: 13, right: 16, bottom: 5, left: -14 }}><CartesianGrid stroke="#e9e9e2" strokeDasharray="3 5" /><XAxis type="number" dataKey="x" domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} axisLine={false} tickLine={false} tick={{ fill: '#929890', fontSize: 10 }} /><YAxis type="number" dataKey="y" domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} axisLine={false} tickLine={false} tick={{ fill: '#929890', fontSize: 10 }} /><Tooltip content={({ active, payload }) => active && payload?.length ? <div className="chart-tooltip"><strong>{payload[0].payload.nome}</strong><span>Técnico <b>{number(payload[0].payload.x)}</b></span><span>Explosivo <b>{number(payload[0].payload.y)}</b></span></div> : null} />{groups.map((group) => <Scatter key={group.name} name={group.name} data={group.data} fill={colors[group.name]} fillOpacity={0.8} />)}</ScatterChart></ResponsiveContainer></div><div className="axis-caption"><span>ÍNDICE TÉCNICO</span><span>ÍNDICE EXPLOSIVO ↑</span></div></article>
          </section>
          <section className="bottom-grid"><article className="panel ranking-panel"><div className="panel-heading"><div><small>DESTAQUES DA AMOSTRA</small><h2>Maiores índices</h2></div><button className="text-action" onClick={() => setView('players')}>Ver todos <ArrowUpRight size={14} /></button></div>{filtered.slice(0, 4).map((player, index) => <div className="ranking-row" key={player.nome}><span className="rank-number">0{index + 1}</span><span className="rank-name">{player.nome}<small>{player.categoria.replaceAll('_', ' ')}</small></span><span className="rank-club"><i style={{ backgroundColor: colors[player.clube] }} />{labels[player.clube]}</span><strong>{number(player[metric])}</strong></div>)}</article><article className="method-note"><div className="method-top"><CircleHelp size={17} /> LEITURA DO ESTUDO</div><h3>Um retrato, não uma sentença.</h3><p>Os resultados comparam os jogadores observados. Não demonstram que a academia causou o desempenho.</p><div className="method-result">Teste global sem significância<br /><strong>p &gt; 0,05 nos dois perfis</strong></div></article></section>
        </> : <section className="panel players-panel"><div className="panel-heading players-heading"><div><small>AMOSTRA VALIDADA</small><h2>Jogadores formados</h2><p>{filtered.length} atletas · ordenados pelo índice {metric === 'indice_tecnico' ? 'técnico' : 'explosivo'}</p></div><label className="search-box"><Search size={16} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar jogador" /></label></div><div className="table-wrap"><table><thead><tr><th>JOGADOR</th><th>ACADEMIA</th><th>POSIÇÃO</th><th>ÍNDICE TÉCNICO</th><th>ÍNDICE EXPLOSIVO</th><th>MINUTOS</th><th /></tr></thead><tbody>{filtered.map((player) => <tr key={player.nome}><td><strong>{player.nome}</strong></td><td><span className="table-club"><i style={{ backgroundColor: colors[player.clube] }} />{player.clube}</span></td><td>{player.categoria.replaceAll('_', ' ')}</td><td>{number(player.indice_tecnico)}</td><td>{number(player.indice_explosivo)}</td><td>{number(player.minutos, 0)}</td><td><a href={player.url} target="_blank" rel="noreferrer" aria-label={`Perfil de ${player.nome}`}><ArrowUpRight size={15} /></a></td></tr>)}</tbody></table>{!filtered.length && <div className="empty-state">Nenhum jogador encontrado.</div>}</div></section>}
        <footer className="page-footer"><span>FONTE: BASE CONSOLIDADA DO ESTUDO · 2026</span><span>ANÁLISE DESCRITIVA E NÃO PARAMÉTRICA</span></footer>
      </div>
    </main>
  </div>
}

export default App
