import { createApp } from '../app.ts';
import { runBenchmark } from '/workspace/github-core-clone-01-kit/sdk/conformance/bench.ts';

const baseUrl = process.env.BENCH_URL;
const token = process.env.MAKEFUN_SHOP_TOKEN;
if (!baseUrl || !token) throw new Error('Set BENCH_URL to a running server and MAKEFUN_SHOP_TOKEN to its token');
const perf = await runBenchmark({ baseUrl, token, log: (line) => process.stdout.write(`${line}\n`) });
const workloads = perf.workloads.map((workload) => ({ name: workload.name, p50_ms: workload.p50_ms }));
process.stdout.write(`${JSON.stringify({ workloads, perf_p50_us: perf.perf_p50_us })}\n`);
