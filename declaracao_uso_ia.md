# Declaração de Uso de IA Generativa — AV2

## Ferramenta e modelo utilizados
Claude Code (Anthropic), modelo Claude Sonnet 5.5, via extensão integrada ao editor (VS Code).

## Divisão de trabalho
- **Execução assistida por IA:** a ferramenta escreveu a maior parte do código (`genresearch/` e `scripts/`), executou os experimentos no Docker, gerou gráficos e tabelas e redigiu o rascunho do relatório, dos slides, do roteiro do vídeo e desta declaração, a partir das minhas instruções e dos arquivos que forneci.
- **Direção e decisões da discente:** defini o escopo, tomei as decisões listadas abaixo, forneci o enunciado, o modelo de relatório e o projeto de referência, gravei o vídeo e fiz os commits e a publicação no GitHub.

## Decisões da discente
1. Usar o Docker Desktop como ambiente Linux (contêiner).
2. Usar o projeto **glpimentor** apenas como referência de ideia (RAG: *chunking* e similaridade de cosseno) e construir um sistema **separado e independente**, sem a chave de API da OpenAI nem pgvector.
3. Ser informada da alternativa de usar um modelo real (Ollama) e **manter a geração e os embeddings simulados**, que o enunciado admite (Parte B).
4. Confirmar o padrão de nome do repositório (o mesmo da AV1, com `AV2`).
5. Fornecer o modelo de relatório do docente (Word) e pedir que o relatório fosse reescrito nesse modelo, com autoria individual.
6. Definir o que vai no repositório (em `report/`: apenas `docx`, `pdf` e `pptx`) e o que fica de fora (roteiro e material de estudo).
7. Hospedar o vídeo no Google Drive.

## Prompts relevantes (mensagens enviadas à ferramenta, no original)
1. "preciso fazer esse trabalho hoje, pode me ajudar?" (com o enunciado da AV2 anexado)
2. "olhe o projeto glpimentor, tem algo parecido pronto, tem rag mas a ia utilizada é um modelo openai via chave de api"
3. "mas eu vou fazer um sistema a parte, q recebe documentos e processa eles e depois responde perguntas recuperando os documentos vetorizados, faz sentido assim?"
4. "mas a ideia do trabalho nao seria rodar um modelo? [...]" (questionei a escolha de simular e, após a explicação, decidi manter simulado)
5. "deixei um exemplo em .docx de como fazia os relatorios para esse mesmo professor, vamos ter q ajustar e deixar no mesmo modelo mas so comigo sendo a estudante"
6. "ao final gere possiveis perguntas relacionada ao trabalho, e também ao trabalho junto com os assuntos da disciplina ate agr" (com os slides e textos da disciplina anexados)
7. "me explique o que o sistema faz de ponta a ponta, se tem teste com interface, quais as configurações"

## Sugestões aproveitadas, corrigidas ou rejeitadas
- **Aproveitado:** Docker como ambiente Linux; vetores e geração simulados; threads como trabalhadores; medição via `/proc`, `getrusage` e cgroup v2.
- **Rejeitado:** reutilizar o serviço glpimentor (depende de chave OpenAI e de pgvector).
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
Todos os números do relatório vêm de `results/*.csv`, `results/c5_limit/*.jsonl` e `results/evidence/`, gerados pelas execuções reais; o texto separa o que foi medido do que é interpretação; hipóteses testadas parcialmente (OpenBLAS) e limitações estão declaradas na seção de limitações do relatório.

## Revisão pela discente
**PREENCHER com o que for verdadeiro:** o que você leu, executou, conferiu ou alterou por conta própria (por exemplo: reexecutou algum passo de `run_all.py`, conferiu tabelas contra os CSV, reescreveu trechos do relatório com suas palavras) e quais pontos consegue explicar na apresentação.
