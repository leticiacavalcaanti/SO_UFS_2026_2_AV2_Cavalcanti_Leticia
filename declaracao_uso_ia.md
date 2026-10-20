# Declaração de Uso de IA Generativa — AV2

## Ferramenta e modelo utilizados
Claude Code (Anthropic), modelo Claude Sonnet 5.5, via extensão integrada ao editor (VS Code).

## Finalidade de cada uso
1. Estruturar o repositório e redigir o código do serviço (`genresearch/`) e dos scripts de experimento (`scripts/`).
2. Executar os experimentos no contêiner Docker e coletar os resultados brutos (CSV, logs, evidências do SO).
3. Redigir os scripts de análise/gráficos, o relatório, os slides, o roteiro do vídeo e esta declaração.
4. Explicar conceitos (cache de páginas, `mmap`, cgroups, deadlock) usados na interpretação.

## Prompts relevantes
1. "preciso fazer esse trabalho hoje, pode me ajudar?" (com o enunciado da AV2 anexado)
2. "olhe o projeto glpimentor, tem algo parecido pronto, tem rag mas a ia utilizada é um modelo openai via chave de api" (para reaproveitar a ideia de *chunking*/cosseno **sem** a chave de API)
3. "mas eu vou fazer um sistema a parte, q recebe documentos e processa eles e depois responde perguntas recuperando os documentos vetorizados, faz sentido assim?"

## Sugestões aproveitadas, corrigidas ou rejeitadas
- **Aproveitado:** usar Docker como ambiente Linux; vetores e geração simulados (sem chave, sem pesos); threads como trabalhadores; medição via `/proc`, `getrusage` e cgroup v2.
- **Rejeitado:** reutilizar o serviço glpimentor (depende de chave OpenAI e de pgvector) — o repositório é independente.
- **Corrigido após revisão crítica dos resultados** (ver "Erros encontrados").

## Erros encontrados (e corrigidos)
- **C5, limite de memória:** a 1ª versão mostrou o `mmap` "sobrevivendo" a 384 MB com 0 faltas maiores e RSS de 1 GB — as páginas já estavam no cache da VM (cobradas a outro cgroup), logo não havia pressão. Corrigido despejando o cache de páginas do arquivo (`posix_fadvise`) no início de cada execução; o resultado passou a mostrar *thrashing* real (≈ 125 mil faltas maiores).
- **C5, escala:** RSS era do processo inteiro, contaminado pela construção do índice e pelas configurações anteriores (por isso `read` e `mmap` saíam idênticos). Corrigido executando cada configuração em um subprocesso novo.
- **C6:** retentativas de requisições que acabavam em erro não eram contadas (0 em vez de 2 por requisição). Corrigido.
- **D1:** o contador de "computações duplicadas" também sofria a corrida e saía negativo. Corrigido com um contador atômico independente (`itertools.count`).
- **D4:** o modo "ordenado" do deadlock travava numa barreira e o modo "timeout" estava confuso; ambos reescritos.
- Faltas de página **menores** no C5a tiveram um pico não monotônico que não foi explicado; por isso não foram interpretadas no relatório.
- Problemas de ambiente: conversão automática de caminhos pelo Git Bash (`MSYS_NO_PATHCONV`) e *here-strings* no PowerShell.

## Como as afirmações foram verificadas
Todos os números do relatório vêm de `results/*.csv`, `results/c5_limit/*.jsonl` e `results/evidence/` gerados pelas execuções reais; o texto separa o que foi medido do que é interpretação; hipóteses testadas parcialmente (OpenBLAS) e limitações estão declaradas na §13 do relatório.

## Revisão pela discente
**PREENCHER:** o que você leu, executou e alterou por conta própria (por exemplo: reexecutou `run_all.py`, conferiu as tabelas contra os CSV, ajustou o texto) e que pontos consegue explicar na apresentação.
