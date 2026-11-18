#!/bin/bash
# Usage: rig.sh <appdir> <port> <tag> — cold-start server under production-pod limits (both vCPUs, 1G),
# run the kit rig once, write JSON to <appdir>/rig_<tag>.json, echo "exit=<rc> cpu=<server_cpu_seconds>"
set -u
APPDIR=$1; PORT=$2; TAG=$3
cd "$APPDIR"
MAKEFUN_SHOP_TOKEN=benchtok systemd-run --scope -p MemoryMax=1G --quiet \
  taskset -c 0,1 node --experimental-strip-types \
  -e "import('./app.ts').then(m=>{const a=m.createApp(${PORT});a.listen(${PORT})})" \
  &>>/tmp/server_${TAG}.log &
SPID=$!
for i in $(seq 1 40); do sleep 0.5; curl -s -o /dev/null http://127.0.0.1:${PORT}/healthz && break; done
curl -s -o /dev/null -w "health:%{http_code} " http://127.0.0.1:${PORT}/healthz
NPID=$(pgrep -f "createApp.${PORT}" | head -1)
cpu0=0
[ -n "$NPID" ] && read -r _ _ _ _ _ _ _ _ _ _ _ _ _ _ UT ST CUT CST _ < <(awk '{print $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18}' /proc/$NPID/stat 2>/dev/null) || true
if [ -n "$NPID" ]; then
  cpu0=$(awk '{u=$14+$15; s=$16+$17; print (u+s)/100}' /proc/$NPID/stat 2>/dev/null || echo 0)
fi
cd /workspace/github-core-clone-01-kit
node --experimental-strip-types sdk/run.ts --url http://127.0.0.1:${PORT} --token benchtok --perf --json > /tmp/rig_${TAG}.json 2>/tmp/rig_${TAG}.err
EC=$?
if [ -n "$NPID" ]; then
  cpu1=$(awk '{u=$14+$15; s=$16+$17; print (u+s)/100}' /proc/$NPID/stat 2>/dev/null || echo 0)
  CPU=$(awk -v a=$cpu0 -v b=$cpu1 'BEGIN{printf "%.2f", b-a}')
else CPU=NA; fi
kill $SPID 2>/dev/null; pkill -f "createApp.${PORT}" 2>/dev/null; pkill -f "createApp.${PORT}" 2>/dev/null; wait $SPID 2>/dev/null
cp /tmp/rig_${TAG}.json "$APPDIR/rig_${TAG}.json"
echo "exit=$EC cpu=$CPU"
