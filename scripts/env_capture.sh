#!/usr/bin/env bash
# Parte A — observação do ambiente (executado dentro do contêiner Linux).
set -u
echo "### data (UTC): $(date -u +%FT%TZ)"
echo "### uname -a";            uname -a
echo "### /etc/os-release";     cat /etc/os-release
echo "### lscpu";               lscpu
echo "### free -h";             free -h
echo "### /proc/meminfo";       cat /proc/meminfo
echo "### lsblk";               lsblk 2>&1
echo "### df -h";               df -h
echo "### mount (sistemas de arquivos usados)"; mount | grep -E " / | /work | /workdata "
echo "### swapon --show";       swapon --show 2>&1; echo "(fim swapon)"
echo "### vm.swappiness";       cat /proc/sys/vm/swappiness
echo "### cgroup (limites do contêiner)"
for f in memory.max memory.swap.max cpu.max; do echo "$f: $(cat /sys/fs/cgroup/$f 2>&1)"; done
echo "### GPU";                 (command -v nvidia-smi >/dev/null && nvidia-smi) || echo "sem GPU NVIDIA (execução somente em CPU)"
echo "### python / bibliotecas"; python --version; pip list 2>/dev/null | grep -i -E "numpy|matplotlib|markdown"
echo "### page size";           getconf PAGESIZE
echo "### vmstat 1 3";          vmstat 1 3
echo "### iostat -xz 1 2";      iostat -xz 1 2
