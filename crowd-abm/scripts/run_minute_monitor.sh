#!/usr/bin/env bash
set -euo pipefail

cd /media/ayush/9AE2A254E2A23503/masti/crowd-abm

PYTHONPATH="$PWD" .venv/bin/python scripts/minute_simulation.py > /tmp/minute_sim_result_full.json 2>/tmp/minute_sim_err_full.log &
SIM_PID=$!

: > /tmp/cpu_samples_full.txt
if command -v nvidia-smi >/dev/null 2>&1; then
  GPU_AVAILABLE=1
  : > /tmp/gpu_samples_full.txt
else
  GPU_AVAILABLE=0
fi

while kill -0 "$SIM_PID" 2>/dev/null; do
  ts=$(date +%s)
  cpu=$(ps -p "$SIM_PID" -o %cpu= | tr -d ' ')
  rss=$(ps -p "$SIM_PID" -o rss= | tr -d ' ')
  [[ -n "$cpu" ]] && echo "$ts $cpu $rss" >> /tmp/cpu_samples_full.txt

  if [[ "$GPU_AVAILABLE" -eq 1 ]]; then
    nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used --format=csv,noheader,nounits 2>/dev/null \
      | awk -v t="$ts" -F',' '{gsub(/ /,"",$1);gsub(/ /,"",$2);gsub(/ /,"",$3);print t" "$1" "$2" "$3}' \
      >> /tmp/gpu_samples_full.txt || true
  fi

  sleep 1
done

wait "$SIM_PID"

echo "CPU summary:"
awk 'BEGIN{n=0;sum=0;max=0;rssmax=0} {n++;sum+=$2;if($2>max)max=$2;if($3>rssmax)rssmax=$3} END{if(n==0){print "cpu_samples=0 avg_cpu=0 max_cpu=0 max_rss_kb=0"} else {printf "cpu_samples=%d avg_cpu=%.2f max_cpu=%.2f max_rss_kb=%d\n",n,sum/n,max,rssmax}}' /tmp/cpu_samples_full.txt

echo "GPU summary:"
if [[ "$GPU_AVAILABLE" -eq 1 && -s /tmp/gpu_samples_full.txt ]]; then
  awk 'BEGIN{n=0;sg=0;sm=0;gmax=0;mmax=0;memmax=0} {n++;sg+=$2;sm+=$3;if($2>gmax)gmax=$2;if($3>mmax)mmax=$3;if($4>memmax)memmax=$4} END{if(n==0){print "gpu_samples=0"} else {printf "gpu_samples=%d avg_gpu_util=%.2f max_gpu_util=%.2f avg_mem_util=%.2f max_mem_util=%.2f max_mem_used_mb=%d\n",n,sg/n,gmax,sm/n,mmax,memmax}}' /tmp/gpu_samples_full.txt
else
  echo "gpu_monitoring=unavailable"
fi

echo "Result JSON:"
cat /tmp/minute_sim_result_full.json

echo "Stderr:"
cat /tmp/minute_sim_err_full.log
