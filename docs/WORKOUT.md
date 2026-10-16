# Workouts

How performed workouts are stored and saved, and the decisions behind the
design. The code lives in `backend/app/workout/`.

## Status

| Part | State |
| --- | --- |
| Tables `workout`, `workout_exercise`, `workout_set`, `target` | Built (migration `216907578762`) |
| Template tables `workout_template`, `exercise_in_workout_template`, and `workout.template_id` | Built (migration `7880c2e946ea`) |
| `POST /workout/new`: save a whole performed workout | Built and tested |
| Read and delete workouts (`GET /workout/all`, `GET /workout/id/{id}`, `DELETE`) | Planned |
| Target routes (`/target/*`) | Planned; the router exists but has no routes |
| Template routes (`/template/*`) and loading a template into the form | Planned |
| Saving continuously during a workout | Planned (version 2) |
| Progression: raising targets after a workout | Planned |
| Frontend | Planned |

## Data model

```text
people
 ├─ target                          current goal per exercise: weight, reps_low, reps_high
 │
 ├─ workout_template                a reusable plan: name
 │   └─ exercise_in_workout_template   an exercise in the plan: exercise_id, position, number_of_sets
 │
 └─ workout                         one performed session: name, date, status, template_id
     └─ workout_exercise            an exercise in that session: exercise_id, position
         └─ workout_set             one set: set_number, target_* (copied), performed_*
```

Each table holds one kind of thing, so nothing is stored twice:

- **`workout`** holds facts about the session: who, when, its name, and
  optionally the template it was started from.
- **`workout_exercise`** links a workout to the exercises in it (a
  many-to-many relationship) and keeps their order in `position`. The same
  exercise may appear more than once, at different positions.
- **`workout_set`** holds one row per set, so the number of sets can vary
  without schema changes.
- **`target`** holds the person's *current* goal for an exercise. It is not
  part of any workout. It can't live on the exercise itself, because default
  exercises are shared by every user while a target belongs to one person.
- **`workout_template`** and **`exercise_in_workout_template`** hold plans.
  A plan has no sets of its own: `number_of_sets` says how many empty set
  rows to create when the template is loaded.

Constraints:

- `target`: unique (`person_id`, `exercise_id`). A person has at most one
  target per exercise.
- `workout_exercise`: unique (`workout_id`, `position`).
- `workout_set`: unique (`workout_exercise_id`, `set_number`). Set numbers
  repeat across exercises but not within one.
- `workout_template`: unique (`person_id`, `name`). One person can't have two
  templates with the same name, but two people can. Workout names are not
  unique, because the same session is repeated.
- `exercise_in_workout_template`: unique (`template_id`, `position`).

On delete:

- Deleting a workout cascades to its exercises and sets. Deleting a template
  cascades to its exercises. Deleting a person cascades to their workouts,
  templates and targets.
- `workout_exercise.exercise_id` has no `ondelete`, so Postgres refuses to
  delete an exercise that appears in a saved workout. That protects history.
- `exercise_in_workout_template.exercise_id` cascades: deleting an exercise
  removes it from templates, because a plan isn't history.
- `workout.template_id` is set to `NULL` when its template is deleted, so the
  workouts survive.

The ORM relationships `Workout.exercises`, `WorkoutExercise.sets` and
`WorkoutTemplate.exercises` are ordered by `position` and `set_number`, and
cascade saves and deletes from parent to child.

### Constraint names

Every foreign key is named explicitly with the Postgres pattern
`<table>_<column>_fkey`, for example `workout_template_id_fkey`. These are the
names Postgres gave the foreign keys it created itself, so the model and the
database agree. A named constraint is needed for a migration's `downgrade()`
to drop it; autogenerate writes `None` for an unnamed one, which can't be
dropped. Unique constraints are named in the models too (`uq_...`).

## Design decisions

### Targets are copied into sets

When a workout is saved, the backend looks up the person's target for each
exercise and copies its three values into every set's `target_weight`,
`target_reps_high` and `target_reps_low`. The set stores the values, not a
reference to the target.

Changing a target later therefore never changes past workouts: each set keeps
the goal that applied on the day. If the person has no target for an
exercise, the `target_*` columns are `NULL`.

The client never sends target values. The backend fills them in, so the copy
step lives in one place and can't be faked.

### Workout status

`workout.status` is `completed` or `in_progress`. Version 1 only saves whole
workouts, so every row is `completed` (the column default). The
`in_progress` value is there for version 2, so history queries can filter on
`completed` from the start.

### The date is the user's local time

`workout.date` stores the wall-clock time the user experienced, for example
"18:30 on 14 October". The column has no timezone and no server default,
because the server can't know the user's timezone. A default of "now in UTC"
would put late-evening workouts on the wrong day for users east of UTC.

The client must send `date` (the API returns `422` without it), as local time
without `Z` or an offset: `"2026-10-14T18:30:00"`. In JavaScript,
`new Date().toISOString()` returns UTC and is wrong here. An
`<input type="datetime-local">` returns the correct format.

### Plans are templates, separate from performed workouts

Planned workouts are reusable templates in their own tables
(`workout_template`, `exercise_in_workout_template`), not rows in `workout`.
Templates therefore never appear in history, and editing a template doesn't
change past workouts.

The intended flow: the user picks a template from a list, the frontend loads
it into the workout form with `number_of_sets` empty rows per exercise, the
user fills it in, and it is saved with `POST /workout/new` like any other
workout. The backend copies targets in at save time, as usual.

`workout.template_id` records which template a workout came from, and is
`NULL` for a workout logged without one. Workouts started from a template
also carry its name, so they can be counted by name too.

## Saving a workout (version 1)

The frontend keeps the workout in memory while the user fills it in, and
sends the whole tree in one request when they save.

`POST /workout/new` (requires a session):

```json
{
  "name": "Push day",
  "date": "2026-10-14T18:30:00",
  "exercises": [
    {
      "exercise_id": "8f1c7350-d2fc-4794-9e79-fa2d83c994db",
      "position": 1,
      "sets": [
        { "set_number": 1, "performed_weight": 60, "performed_reps": 8 },
        { "set_number": 2, "performed_weight": 60, "performed_reps": 7 }
      ]
    }
  ]
}
```

The backend:

1. Creates the `Workout` for the signed-in person.
2. For each exercise, checks that the person may use it (their own or a
   default exercise), then creates a `WorkoutExercise`.
3. Looks up the person's target for that exercise once, and creates each
   `WorkoutSet` with the target values copied in.
4. Adds the workout and commits once. Because of the relationship cascades,
   the exercises and sets are saved with it. The request either saves the
   whole tree or nothing.

It returns `201` with the saved workout as `WorkoutDetail`: the workout with
its exercises and their sets, including the new IDs and the copied target
values.

| Status | When |
| --- | --- |
| `401` | Not signed in |
| `404` `Exercise not found` | An `exercise_id` doesn't exist or belongs to another person |
| `422` | The body doesn't match the schema: a missing `name`, `date` or `exercises`, an invalid UUID, two exercises with the same `position`, or two sets in one exercise with the same `set_number` |
| `409` | The database rejected the workout. The checks above should prevent this; it covers rare races, such as an exercise deleted while the request runs |

### Where each rule is checked

- **The schema** checks everything visible in the request itself, including
  that positions and set numbers are unique (`field_validator`s on
  `WorkoutCreate` and `WorkoutExerciseCreate`). These fail with `422` before
  anything touches the database.
- **The route** checks what needs the database or the person: whether each
  exercise exists and may be used (`404`).
- **The database constraints** stay as a safety net, so bad data can't be
  stored even by code that skips the schema. The route catches
  `IntegrityError` and returns `409` instead of a `500`.

The frontend derives `position` and `set_number` from the order of the rows
(index + 1), so a normal user never triggers the `422`s.

The frontend should keep a draft in `localStorage` while the user fills in
the form, and clear it after a successful save, so a closed tab doesn't lose
the workout.

## Schemas

Each resource has one schema per direction, in `app/workout/schemas.py`:

- **Create** schemas describe what the client may send. None of them contains
  `person_id`; the person always comes from the session.
- **Update** schemas have every field optional.
- **Response** schemas describe what the API returns. `WorkoutResponse` is the
  light version for lists (no exercises). `WorkoutDetail` adds the nested
  exercises and sets for a single workout.

## Version 2: saving during the workout

Planned additions, none of which change the existing tables or routes. If
two exercises' positions are swapped during a workout, the unique
(`workout_id`, `position`) constraint means the update has to avoid a
moment where both rows have the same position.

- `POST /template/id/{id}/start` copies a template into a new workout with
  status `in_progress`.
- `PATCH /workout/exercise/{id}/sets` saves one exercise's sets. The frontend
  calls it when the user moves to the next exercise or pauses, and updates
  the screen without waiting for the response.
- `POST /workout/id/{id}/finish` saves what remains and sets the status to
  `completed`. This is also where progression will raise targets by
  `exercise.increment`.

`POST /workout/new` stays, for logging a workout afterwards.

## Tests

`backend/tests/test_workout.py` covers saving a workout:

- the happy path: the response tree, the rows in each table, the copied
  target values (and `NULL` for an exercise without a target), and that no
  targets are created
- rejected requests: duplicate set numbers, duplicate positions, another
  person's exercise, no session, and a missing required field
  (parametrized over `name`, `date` and `exercises`)
- two workouts with the same set numbers can both be saved

Every rejected request also checks that no workout was saved, which proves
the request is all-or-nothing. The `422` tests check the error message, so
they can't pass because of some other validation error.

The tests build their schema from the models in in-memory SQLite, not from
the migrations. Shared fixtures (`create_other_person`, `setup_exercises`)
are in `tests/conftest.py`.
