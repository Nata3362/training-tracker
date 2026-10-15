# Workouts

How performed workouts are stored and saved, and the decisions behind the
design. The code lives in `backend/app/workout/`.

## Status

| Part | State |
| --- | --- |
| Tables `workout`, `workout_exercise`, `workout_set`, `target` | Built (migration `216907578762`) |
| `POST /workout/new`: save a whole performed workout | Built and tested |
| Read and delete workouts (`GET /workout/all`, `GET /workout/id/{id}`, `DELETE`) | Planned |
| Target routes (`/target/*`) | Planned; the router exists but has no routes |
| Workout templates (plans) | Planned |
| Saving continuously during a workout | Planned (version 2) |
| Progression: raising targets after a workout | Planned |
| Frontend | Planned |

## Data model

```text
people
 ├─ target                   current goal per exercise: weight, reps_low, reps_high
 │
 └─ workout                  one performed session: name, date, status
     └─ workout_exercise     an exercise in that session: exercise_id, position
         └─ workout_set      one set: set_number, target_* (copied), performed_*
```

Each table holds one kind of thing, so nothing is stored twice:

- **`workout`** holds facts about the session: who, when, and its name.
- **`workout_exercise`** links a workout to the exercises in it (a
  many-to-many relationship) and keeps their order in `position`.
- **`workout_set`** holds one row per set, so the number of sets can vary
  without schema changes.
- **`target`** holds the person's *current* goal for an exercise. It is not
  part of any workout.

Constraints:

- `target`: unique (`person_id`, `exercise_id`). A person has at most one
  target per exercise.
- `workout_set`: unique (`workout_exercise_id`, `set_number`). Set numbers
  repeat across exercises but not within one.
- Deleting a workout cascades to its exercises and sets. Deleting a person
  cascades to their workouts and targets.
- `workout_exercise.exercise_id` has no `ondelete`, so Postgres refuses to
  delete an exercise that appears in a saved workout. That protects history.

The ORM relationships `Workout.exercises` and `WorkoutExercise.sets` are
ordered by `position` and `set_number`, and cascade saves and deletes from
parent to child.

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

Planned workouts will be reusable templates in their own tables
(`workout_template`, `template_exercise`), not rows in `workout`. Starting a
workout from a template copies it into the workout tables. Templates
therefore never appear in history, and editing a template doesn't change past
workouts.

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
| `400` `duplicate of set number` | Two sets in one exercise have the same `set_number` |
| `422` | The body doesn't match the schema, for example a missing `date` or an invalid UUID |

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

Planned additions, none of which change the existing tables or routes:

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

`backend/tests/test_workout.py` covers saving a workout: the response tree,
the rows in each table, the copied target values (and `NULL` for an exercise
without a target), and that no targets are created. Shared fixtures
(`create_other_person`, `setup_exercises`) are in `tests/conftest.py`.
