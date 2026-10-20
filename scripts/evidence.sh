#!/usr/bin/env bash
# Evidências de processos, threads, memória, E/S e chamadas de sistema (dentro do contêiner).
# Requer --cap-add=SYS_PTRACE para o strace.
set -u
OUT=${1:-/work/results/evidence}
mkdir -p "$OUT"
cd /work/scripts

echo "== 1. workload com 4 trabalhadores em segundo plano =="
python - <<'EOF' &
from common import ensure_index
from genresearch.corpus import make_workload
from genresearch.server import Config, Server
idx, _ = ensure_index(2000)
Server(idx, Config(workers=4, producers=2, queue_cap=16, cache_cap=0, gen_rounds=6000)).run(make_workload(600, 600, 0))
EOF
sleep 4
PID=$(pgrep -f "python -" | head -1)
echo "PID do servidor: $PID"

{
  echo "### ps -eLf (processos e threads) — threads: worker-N, producer-N"; ps -Lo pid,tid,psr,pcpu,stat,wchan:22,comm -p "$PID"
  echo; echo "### /proc/$PID/status (resumo)"; grep -E "Name|State|Threads|VmSize|VmRSS|VmHWM|RssAnon|RssFile|voluntary" /proc/$PID/status
  echo; echo "### ctxt switches por thread (voluntárias/involuntárias)"
  for t in /proc/$PID/task/*; do printf "%s %s " "$(basename $t)" "$(cat $t/comm)"; grep -E "ctxt" $t/status | tr '\n' ' '; echo; done
  echo; echo "### /proc/$PID/io"; cat /proc/$PID/io
  echo; echo "### pidstat -t (CPU por thread, 3 s)"; pidstat -t -p "$PID" 1 3 2>&1
  echo; echo "### vmstat 1 5"; vmstat 1 5
  echo; echo "### iostat -xz 1 3"; iostat -xz 1 3
  echo; echo "### /proc/$PID/smaps_rollup"; cat /proc/$PID/smaps_rollup 2>&1
} > "$OUT/processos_threads_memoria.txt" 2>&1
wait
echo "== 2. strace -c -f: resumo de chamadas de sistema do pipeline =="
strace -f -c -o "$OUT/strace_pipeline_resumo.txt" python - <<'EOF' >/dev/null 2>&1
from common import ensure_index
from genresearch.corpus import make_workload
from genresearch.server import Config, Server
idx, _ = ensure_index(500)
Server(idx, Config(workers=4, producers=2, queue_cap=16, cache_cap=0, gen_rounds=600, log_path="/tmp/x.log")).run(make_workload(100, 100, 0))
EOF
echo "== 3. strace: read() vs mmap() em arquivo de 16 MB =="
python - <<'EOF'
import os
p="/workdata/bigfile_16.bin"
if not os.path.exists(p): open(p,"wb").write(os.urandom(16<<20))
EOF
cat > /tmp/rd.py <<'EOF'
import os,sys,mmap,zlib
p="/workdata/bigfile_16.bin"; fd=os.open(p,os.O_RDONLY); a=0
if sys.argv[1]=="read":
    while True:
        b=os.read(fd,1<<20)
        if not b: break
        a=zlib.crc32(b,a)
else:
    m=mmap.mmap(fd,0,access=mmap.ACCESS_READ)
    for o in range(0,len(m),1<<20): a=zlib.crc32(m[o:o+(1<<20)],a)
print(a)
EOF
strace -f -e trace=openat,read,pread64,mmap,munmap,madvise,fstat -o "$OUT/strace_read.txt" python /tmp/rd.py read >/dev/null
strace -f -e trace=openat,read,pread64,mmap,munmap,madvise,fstat -o "$OUT/strace_mmap.txt" python /tmp/rd.py mmap >/dev/null
for m in read mmap; do
  echo "--- $m: chamadas relevantes ao arquivo de dados" > "$OUT/strace_${m}_resumo.txt"
  grep -c "read(" "$OUT/strace_$m.txt" | sed "s/^/read() total: /" >> "$OUT/strace_${m}_resumo.txt"
  grep -E "bigfile_16" "$OUT/strace_$m.txt" >> "$OUT/strace_${m}_resumo.txt"
  grep -E "mmap\(NULL, 16777216" "$OUT/strace_$m.txt" >> "$OUT/strace_${m}_resumo.txt" || true
done
echo "evidências em $OUT"
