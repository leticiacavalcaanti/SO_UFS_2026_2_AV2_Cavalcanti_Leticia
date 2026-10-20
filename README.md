# SO_UFS_2026_2_AV2_Cavalcanti_Leticia

Atividade 2 (AV2) — Sistemas Operacionais — **Memória, armazenamento, sincronização e desempenho de aplicações de IA generativa (GenResearch-Servidor)**
Modalidade individual | Discente: **Leticia Cavalcanti** | 2026.2

## Entregáveis
| Item | Onde |
|---|---|
| Relatório técnico (PDF) | [report/relatorio.pdf](report/relatorio.pdf) (fonte: [report/relatorio.md](report/relatorio.md)) |
| Apresentação (PDF) | [report/apresentacao.pdf](report/apresentacao.pdf) |
| Vídeo | [https://drive.google.com/file/d/1ZTenxEhflYIi4mIGWAJvMkZqFxuyeKsG/view?usp=sharing](https://drive.google.com/file/d/1ZTenxEhflYIi4mIGWAJvMkZqFxuyeKsG/view?usp=sharing) (também em [VIDEO.md](VIDEO.md)) |
| Código | [genresearch/](genresearch/) (serviço) e [scripts/](scripts/) (experimentos) |
| Resultados brutos, logs, gráficos | [results/](results/) |
| Declaração de uso de IA | [declaracao_uso_ia.md](declaracao_uso_ia.md) |

## O que é o GenResearch-Servidor
Serviço RAG simplificado, independente de qualquer API externa (sem chaves, sem pesos de modelo):

```
produtores (2) ──put──▶ BoundedBuffer (empty/full/mutex) ──get──▶ trabalhadores (1/2/4/8 threads)
                                                                      │
   consulta ─▶ cache compartilhado (LRU/FIFO + mutex) ──miss──▶ embedding ─▶ varredura do índice (.npy; read ou mmap)
                                                                      ─▶ textos no SQLite ─▶ contexto limitado ─▶ geração simulada ─▶ cache
                                         logs de eventos (SafeLogger, mutex) ─ métricas /proc, getrusage e cgroup
```
- **Ingestão** (`genresearch/store.py`): lê `.txt`, fragmenta por palavras com sobreposição (ideia do `ChunkingService` do projeto glpimentor_servicoia, de autoria própria), gera **vetores simulados** (hashing trick, normalizados) e grava `vectors.npy` + `meta.sqlite`.
- **Recuperação**: top-k por produto escalar, varrendo o índice em blocos (funciona igual para índice lido na RAM ou mapeado com `mmap`).
- **Geração**: **simulada** (latência configurável + CPU por SHA-256 proporcional ao contexto). Escolha deliberada: o foco é o SO, não a qualidade do texto; não usa chave de API.
- **Sincronização**: `genresearch/sync.py` (semáforos `empty`/`full` + mutex), `cache.py` (mutex), `logger.py` (mutex).
- **Trabalhadores = threads**, porque a carga é mista (E/S simulada em `sleep`, numpy e hashlib liberam o GIL); processos custariam cópia do índice e IPC.

## Ambiente
Linux em **contêiner Docker** (Debian 13, kernel 6.6.87 WSL2) sobre Windows 11; CPU i5-10210U (4 CPUs lógicas), 5,8 GiB de RAM, 1 GiB de swap, sem GPU. Detalhes completos em [results/env/ambiente_container.txt](results/env/ambiente_container.txt). Python 3.12, numpy 2.1.3, matplotlib 3.9.2.

## Como reproduzir
Pré-requisitos: Docker (Linux, macOS ou Windows com Docker Desktop) e Python 3 no hospedeiro.

```bash
docker build -t genresearch .                 # imagem com python, numpy, procps, sysstat, strace
python scripts/run_all.py                     # TODOS os experimentos (≈ 1 h); resultados em results/
python scripts/run_all.py c1c2 c6             # ou apenas alguns: env c1c2 c3c4 c5scale c5limit c6 sync evidence
docker run --rm -v "$PWD:/work" -v genres_data:/workdata -w /work/scripts genresearch python analyze.py   # gráficos e tabelas
```
Variáveis: `REPS` (repetições, padrão 3), `N_REQ` (requisições por execução, padrão 400), `C12_SIZES` (tamanhos de arquivo em MB do C1/C2).
Os dados são **sintéticos e determinísticos** (semente fixa): `genresearch/corpus.py` gera corpus e consultas; nada é baixado. Corpus e índices ficam no volume Docker `genres_data` (não versionados).

## Mapa dos experimentos
| Config. | Script | Saída bruta |
|---|---|---|
| Parte A (ambiente) | `scripts/env_capture.sh` | `results/env/` |
| C1 leitura convencional / C2 mmap / Parte E | `scripts/c1_c2_read_mmap.py` | `results/c1_c2_read_mmap.csv` |
| C3 concorrência e fila | `scripts/c3_c4_pipeline.py c3` | `results/c3_concurrency.csv`, `results/logs/` |
| C3b (teste OpenBLAS) | `OPENBLAS_NUM_THREADS=1 C3_QCAPS=64 C3_OUT=c3_openblas1.csv python scripts/c3_c4_pipeline.py c3` (no contêiner) | `results/c3_openblas1.csv` |
| C4 cache compartilhado | `scripts/c3_c4_pipeline.py c4` | `results/c4_cache.csv` |
| C5 pressão de memória | `scripts/c5_pressure.py` (`scale`, `limit`) | `results/c5_scale.csv`, `results/c5_limit/`, `results/c5_limit_summary.csv` |
| C6 falhas controladas | `scripts/c6_failures.py` (+ OOM do C5) | `results/c6_failures.csv` |
| Parte D sincronização | `scripts/sync_demo.py` | `results/d1…d4_*.csv` |
| Evidências SO (ps, threads, strace, vmstat, iostat) | `scripts/evidence.sh` | `results/evidence/` |

## Limitações conhecidas
Os experimentos rodam em contêiner sobre WSL2 (o cache de páginas e o disco são os da VM, não do Windows); a geração é simulada; vetores são simulados. Ver seção de limitações do relatório.

## Licença e observações
Sem chaves, tokens, `.env`, dados pessoais ou pesos de modelo (ver `.gitignore`). Código autoral; uso de IA generativa na elaboração declarado em [declaracao_uso_ia.md](declaracao_uso_ia.md).

