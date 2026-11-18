# Interim 3-way comparison: first 22 of 50 questions (20 OSHA + 2 DOE)

Model qwen2.5:3b via Ollama, CPU (i5-1340P), judge = same model. Snapshot of the first 66 rows of
compare.jsonl, taken 2026-11-18 22:42. The set is OSHA-heavy and small, so treat differences of 1–3
questions as noise. The final table is compare.md once all 50 questions finish.

| system | correctness (1/0.5/0) | fully correct | faithfulness | abstained | median latency | LLM calls | input tok | output tok | decode tok/s |
|---|---|---|---|---|---|---|---|---|---|
| single | 0.591 | 11/22 | 0.976 (n=21) | 1 | 23.0 s | 1 | 1,276 | 48 | 11.67 |
| multi | 0.705 | 15/22 | 1.000 (n=19) | 2 | 162.6 s | 8.0 | 8,361 | 983 | 11.73 |
| multi_reflect | 0.682 | 13/22 | 0.940 (n=19) | 3 | 159.6 s | 8.9 | 9,993 | 1,275 | 11.56 |

Notes
- Cost is $0.00 per request for every system: local model, price table rates are 0.
- multi_reflect revised on 3/22 questions (2 with one revision, 1 with two). It fixed 3 answers that multi got wrong
  (osha-09, osha-14, osha-19) and broke 3 that multi got right (osha-10, osha-11, osha-17): net zero.
- Outlier: multi on osha-17 took 5,740 s; one Writer call needed 2 retries. All other nodes in that run were normal,
  so it is most likely the laptop sleeping or Ollama stalling. The median is unaffected; p95/max are not meaningful
  for this snapshot.
- Judge leniency: on doe-02 the multi system answered "50% to 60%, as calculated" (gold: 35% to more than 90%). The
  correctness judge marked it incorrect, but the faithfulness judge gave it 1.0. The 3B judge does not reliably
  catch invented numbers, so faithfulness here is an upper bound.
- Prefill tok/s is not reported: Ollama reuses cached prompt prefixes, which inflates the prompt-eval rate for the
  multi-agent systems (many calls share long prefixes), so the numbers are not comparable across systems.
