# Architecture: from Sheet to webapp

Target stack: **Python (FastAPI) + PostgreSQL via SQLAlchemy** for the
backend/data layer; the frontend framework is left open (see
[Views](#4-view-layer) — a plain server-rendered page works fine for two
users and keeps a phone-first app close by later).

No database exists yet — this is still a design, not a running schema. The
models below are what gets created from scratch, not a migration path, so
there's nothing here about altering existing tables.

This document maps the current Apps Script prototype (`Code.gs`, described in
full in [README.md](README.md) see old folder) onto four layers — **Data → Domain → API →
View** — so each Sheets tab lands in the right place instead of getting
ported 1:1. The prototype conflates view and database in several tabs
precisely because Sheets has no other layer to put UI logic in; a webapp
does, so those tabs get split.

---

## 1. Why four layers, not the Sheet's tabs

A Sheets tab is forced to be storage, query, *and* UI at once — a cell is
simultaneously a database field and a rendered pixel. A webapp doesn't have
that constraint, so:

- **Data layer** — Postgres tables. Only facts get stored here. No formulas,
  no rendering concerns.
- **Domain layer** — plain Python functions with the business rules
  (progression, target resolution, session-save). This is the direct
  successor to `Code.gs`'s non-UI functions (`targetFor`, `updateTargets`,
  `saveSession`'s data half). Pure, testable, no HTTP or SQL leaking in.
- **API layer** — FastAPI routes that call the domain layer and return JSON.
  This is the seam a future mobile app reuses without change.
- **View layer** — pages/components that call the API. Nothing in this layer
  touches Postgres directly.

Rule: a view never queries the database, and a table never contains a
formula. Every "mixed" tab below gets split along that line.

---

## 2. Tab-by-tab: what's data, what's view

| Tab | Verdict | Split |
| --- | --- | --- |
| `People` | **Data** | Straight table. The `+ PERSON` checkbox was a UI trigger for tab-scaffolding side effects (`buildTodayFor`, `buildMyLog`, `seedTargets`) that only exist because Sheets needs one physical tab per person. A webapp has one `/today` view parameterized by logged-in user — **no scaffolding step at all**. `ponytail: this is a case where the target architecture is strictly simpler than the prototype, not just a port.` |
| `Exercises` | **Data** | Straight table, including `SUB 1`/`SUB 2`. |
| `Plans` | **Data** | Straight table (`plan_exercises`). Also fixes prototype limitation #1 (README): keying `plan_exercises` by `(plan, day, exercise)` instead of `exercise` alone removes the "wrong rep range when a lift appears on two days" bug for free. |
| `Targets` | **Data** | Straight table. Add a `hold` boolean column — this closes prototype limitation #2 (no deload-hold flag) at schema time instead of remaining a known gap. |
| `Log` | **Mixed → split** | Raw facts (`date, person, exercise, planned_as, set, type, tgt_*, kg, reps, rir, note`) are the **data**. `VOLUME`, `e1RM`, `%1RM` are **spreadsheet formulas standing in for a view-time computation** — they get recomputed by the domain layer (or a SQL view) whenever read, not stored as columns. Nothing here needs a session table beyond a `session_id` computed the same way (`date + person`), unless you later want to edit/delete a whole session as a unit — flagged as an open question below. |
| `Targets` update logic | **Domain** | `updateTargets()` — stays exactly what it is, just as a Python function instead of a `.gs` function. |
| `Today — <name>` | **Mixed → split, this is the big one** | The sheet is doing three jobs at once: (a) **read composition** — join `Plans + Targets + Exercises + People` into a workout (`loadWorkout()`); (b) **draft/staging state** — the hidden `M_*` columns hold in-progress edits (added sets, swapped exercises) before commit; (c) **write** — `saveSession()` flushes the draft into `Log` and calls the domain layer. In the webapp: (a) becomes a `GET /workouts/today` API call, (b) becomes **client-side component state** (no backend table — a browser tab already gives per-person isolation that the prototype needed a whole physical sheet to fake), (c) becomes `POST /sessions`. `ponytail: the hidden meta columns were a workaround for Sheets having no client state; a real frontend gets that for free, so this whole mechanism disappears rather than needing a port.` |
| `My Log — <name>` | **View** | Was a stored `FILTER()` formula; becomes `GET /log?person=` + a list component. No table. |
| `History` | **View** | Parameterized query (person, exercise) over `Log` + `Targets`. `GET /history?person=&exercise=` + a component. No table. |
| `PRs` | **View** | Aggregate (`MAX` per person/exercise) over `Log`. `GET /prs` + a component. No table — a materialized view or cache is an optimization, not a v1 need for two users' data volume. |
| `Charts` | **View** | Two pivot queries over `Log`/`Exercises`. `GET /charts/volume` etc. + a client chart library. No table. |

Net effect: **5 real tables** (`people`, `exercises`, `plan_exercises`,
`targets`, `log_sets`), everything else is either domain logic or a read-only
view backed by a query.

---

## 3. Data layer — proposed schema

SQLAlchemy 2.0-style declarative models — this is the target schema, created
fresh (`Base.metadata.create_all()` or a first Alembic revision once the
project's ready for that), not a migration against something that already
exists.

```python
from datetime import date, datetime
from sqlalchemy import ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Person(Base):
    __tablename__ = "people"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str] = mapped_column()
    bodyweight_kg: Mapped[float | None]
    current_plan: Mapped[str | None]
    default_rir: Mapped[int | None]
    unit: Mapped[str] = mapped_column(default="kg")


class Exercise(Base):
    __tablename__ = "exercises"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    muscle: Mapped[str | None]
    type: Mapped[str | None]
    bodyweight: Mapped[bool] = mapped_column(default=False)
    increment_kg: Mapped[float] = mapped_column(default=2.5)
    sub_1_id: Mapped[int | None] = mapped_column(ForeignKey("exercises.id"))
    sub_2_id: Mapped[int | None] = mapped_column(ForeignKey("exercises.id"))


class PlanExercise(Base):
    __tablename__ = "plan_exercises"
    __table_args__ = (UniqueConstraint("plan", "day", "exercise_id"),)  # fixes prototype limitation #1

    id: Mapped[int] = mapped_column(primary_key=True)
    plan: Mapped[str]
    day: Mapped[str]
    ord: Mapped[int]
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    sets: Mapped[int]
    seed_kg: Mapped[float | None]
    rep_lo: Mapped[int | None]
    rep_hi: Mapped[int | None]
    rir: Mapped[int | None]
    note: Mapped[str | None]


class Target(Base):
    __tablename__ = "targets"
    __table_args__ = (UniqueConstraint("person_id", "exercise_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    tgt_kg: Mapped[float | None]
    rep_lo: Mapped[int | None]
    rep_hi: Mapped[int | None]
    hold: Mapped[bool] = mapped_column(default=False)  # fixes prototype limitation #2
    updated_at: Mapped[date | None]
    note: Mapped[str | None]


class LogSet(Base):
    __tablename__ = "log_sets"
    __table_args__ = (CheckConstraint("type IN ('W','U','D','A','X')"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date]
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    session_id: Mapped[str]              # date + person, same scheme as prototype
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    planned_as_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    set_number: Mapped[int]
    type: Mapped[str]
    tgt_kg: Mapped[float | None]
    tgt_lo: Mapped[int | None]
    tgt_hi: Mapped[int | None]
    kg: Mapped[float]
    reps: Mapped[int]
    rir: Mapped[int | None]
    note: Mapped[str | None]
```

`Person.user_id` is the one field [AUTH.md](AUTH.md) adds — it's on the model
from the start here, not bolted on later.

`log_sets` is append-only, same invariant as the prototype's `Log`: nothing
ever updates a row, `saveSession` only inserts (or deletes-and-reinserts a
whole `session_id` on confirmed replace, matching current behaviour).

No `volume`, `e1rm`, `pct_1rm` columns — see below.

---

## 4. Domain layer

Direct successors of the non-UI functions in `Code.gs`, as plain functions
(`app/domain/*.py`), unit-testable without a DB or HTTP client:

| `Code.gs` function | Domain function | Notes |
| --- | --- | --- |
| `targetFor()` | `resolve_target(person, exercise, plan_row)` | Same fallback chain: target row → plan seed. |
| `updateTargets()` | `apply_progression(person, sets)` | Same rule: max kg of working sets, +increment if every set topped `rep_hi`. Now also skips update when `targets.hold` is true. |
| `logFormulas()` (the O/P/Q formulas) | `compute_volume(set)`, `compute_e1rm(set, bodyweight)`, `compute_pct_1rm(set, best_e1rm)` | Called at read time (or cached) instead of stored. Epley formula, bodyweight addition — logic unchanged. |
| `saveSession()` | `save_session(person, date, draft_rows)` | Builds `log_sets` rows from the client-submitted draft, calls `apply_progression`. Session-exists confirm/replace becomes a 409 the API surfaces to the frontend, not a `ui.alert`. |
| `swapExercise()` | pure frontend state change | No backend involvement until save — the domain layer only ever sees the final `exercise` vs `planned_as` on each submitted row. |
| `planRows()`, `getPeople()`, `exerciseRow()` etc. | plain repository queries | Thin, boring, not really "domain" — just reads. |

---

## 5. API layer (FastAPI)

```
GET  /people
GET  /exercises
GET  /plans/{plan}/{day}
GET  /targets?person=
GET  /workouts/today?person=&day=        # loadWorkout() composition
POST /sessions                            # saveSession()
GET  /log?person=                         # My Log
GET  /history?person=&exercise=
GET  /prs
GET  /charts/volume-by-week
GET  /charts/volume-by-muscle
```

Each returns JSON; each is a thin wrapper calling one domain/repository
function. This is the reuse seam for a later mobile app — it talks to the
same endpoints, no new backend work.

---

## 6. View layer

Screens, mapped from the tabs that turned out to be pure view:

- **Today** (`workouts/today`) — one page, current logged-in person implicit.
  Draft state (added sets, swapped exercises, notes) lives in the frontend
  only until "Save session" posts it. This replaces the hidden `M_*` columns
  entirely.
- **My Log**, **History**, **PRs**, **Charts** — each a page bound to one
  `GET` endpoint above. Charts need a client-side chart library (Chart.js or
  similar) — the prototype's manual `Insert > Chart` step goes away for
  free once the aggregation is server-side.

Framework: not decided — you picked Python/Postgres for the backend, not a
frontend framework. For two users and mobile-first logging, a
server-rendered page (Jinja2 + a sprinkle of HTMX/vanilla JS for the
add-set/swap interactions) is the lazy option: no build step, no SPA
state-management library, and it's the smallest thing that satisfies
"mobile primary, desktop for planning." A full SPA (React/Vue) is the
upgrade if the "later, an app" turns into a shared component layer with a
future native app.
`ponytail: recommending server-rendered + HTMX over a SPA framework; upgrade to a SPA if you end up sharing view logic with a native app.`

---

## 7. First steps, in order

1. SQLAlchemy models above (`Person`, `Exercise`, `PlanExercise`, `Target`,
   `LogSet`), `Base.metadata.create_all()` against a fresh Postgres instance,
   + seed data ported from `Exercises`/`Plans` starters in `Code.gs`.
2. Domain functions (`resolve_target`, `apply_progression`, the three
   compute functions) with the self-check tests the logic deserves — these
   carry the two known-limitation fixes (plan+day+exercise keying, `hold`
   flag), worth a test each.
3. Read endpoints (`/people`, `/exercises`, `/workouts/today`) — enough to
   render Today.
4. `POST /sessions` + the Today page's draft/save flow.
5. `My Log`, `History`, `PRs`, `Charts` — same shape repeated four times,
   last because they're the least novel.

---

## 8. Open questions

- **Auth.** Two named users, no login in the prototype (tab = identity).
  The webapp needs *some* way to know who's logging — even HTTP basic auth
  or a hardcoded person-picker is enough for two people; say if you want
  more than that.
- **Session as an entity.** Prototype derives `session_id` from
  `date + person initials` and treats it as a string, not a table. Proposed
  schema keeps that. If you want to rename/delete/annotate a whole session
  later, a real `sessions` table is a small addition — flag if that's coming
  soon so it's in the schema from day one instead of a migration later.
- **Stored vs computed `volume`/`e1rm`/`%1rm`.** Proposed as computed-at-read
  (SQL view or domain function). Fine at this data volume; only worth
  denormalizing into real columns if `PRs`/`Charts` queries get slow.
