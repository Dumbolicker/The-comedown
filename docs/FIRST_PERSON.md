# First person (17 Nov 2026)

## Switching

- **X** (rebindable under Settings → Controls), the **1P** button on the clock, **R3** on a controller, or **scroll all the way in**. Scroll out, press it again, or tap **3P** to go back.
- Settings → Controls → **Camera** picks the view you start in. The choice is saved on this device.
- While you're a ragdoll (a flop, a tackle that goes wrong, an explosion) the camera steps out behind you and comes back
  when you're up, so you can see what happened.

## Controls

| | Keyboard and mouse | Controller | Touch |
| --- | --- | --- | --- |
| Look | mouse | right stick | right thumb |
| Main thing (open, sit, talk, pick up…) | **E** | **Y** | **GRAB** (shows the verb) |
| The other thing (kick, knock, wave…) | **G** or right-click | **RB** (when you have no horns) | **ALT** (appears when there is one) |
| Tackle, or throw what you hold | click or **F** | **X** / **RT** | **TACKLE** |

The crosshair is a dot. A gold ring around it means you can do something with what you're looking at, and the label under
it names the thing and its two verbs. "(far)" means walk closer.

## Everything from third person still works

Moving, sprinting, jumping and double jumps, tackling (you lunge where you look), throwing (it goes where you look, with
a little arc), picking things up (held things sit low in front of you), flopping, hollering, pooping, horns, dragon
fire, wings, getting laced or folded, the drugs and their effects, slot machines, Doc's shop, quests, doors that open as
you walk up, stashes you walk into, and coins you walk over. The tests below run each of them in first person.

## What you can do with what you look at

| What | E (Y, GRAB) | G (right-click, RB, ALT) |
| --- | --- | --- |
| Trash can, wheelie bin | Rummage (coins, a bottle, half a sandwich, or something that makes people say you smell) | Pick up |
| Dumpster | Dig through it | Kick |
| Trash bag | Pick up | Rip it open |
| Crate | Pick up | Smash it |
| Oil drum, tire, flamingo, beach ball, rubble, poop | Pick up | Kick |
| Traffic cone | Pick up | Put it on your head (it falls off when you go down) |
| Mailbox | Open it | Pick up |
| Bench, lawn chair, stool | Sit | Pick up |
| Couch | Sit | Search the cushions |
| Picnic table | Sit (on your side, facing the table) | Flip it over |
| Table, card table | Pick up, or play a hand (Ð 10, even odds) | Flip it over |
| Fence | Pick up | Kick (it splinters) |
| Garden gnome | Pick up | Rub its hat for luck |
| Shopping cart | Pick up | Shove |
| Old TV, floor lamp | Turn on / off | Pick up |
| Propane tank | Pick up | Open the valve (it takes off, then goes off) |
| Car | Honk the horn (people jump) | Try the door (locked, an alarm, or change in the cup holder) |
| Porta-potty | Use it (+3 s) | Shove |
| Grill | Light it | Kick |
| Fire hydrant | Open the cap (geyser) | Kick |
| Newspaper box | Read the paper | Pick up |
| Empty bottle | Pick up | Smash it |
| Empty salt bag | Pick up | Crumple it |
| Fridge | Open it (one snack each, +2 s) | Shove |
| Bookshelf | Read a book | Shove |
| Store shelf | Take something (shoplifting raises heat; Raj notices) | Shove |
| Parcel | Pick up | Shake it |
| Coin | Pick it up | Flip it |
| Vending machine | Buy a soda (Ð 5) | Shake it (a free soda, nothing, or it tips onto you) |
| A stranger | Talk (sometimes they point you at a stash) | Shove |
| Someone who's down | Help them up | Check their pockets |
| Police | Talk | Shove (heat) |
| Quest people | Talk | Wave |
| Doc Suture | Buy cyberware | Chat |
| Door | Open it / Close it (it stays shut a few seconds even with you next to it) | Knock (someone might answer) |
| Slot machine | Play | Kick |
| Window | Knock | Punch |
| Wall | Look closer | Punch (condemned walls give way) |
| Bed | Lie down | Sit on the edge |
| Kitchen counter | Wash your hands | Drink from the tap |
| Casino bar | Order a HENNY (Ð 30) | Chat with the bartender |
| Cashier cage | Cash out | Rattle the cage |
| Gas pump | Pump gas | Punch |
| Drinks cooler | Grab a cold drink (heat) | Punch |
| Shop counter | Buy a hot dog (Ð 3, +2 s) | Ring the bell |
| Doc's chair | Buy cyberware | Look closer |
| Trampoline | Jump on | Look closer |
| A stash | Take it | |
| The ground in front of you | Sit down | Lie down |

**Holding something:** E puts it down where you look (on a flat top), gives it to the person you look at, or throws it
in the bin you look at; otherwise it drops it. G uses it: drink the bottle, bounce the ball, open the propane valve, flip
the coin, wear the cone, rub the gnome, shake the parcel, crumple the salt bag. Click throws it where you look.

**Sitting or lying down:** anything in reach still works (turn the TV off from the couch). Looking at nothing, E gets you
up; moving or jumping always does.

## Comfort

Settings → Comfort has **First-person field of view** (50–95°, top to bottom; 64° by default), **First-person head bob**
(on by default, off if your device asks for reduced motion), and **Your body in first person** (show your arms and legs
when you look down, or hide them). The usual advice is to let players change the field of view and turn off camera bob,
because both can bring on motion sickness: Xbox Accessibility Guideline 117 ([Microsoft](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/117))
and the Game Accessibility Guidelines ([field of view](https://gameaccessibilityguidelines.com/?p=187)). Camera shake
in first person turns the view a little instead of moving it, and the Settings shake slider still scales it.

## How it works

- **The eye** sits at 92% of your height, 12 cm in front of your head, and leans up to 24 cm further forward as you look
  down, the way a head nods, so looking down shows your legs and feet instead of the inside of your shoulders.
- **Your body** is drawn without the head, neck, hat or horns, and the poses that bring a hand to your face (scratching
  your head, drinking, sniffing, pouring, arms up in a jump) are moved down and forward into view.
- **The crosshair pick** casts one ray from the eye: props as rotated boxes, people as upright boxes (or a box around them
  when they're down), Doc, stashes, doorways, and every solid in the 8 m collision cells the ray crosses (walls, windows,
  furniture, machines), plus the ground right in front of you. The nearest hit wins.
- **Seats** hold your feet on the floor and your hips on the seat; the physics capsule steps out of the way so a couch
  doesn't get shoved by the person sitting on it. Lying down turns the body onto its back.
- **Inside buildings** the roof stays on in first person (the third-person view cuts it away to see in).

## What it costs

`tests/perf_fp.py` times update() and render() over 40 frames at the same three spots in each view (software GL on a
4-core cloud VM, so compare the columns, not the absolute numbers):

| Spot | Update, third | Update, first | Render JS, third | Render JS, first |
| --- | --- | --- | --- | --- |
| Street | 2.35 ms | 1.63 ms | 2.28 ms | 2.07 ms |
| Inside a house | 2.19 ms | 2.24 ms | 2.18 ms | 1.89 ms |
| Casino | 1.55 ms | 1.92 ms | 1.90 ms | 2.51 ms |

The two views see different things from different places, so a spot can go either way by about half a millisecond. The
crosshair pick itself costs 0.07 ms a frame with 483 props and 3,414 solids in the town.

## Tests

`tests/feat13.py` runs first person end to end: the eye height and look range; walking, facing, jumping; holding in view;
throwing where you look; tackling; flopping and coming back; the head not drawn; X, scrolling, the 1P button and the
Settings rows; then both verbs on a fresh copy of every one of the 39 prop kinds, held-item verbs, people (talk, shove,
give, help up, pockets), police, a quest giver, Doc, a door, a slot machine, a window, a wall, a condemned wall, 12 pieces
of furniture and machines, a stash, the ground, the couch, using the TV from the couch, and the cone hat. 138 verbs, 0
failures, 0 errors. Pictures of ten scenes are in `screenshots/fp/first_person.jpg` (`tests/shots_fp.py` makes them).
