# Evidence and references

Read this when you research anything outside the codebase, or when you need to back a claim about the project with data.

## Source tiers

Use the highest tier available. If you have to use a lower one, say so.

| Tier | What | Examples |
| --- | --- | --- |
| 1. Primary | The people who made it or who set the rule | Engine and library docs, platform rules (Steamworks, Apple App Review, Google Play policy, Discord developer docs), standards, the original paper, the developer's own GDC talk or postmortem |
| 2. Recognized work | Work an expert jury has judged excellent | Winners and finalists of the GDC Awards, BAFTA Games Awards, IGF, The Game Awards, D.I.C.E. Awards, plus their postmortems |
| 3. Reputable secondary | Careful reporting and well-kept code | Established games press, peer-reviewed surveys, GitHub repos with a clear license, recent releases, CI and real adoption |
| 4. Leads only | Use to find a better source, then cite that | Wikipedia, forum threads, blogs, video essays |
| Avoid | | SEO content farms, unsourced listicles, AI-generated pages |

## Award-winning references, used correctly

Award winners are good references for **principles**: why a mechanic reads clearly, how feedback is timed, how levels teach. Write down the principle and the numbers ("hit-stop of 3–5 frames on heavy impacts"), never the art, characters, names, music, levels or recognizable look. A specific existing game is never a template to recreate, only an example of a principle that you then express in the owner's own style.

## Citation format

Give the claim, then the link with its publisher and year, then the tier in brackets:

> The Steam Direct fee is $100 per game and is returned after $1,000 in sales — [PC Gamer, 2017](https://www.pcgamer.com/valve-reveals-steam-direct-fee-upcoming-changes-to-the-store) [3; confirm on partner.steamgames.com]

If sources disagree, say so and give both.

## Measuring instead of guessing

For any claim about the project ("faster", "more realistic", "fixed"):

1. **Metric.** Name what you measure and the unit: frame time in ms (p50/p95), m/s², bytes, error count.
2. **Baseline.** Measure before you change anything, using the same method.
3. **Change.** Make one change at a time where possible.
4. **After.** Repeat the measurement with the same inputs. Report n, the spread and the difference.
5. **Threshold.** Define what counts as passing before you look at the result.

Physics constants get a measured value and an expected value with a source, plus the percentage error. Example: free fall measured 9.79 m/s² against 9.81 m/s² (standard gravity, defined value) is 0.2% off.

Useful physical reference values. Confirm against a handbook (for example, the Engineering ToolBox tables) before you rely on them:

| Material | Density (kg/m³) | Typical friction (dry, similar material) |
| --- | --- | --- |
| Softwood (pine) | 350–550 | 0.25–0.5 |
| Brick | 1,600–2,000 | 0.6–0.7 |
| Concrete | ~2,400 | 0.6–0.7 |
| Glass | ~2,500 | 0.4–0.9 (clean glass on glass is high) |
| Steel | ~7,850 | 0.5–0.8 |

## Reporting

End research with the sources used, as markdown links, and anything you could not confirm.
