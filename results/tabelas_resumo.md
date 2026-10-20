# Tabelas-resumo (geradas por scripts/analyze.py)


## C1/C2 — leitura convencional x mmap (médias de 3 repetições)

| MB | método | padrão | cache | abertura (ms) | leitura (ms) | ΔRSS (MB) | ΔVSZ (MB) | falhas maiores | falhas menores | lido do disco (MB) |
|---|---|---|---|---|---|---|---|---|---|---|
| 16 | mmap | rand | cold | 0.025 | 102.9 | 16 | 16 | 268 | 133 | 16 |
| 16 | mmap | rand | warm | 0.026 | 6.5 | 16 | 16 | 0 | 256 | 0 |
| 16 | mmap | seq | cold | 0.021 | 29.9 | 16 | 16 | 129 | 203 | 16 |
| 16 | mmap | seq | warm | 0.020 | 7.5 | 16 | 16 | 0 | 256 | 0 |
| 16 | read_all | seq | cold | 0.005 | 27.3 | 16 | 16 | 0 | 4001 | 16 |
| 16 | read_all | seq | warm | 0.009 | 11.3 | 5 | 5 | 0 | 1365 | 0 |
| 16 | read_stream | rand | cold | 0.004 | 328.7 | 0 | 0 | 0 | 0 | 15 |
| 16 | read_stream | rand | warm | 0.005 | 8.6 | 0 | 0 | 0 | 0 | 0 |
| 16 | read_stream | seq | cold | 0.005 | 21.1 | 0 | 0 | 0 | 175 | 16 |
| 16 | read_stream | seq | warm | 0.006 | 8.8 | 0 | 0 | 0 | 160 | 0 |
| 128 | mmap | rand | cold | 0.038 | 619.2 | 94 | 128 | 1205 | 612 | 116 |
| 128 | mmap | rand | warm | 0.033 | 10.7 | 95 | 128 | 0 | 1618 | 0 |
| 128 | mmap | seq | cold | 0.026 | 298.3 | 128 | 128 | 1025 | 1024 | 128 |
| 128 | mmap | seq | warm | 0.047 | 63.1 | 128 | 128 | 0 | 2048 | 0 |
| 128 | read_all | seq | cold | 0.005 | 243.5 | 128 | 128 | 0 | 32769 | 128 |
| 128 | read_all | seq | warm | 0.013 | 130.6 | 128 | 128 | 0 | 32769 | 0 |
| 128 | read_stream | rand | cold | 0.008 | 660.1 | 0 | 0 | 0 | 0 | 23 |
| 128 | read_stream | rand | warm | 0.007 | 10.2 | 0 | 0 | 0 | 0 | 0 |
| 128 | read_stream | seq | cold | 0.005 | 153.1 | 0 | 0 | 0 | 0 | 128 |
| 128 | read_stream | seq | warm | 0.006 | 55.5 | 0 | 0 | 0 | 0 | 0 |
| 768 | mmap | rand | cold | 0.036 | 1409.5 | 165 | 768 | 2441 | 421 | 287 |
| 768 | mmap | rand | warm | 0.029 | 17.6 | 165 | 768 | 0 | 2812 | 0 |
| 768 | mmap | seq | cold | 0.021 | 1063.8 | 768 | 768 | 6146 | 6144 | 768 |
| 768 | mmap | seq | warm | 0.024 | 322.4 | 768 | 768 | 0 | 12288 | 0 |
| 768 | read_all | seq | cold | 0.005 | 1368.7 | 768 | 768 | 0 | 196609 | 768 |
| 768 | read_all | seq | warm | 0.012 | 660.9 | 768 | 768 | 0 | 196609 | 0 |
| 768 | read_stream | rand | cold | 0.005 | 636.7 | 0 | 0 | 0 | 0 | 23 |
| 768 | read_stream | rand | warm | 0.007 | 12.8 | 0 | 0 | 0 | 0 | 0 |
| 768 | read_stream | seq | cold | 0.005 | 754.7 | 0 | 0 | 0 | 0 | 768 |
| 768 | read_stream | seq | warm | 0.005 | 331.4 | 0 | 0 | 0 | 0 | 0 |

## C3 — concorrência e fila (400 requisições distintas, cache desligado, 2 produtores)

| fila | workers | vazão (req/s) | latência mediana (ms) | p95 (ms) | fila média | fila máx | espera na fila média (ms) | utilização | produtor bloqueado (s) | RSS máx (MB) | threads máx | perdidas | duplicadas |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4 | 1 | 25.3 ± 1.5 | 37.4 | 50.5 | 3.5 | 4 | 157.3 | 1.00 | 31.14 | 114 | 8 | 0 | 0 |
| 4 | 2 | 36.5 ± 0.8 | 53.3 | 72.8 | 3.3 | 4 | 106.2 | 1.00 | 21.43 | 178 | 9 | 0 | 0 |
| 4 | 4 | 43.1 ± 0.2 | 89.7 | 137.6 | 3.2 | 4 | 86.8 | 0.99 | 17.91 | 229 | 11 | 0 | 0 |
| 4 | 8 | 46.0 ± 1.5 | 165.9 | 274.3 | 3.0 | 4 | 76.0 | 0.99 | 16.77 | 301 | 15 | 0 | 0 |
| 64 | 1 | 25.4 ± 1.9 | 37.3 | 50.5 | 58.5 | 64 | 2340.9 | 1.00 | 24.17 | 329 | 8 | 0 | 0 |
| 64 | 2 | 39.4 ± 0.3 | 49.5 | 67.3 | 58.3 | 64 | 1482.6 | 1.00 | 15.12 | 338 | 9 | 0 | 0 |
| 64 | 4 | 47.0 ± 1.1 | 82.5 | 126.1 | 58.2 | 64 | 1247.8 | 1.00 | 12.78 | 357 | 11 | 0 | 0 |
| 64 | 8 | 43.6 ± 6.0 | 177.0 | 292.1 | 58.0 | 64 | 1339.7 | 0.99 | 13.41 | 388 | 15 | 0 | 0 |

## C4 — cache compartilhado (400 requisições, 2 workers)

| cenário | capacidade | política | acerto (%) | erros (misses) | substituições | tempo economizado (s) | tempo total (s) | vazão (req/s) | p95 (ms) |
|---|---|---|---|---|---|---|---|---|---|
| distintas | 0 | lru | 0.0 | 400 | 0 | 0.00 | 12.91 ± 2.73 | 32.0 | 100.7 |
| distintas | 16 | fifo | 0.0 | 400 | 384 | 0.00 | 19.23 ± 4.61 | 21.8 | 152.0 |
| distintas | 16 | lru | 0.0 | 400 | 384 | 0.00 | 14.79 ± 5.04 | 28.9 | 119.8 |
| distintas | 64 | lru | 0.0 | 400 | 336 | 0.00 | 11.74 ± 1.29 | 34.3 | 81.3 |
| distintas | 512 | lru | 0.0 | 400 | 0 | 0.00 | 11.27 ± 1.04 | 35.7 | 79.3 |
| parafrase50 | 0 | lru | 0.0 | 400 | 0 | 0.00 | 9.91 ± 0.24 | 40.4 | 66.2 |
| parafrase50 | 16 | fifo | 13.2 | 347 | 326 | 2.81 | 9.08 ± 0.07 | 44.1 | 69.5 |
| parafrase50 | 16 | lru | 12.6 | 350 | 330 | 2.50 | 8.76 ± 0.20 | 45.7 | 67.5 |
| parafrase50 | 64 | lru | 34.4 | 262 | 194 | 7.48 | 6.93 ± 0.11 | 57.8 | 67.3 |
| parafrase50 | 512 | lru | 50.9 | 196 | 0 | 10.87 | 5.17 ± 0.17 | 77.4 | 66.4 |
| repetidas50 | 0 | lru | 0.0 | 400 | 0 | 0.00 | 12.02 ± 0.76 | 33.4 | 79.8 |
| repetidas50 | 16 | fifo | 10.2 | 359 | 340 | 2.11 | 9.20 ± 0.20 | 43.5 | 67.7 |
| repetidas50 | 16 | lru | 9.9 | 360 | 339 | 2.01 | 9.42 ± 0.35 | 42.5 | 69.8 |
| repetidas50 | 64 | lru | 29.7 | 281 | 215 | 6.33 | 7.31 ± 0.31 | 54.8 | 69.0 |
| repetidas50 | 512 | lru | 44.7 | 221 | 0 | 9.32 | 5.73 ± 0.05 | 69.8 | 65.8 |
| repetidas90 | 0 | lru | 0.0 | 400 | 0 | 0.00 | 9.94 ± 0.20 | 40.2 | 64.6 |
| repetidas90 | 16 | fifo | 73.7 | 105 | 75 | 16.60 | 2.75 ± 0.46 | 147.8 | 61.9 |
| repetidas90 | 16 | lru | 74.0 | 104 | 70 | 16.19 | 2.74 ± 0.20 | 146.3 | 59.4 |
| repetidas90 | 64 | lru | 89.2 | 43 | 0 | 19.20 | 1.25 ± 0.14 | 321.4 | 54.9 |
| repetidas90 | 512 | lru | 89.2 | 43 | 0 | 20.56 | 1.29 ± 0.13 | 311.7 | 56.2 |

## C5a — crescimento do corpus e do contexto (1 worker, 150 consultas)

| docs | índice (MB) | modo | contexto máx (B) | recuperação mediana (ms) | geração mediana (ms) | p95 total (ms) | RSS máx (MB) | VSZ máx (MB) | falhas maiores | falhas menores | lido do disco (MB) | contexto médio (B) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 500 | 6 | read | 500 | 0.82 | 20.3 | 24.6 | 44 | 448 | 0 | 1138 | 6 | 22 |
| 500 | 6 | read | 2000 | 0.82 | 34.4 | 45.9 | 44 | 448 | 0 | 1155 | 6 | 1674 |
| 500 | 6 | read | 8000 | 1.06 | 98.3 | 133.3 | 44 | 449 | 0 | 1242 | 6 | 7581 |
| 500 | 6 | mmap | 500 | 0.76 | 20.3 | 24.2 | 44 | 448 | 57 | 811 | 6 | 22 |
| 500 | 6 | mmap | 2000 | 0.84 | 34.2 | 44.7 | 44 | 448 | 56 | 833 | 6 | 1674 |
| 500 | 6 | mmap | 8000 | 1.09 | 96.2 | 127.5 | 44 | 449 | 56 | 915 | 6 | 7581 |
| 2000 | 25 | read | 500 | 1.98 | 20.3 | 26.3 | 63 | 467 | 0 | 1145 | 25 | 43 |
| 2000 | 25 | read | 2000 | 2.06 | 34.3 | 47.2 | 63 | 467 | 0 | 1334 | 25 | 1655 |
| 2000 | 25 | read | 8000 | 2.60 | 112.7 | 155.4 | 64 | 468 | 0 | 1602 | 25 | 7617 |
| 2000 | 25 | mmap | 500 | 1.96 | 20.3 | 26.8 | 63 | 467 | 209 | 1186 | 25 | 43 |
| 2000 | 25 | mmap | 2000 | 2.11 | 37.2 | 51.4 | 63 | 467 | 208 | 1211 | 25 | 1655 |
| 2000 | 25 | mmap | 8000 | 2.66 | 114.3 | 149.4 | 64 | 468 | 209 | 1308 | 25 | 7617 |
| 8000 | 102 | read | 500 | 9.55 | 20.4 | 40.0 | 140 | 545 | 0 | 23512 | 102 | 38 |
| 8000 | 102 | read | 2000 | 10.26 | 43.7 | 109.4 | 140 | 545 | 0 | 23560 | 102 | 1666 |
| 8000 | 102 | read | 8000 | 8.35 | 112.6 | 167.4 | 141 | 545 | 0 | 23631 | 102 | 7604 |
| 8000 | 102 | mmap | 500 | 10.59 | 20.5 | 57.9 | 140 | 545 | 831 | 23979 | 102 | 38 |
| 8000 | 102 | mmap | 2000 | 9.08 | 41.5 | 71.6 | 140 | 545 | 829 | 24015 | 102 | 1666 |
| 8000 | 102 | mmap | 8000 | 8.21 | 105.7 | 141.0 | 140 | 545 | 830 | 24099 | 102 | 7604 |
| 24000 | 305 | read | 500 | 21.79 | 20.4 | 51.9 | 344 | 748 | 0 | 1247 | 305 | 53 |
| 24000 | 305 | read | 2000 | 21.55 | 38.4 | 79.8 | 344 | 748 | 0 | 1265 | 305 | 1640 |
| 24000 | 305 | read | 8000 | 21.48 | 103.5 | 160.2 | 344 | 748 | 0 | 1350 | 305 | 7571 |
| 24000 | 305 | mmap | 500 | 20.33 | 20.4 | 48.1 | 344 | 748 | 2474 | 3519 | 305 | 53 |
| 24000 | 305 | mmap | 2000 | 20.95 | 36.9 | 75.5 | 344 | 748 | 2474 | 3545 | 305 | 1640 |
| 24000 | 305 | mmap | 8000 | 21.87 | 105.9 | 173.1 | 344 | 748 | 2475 | 3640 | 305 | 7571 |

## C5b — índice de 1024 MB sob limite de memória do cgroup (swap do contêiner desligado)

| limite | modo | rep | exit | OOM kill | abertura (s) | consultas concluídas | mediana consulta (ms) | RSS máx (MB) | falhas maiores | lido do disco (MB) | swap usado (MB) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2048m | read | 1 | 0 | não | 1.74 | 15 | 71 | 1061 | 0 | 1024 | 1 |
| 2048m | read | 2 | 0 | não | 0.91 | 15 | 70 | 1060 | 0 | 1024 | 1 |
| 2048m | read | 3 | 0 | não | 1.35 | 15 | 103 | 1061 | 0 | 1024 | 1 |
| 2048m | mmap | 1 | 0 | não | 0.00 | 15 | 153 | 1062 | 8296 | 1024 | 1 |
| 2048m | mmap | 2 | 0 | não | 0.00 | 15 | 89 | 1060 | 8302 | 1024 | 1 |
| 2048m | mmap | 3 | 0 | não | 0.00 | 15 | 91 | 1061 | 8301 | 1024 | 1 |
| 384m | read | 1 | 137 | SIM | - | 0 | - | - | - | - | - |
| 384m | read | 2 | 137 | SIM | - | 0 | - | - | - | - | - |
| 384m | read | 3 | 137 | SIM | - | 0 | - | - | - | - | - |
| 384m | mmap | 1 | 0 | não | 0.00 | 15 | 1174 | 398 | 125343 | 15339 | 1 |
| 384m | mmap | 2 | 0 | não | 0.00 | 15 | 1204 | 399 | 124972 | 15363 | 1 |
| 384m | mmap | 3 | 0 | não | 0.00 | 15 | 1589 | 399 | 124790 | 15363 | 1 |

## C6 — falhas controladas (média de 3 repetições)

| cenário | requisições | ok | erros | rejeitadas | retentativas | perdidas (tot.) | tempo (s) |
|---|---|---|---|---|---|---|---|
| arquivo_ausente | 40 | 0 | 40 | 0 | 80 | 0 | 0.63 |
| indice_indisponivel_recupera | 120 | 120 | 0 | 0 | 10 | 0 | 2.19 |
| fila_saturada_rejeita | 120 | 8 | 0 | 112 | 0 | 0 | 0.26 |
| fila_saturada_bloqueia | 120 | 120 | 0 | 0 | 0 | 0 | 4.01 |
| servico_externo_falha30_retries0 | 120 | 79 | 41 | 0 | 0 | 0 | 0.96 |
| servico_externo_falha30_retries3 | 120 | 119 | 1 | 0 | 55 | 0 | 1.81 |

## D1 — cache compartilhado: corrida e correções (8 threads × 1500 ops, 40 chaves)

| modo | ops | hits contados | misses contados | atualizações perdidas | computações | computações duplicadas | tempo (s) |
|---|---|---|---|---|---|---|---|
| unsafe | 12000 | 1614 | 52 | 10334 | 62 | 22 | 0.36 |
| global_lock | 12000 | 11960 | 40 | 0 | 40 | 0 | 0.68 |
| per_key | 12000 | 11960 | 40 | 0 | 40 | 0 | 0.56 |

## D2 — log concorrente

| logger | eventos | linhas no arquivo | linhas corrompidas (média) |
|---|---|---|---|
| UnsafeLogger | 2400 | 2400 | 1817 |
| SafeLogger | 2400 | 2400 | 0 |

## D3 — produtores/consumidores com buffer limitado (3 produtores × 500 itens, 2 consumidores)

| cenário | capacidade | produzidos | consumidos | perdidos | duplicados | violações FIFO | ocupação máx | produtor bloqueado (s) | consumidor esperou (s) | tempo (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| consumidor_lento | 1 | 1500 | 1500 | 0 | 0 | 0 | 1 | 1.20 | 0.05 | 0.41 |
| consumidor_lento | 4 | 1500 | 1500 | 0 | 0 | 0 | 4 | 1.21 | 0.05 | 0.41 |
| consumidor_lento | 64 | 1500 | 1500 | 0 | 0 | 0 | 64 | 1.14 | 0.05 | 0.41 |
| produtor_lento | 1 | 1500 | 1500 | 0 | 0 | 0 | 1 | 0.04 | 1.00 | 0.50 |
| produtor_lento | 4 | 1500 | 1500 | 0 | 0 | 0 | 3 | 0.01 | 0.98 | 0.50 |
| produtor_lento | 64 | 1500 | 1500 | 0 | 0 | 0 | 3 | 0.01 | 1.00 | 0.50 |

## D4 — deadlock isolado em subprocesso

| modo | concluiu | tempo (s) | resultado |
|---|---|---|---|
| deadlock | NÃO | 3.01 | DEADLOCK detectado por timeout; processo encerrado (kill) |
| ordered | sim | 0.30 | COMPLETED T1,T2 |
| timeout | sim | 0.60 | COMPLETED T1,T2 |
