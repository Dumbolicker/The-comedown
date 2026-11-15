# Why "one more run" works: engagement design and its sources

This page lists the engagement features in Borrowed Time, the research behind each one, and the lines we chose not to cross.

The references are well-known papers with their DOIs so you can look them up. I wrote them from memory and did not re-fetch them while writing this page.

## What's in the game

| Technique | What the research says | What the game does | Code |
| --- | --- | --- | --- |
| Competence and mastery | Enjoyment and wanting to play again track how competent, autonomous and connected a game makes players feel (Ryan, Rigby & Przybylski 2006) | Chaos-streak milestones (×5, ×10, ×15, ×20, ×30, ×50) give escalating bonuses and sound. From ×10 up you also get a beat of slow motion | `engageUpdate`, `MILES` |
| Juice and feedback | Strong, immediate feedback makes the same action feel better (Jonasson & Purho, "Juice it or lose it", 2012) | Slow motion (45% speed) on roof cave-ins, the water-tower splash, a new personal best and big streaks. Doors kicked off their hinges | `G.slowT` in `frame()` |
| Specific, attainable goals | Specific, challenging goals raise effort more than "do your best" (Locke & Latham 2002) | Your best score sits under the chaos counter all run. Three daily challenges. A "new personal best" moment mid-run | `pbval`, `dailyList` |
| Goal gradient | People speed up as a goal gets close (Kivetz, Urminsky & Zheng 2006) | The game-over screen names your closest unfinished goal: "50 chaos short of your best", "So close: 82% of a daily" | `nextGoalText` |
| Endowed progress | A head start makes people more likely to finish (Nunes & Drèze 2006) | The chrome bank pays up to Ð 250 into your next run, so it starts ahead | `chromePayout` |
| Curiosity gap | A known gap in what you know drives the urge to close it (Loewenstein 1994) | Feat names are visible but their requirements stay hidden until you earn them. The game-over screen counts how many secret feats are left | `openRecords`, `nextGoalText` |
| Variable rewards | Rewards on a variable schedule keep behavior going strongly (Ferster & Skinner 1957) | About 8.5% of untainted stashes are golden: +10 s and +1,000 chaos, and they sparkle so you notice them. The creature roll (15%, not shown on the title) keeps doses surprising | `golden`, `transform` roll |
| Habit and return visits | Repeating a behavior in the same context builds habit (Lally et al. 2010) | Daily streak: Ð 50 per consecutive day into the chrome bank, capped at Ð 300 from day 6 | `streakTick` |
| Flow | People stay engaged when challenge matches skill (Csikszentmihalyi 1990) | The draining clock, heat levels and the drone ramp up pressure while you're doing well | existing loop |

## Lines we didn't cross

- **No rigged near-misses in the slot machine.** Near-misses switch on win-related brain circuitry and make people want to keep gambling, even though they're losses (Clark et al. 2009). The reels stay honest. The visible pity prize (a guaranteed win within 20 spins) stays as it is.
- **No real money, ever.** Dollas can't be bought or cashed out.
- **No guilt, no fear of missing out.** A missed day restarts the streak quietly. Nothing counts down to make you come back, and no message shames you for leaving.
- **No endless streak pressure.** The streak bonus stops growing at day 6.
- **Break reminder.** On by default, under Settings → Comfort. After each hour of play you get one short "stretch and drink some water" note. The WHO lists gaming disorder in ICD-11 (6C51), and an honest nudge costs nothing.

## References

- Clark, L., Lawrence, A. J., Astley-Jones, F., & Gray, N. (2009). Gambling near-misses enhance motivation to gamble and recruit win-related brain circuitry. *Neuron*, 61(3), 481–490. https://doi.org/10.1016/j.neuron.2008.12.031
- Csikszentmihalyi, M. (1990). *Flow: The Psychology of Optimal Experience*. Harper & Row.
- Ferster, C. B., & Skinner, B. F. (1957). *Schedules of Reinforcement*. Appleton-Century-Crofts.
- Jonasson, M., & Purho, P. (2012). *Juice it or lose it* (conference talk).
- Kivetz, R., Urminsky, O., & Zheng, Y. (2006). The goal-gradient hypothesis resurrected. *Journal of Marketing Research*, 43(1), 39–58. https://doi.org/10.1509/jmkr.43.1.39
- Lally, P., van Jaarsveld, C. H. M., Potts, H. W. W., & Wardle, J. (2010). How are habits formed: Modelling habit formation in the real world. *European Journal of Social Psychology*, 40(6), 998–1009. https://doi.org/10.1002/ejsp.674
- Locke, E. A., & Latham, G. P. (2002). Building a practically useful theory of goal setting and task motivation. *American Psychologist*, 57(9), 705–717. https://doi.org/10.1037/0003-066X.57.9.705
- Loewenstein, G. (1994). The psychology of curiosity: A review and reinterpretation. *Psychological Bulletin*, 116(1), 75–98. https://doi.org/10.1037/0033-2909.116.1.75
- Nunes, J. C., & Drèze, X. (2006). The endowed progress effect. *Journal of Consumer Research*, 32(4), 504–512. https://doi.org/10.1086/500480
- Ryan, R. M., Rigby, C. S., & Przybylski, A. (2006). The motivational pull of video games: A self-determination theory approach. *Motivation and Emotion*, 30(4), 344–360. https://doi.org/10.1007/s11031-006-9051-8

## How to tell whether it works

Measure it on your own players, not just from the papers. Two numbers matter most, and both are already saved per device in `bt_profile`:

- runs per session
- days played in a row (`streak.n`)

On Steam, compare the achievement unlock rates once the game is out.
