# Workout Tracker — build it in Google Sheets

Ten minutes, once.

## 1. Create the sheet
1. Go to <https://sheets.new> — a blank spreadsheet.
2. Name it, e.g. *Workout Tracker*.

## 2. Paste the build script
1. **Extensions → Apps Script**.
2. Delete whatever is in `Code.gs`.
3. Paste the whole contents of `Code.gs` from this folder.
4. Save (⌘S / Ctrl-S).

## 3. Run it
1. In the function dropdown at the top, choose **`setup`**, press **Run**.
2. Google asks for permission the first time — *Review permissions → your account →
   Advanced → Go to (unsafe) → Allow*. It's your own script editing your own sheet.
3. About 30 seconds. You'll get an alert when it's done.

Tabs built: **Today — Oliver**, **Today — Natasja**, **Log**, **Targets**, **Plans**,
**Exercises**, **People**, **History**, **PRs**, **Charts**, plus a read-only
**My Log —** per person.

## How the pieces fit

| Tab | Holds | Shared? |
| --- | --- | --- |
| `Plans` | structure — exercise, set count, rep range, RIR, a seed weight | shared |
| `Targets` | the working weight per person per exercise, + rep-range overrides | per person |
| `Today — name` | the session you're logging right now | per person |
| `Log` | one row per set, forever | one table, Person column |

**Plans holds no real weights.** Two people run the same structure at different
loads: the weight comes from their own `Targets` row. The plan's `SEED KG` is only
used the first time, before anyone has a target.

**Targets maintains itself.** `SAVE SESSION` writes each exercise's next working
weight: the heaviest working set you did, plus one increment if *every* working set
reached the top of the rep range. Edit the cell by hand any time — a deload, coming
back from injury — and the next session picks up your number.

**Rep ranges are shared** via the plan. Fill in `REP LO` / `REP HI` on someone's
`Targets` row only when theirs should differ.

**Two people, at once.** Each person logs on their own `Today — name` tab, so you
can both type during the same session without touching each other's cells. The tab
*is* the person — no person dropdown to get wrong.

## Using it
- **Today — you** — pick the workout, tick **LOAD WORKOUT**. Grey line is your
  target, white line under it is what you did. Type kg and reps into the white line.
- **+ column** — tick the `+` on an exercise title to add a set; tick it on a set row
  to add a **drop set** (`↳`) under that set.
- **Swap** — tap the exercise title and pick from the dropdown: that lift's two
  declared substitutes first, then the library. The Log keeps `PLANNED AS` on the
  original, so the substitute builds its own history and the original's PRs stay
  clean. `SUB 1` / `SUB 2` in **Exercises** are dropdowns too — no mis-spelling.
- **SAVE SESSION** — appends every filled row to `Log`, stamps the targets as values,
  updates `Targets`. Ticking twice asks before replacing.
- **People** — add a row, tick **+ PERSON**: builds their Today and My Log tabs,
  seeds their targets from the plan, extends PRs.

### Why checkboxes instead of buttons
The Google Sheets **mobile app runs neither menus nor drawing buttons** — only cell
edits fire scripts. So every action is a checkbox that runs and unticks itself. It
all works one-handed on a phone.

## Charts (30 seconds, manual)
Apps Script can't reliably place charts: **Charts** tab → select the `week` block →
Insert → Chart → line chart. Same for the muscle block with a column chart.

## Notes

### Filtering
`Log`, `Targets`, `Plans` and `Exercises` get filter dropdowns on their header rows
(**Workout → Add column filters** if they're missing) — filter `Targets` to one person,
`Plans` to one program, `Log` to one exercise.

A basic filter is **shared**: if you filter, the other person sees it filtered too. For
filtering only you can see, use **Data → Create filter view** — make it once, it's saved
and named. The `My Log — name` tabs are already permanently filtered per person.

### Parse errors / locale
Danish (and most non-US) locales separate formula arguments with `;` and array
columns with `\`, and use `,` as the decimal point. The script detects this and
writes formulas in your sheet's dialect. If anything shows a parse error:
**Workout → Fix formulas**. It rewrites every formula and touches no logged data.

Re-running `setup()` is safe for your history — it will not wipe a `Log` that has
rows — but it *does* reset `Plans` and `Exercises` to the starters. Use the three
`Fix…` menu items for repairs instead.

- Set types in `Log`: `W` working · `U` warmup (no volume, no PRs) · `D` drop ·
  `A` AMRAP · `X` skipped.
- Progression is per exercise: `INCREMENT KG` in **Exercises**.
- e1RM is Epley, with bodyweight added for lifts flagged `Bodyweight? = Y`.
- `Plans` is never written to by logging. Permanent structural changes are edited
  there by hand, on desktop.
