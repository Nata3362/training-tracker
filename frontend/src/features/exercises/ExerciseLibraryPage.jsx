import { useEffect, useMemo, useState } from "react";

import { api } from "../../api";
import ColumnFilter from "./ColumnFilter";

const muscleGroups = [
    ["back", "Back"],
    ["chest", "Chest"],
    ["biceps", "Biceps"],
    ["triceps", "Triceps"],
    ["glutes", "Glutes"],
    ["hamstrings", "Hamstrings"],
    ["calfs", "Calves"],
];

const equipmentOptions = [
    ["dumbell", "Dumbbell"],
    ["barbell", "Barbell"],
    ["bodyweight", "Bodyweight"],
    ["machine", "Machine"],
];

const muscleGroupLabels = Object.fromEntries(muscleGroups);
const equipmentLabels = Object.fromEntries(equipmentOptions);

const emptyForm = {
    name: "",
    muscle_group: "chest",
    equipment: "barbell",
    increment: "1.25",
};

// `editingId` value for the row that creates a new exercise
const NEW = "new";

// A table row of inputs used for both creating and editing an exercise.
// A <form> can't wrap a <tr>, so the inputs join the form in the actions
// cell through the `form` attribute.
function ExerciseFormRow({ values, onChange, onSubmit, onCancel, busy }) {
    function handleKeyDown(event) {
        if (event.key === "Escape") onCancel();
    }

    return (
        <tr className="exercise-editing" onKeyDown={handleKeyDown}>
            <td>
                <input form="exercise-row-form" name="name" aria-label="Name" placeholder="Exercise name" value={values.name} onChange={onChange} required autoFocus />
            </td>
            <td>
                <select form="exercise-row-form" name="muscle_group" aria-label="Muscle group" value={values.muscle_group} onChange={onChange}>
                    {muscleGroups.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
            </td>
            <td>
                <select form="exercise-row-form" name="equipment" aria-label="Equipment" value={values.equipment} onChange={onChange}>
                    {equipmentOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
            </td>
            <td>
                <input form="exercise-row-form" name="increment" aria-label="Weight increment" type="number" min="0" step="0.25" value={values.increment} onChange={onChange} required />
            </td>
            <td className="exercise-actions">
                <form id="exercise-row-form" onSubmit={onSubmit}>
                    <button type="submit" disabled={busy}>{busy ? "Saving..." : "Save"}</button>
                    <button type="button" onClick={onCancel} disabled={busy}>Cancel</button>
                </form>
            </td>
        </tr>
    );
}

function ExerciseLibraryPage() {
    const [exercises, setExercises] = useState([]);
    const [search, setSearch] = useState("");
    const [muscleGroup, setMuscleGroup] = useState("");
    const [equipment, setEquipment] = useState("");
    const [editingId, setEditingId] = useState(null);
    const [form, setForm] = useState(emptyForm);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        api("/exercise/all")
            .then(setExercises)
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    const visibleExercises = useMemo(() => {
        const query = search.trim().toLowerCase();

        return exercises.filter((exercise) => {
            const matchesSearch = exercise.name.toLowerCase().includes(query);
            const matchesMuscle = !muscleGroup || exercise.muscle_group === muscleGroup;
            const matchesEquipment = !equipment || exercise.equipment === equipment;

            return matchesSearch && matchesMuscle && matchesEquipment;
        });
    }, [equipment, exercises, muscleGroup, search]);

    function updateForm(event) {
        const { name, value } = event.target;
        setForm((current) => ({ ...current, [name]: value }));
    }

    function startCreate() {
        setError(null);
        setForm(emptyForm);
        setEditingId(NEW);
    }

    function startEdit(exercise) {
        setError(null);
        setForm({
            name: exercise.name,
            muscle_group: exercise.muscle_group,
            equipment: exercise.equipment,
            increment: String(exercise.increment),
        });
        setEditingId(exercise.id);
    }

    function cancelEdit() {
        setEditingId(null);
    }

    async function saveExercise(event) {
        event.preventDefault();
        setError(null);
        setBusy(true);

        const body = JSON.stringify({
            ...form,
            increment: Number(form.increment),
        });

        try {
            if (editingId === NEW) {
                const created = await api("/exercise/new", { method: "POST", body });
                setExercises((current) => [...current, created]);
            } else {
                const updated = await api(`/exercise/id/${editingId}`, { method: "PATCH", body });
                setExercises((current) => current.map((exercise) => (exercise.id === updated.id ? updated : exercise)));
            }
            setEditingId(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    }

    async function deleteExercise(exercise) {
        if (!window.confirm(`Delete "${exercise.name}"?`)) return;
        setError(null);
        setBusy(true);

        try {
            await api(`/exercise/id/${exercise.id}`, { method: "DELETE" });
            setExercises((current) => current.filter((item) => item.id !== exercise.id));
            if (editingId === exercise.id) setEditingId(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setBusy(false);
        }
    }

    return (
        <main className="exercise-library">
            <header className="page-header">
                <div>
                    <h1>Exercise Library</h1>
                    <p>Browse your exercises and the built-in defaults.</p>
                </div>
            </header>

            <input
                className="exercise-search"
                type="search"
                placeholder="Search exercises"
                aria-label="Search exercises"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
            />

            {error && <p className="error" role="alert">{error}</p>}
            {loading ? <p>Loading exercises...</p> : (
                <div className="exercise-table-wrapper">
                    <table className="exercise-table">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>
                                    <ColumnFilter label="Muscle group" options={muscleGroups} value={muscleGroup} onChange={setMuscleGroup} />
                                </th>
                                <th>
                                    <ColumnFilter label="Equipment" options={equipmentOptions} value={equipment} onChange={setEquipment} />
                                </th>
                                <th>Increment</th>
                                <th className="exercise-actions">
                                    <button
                                        type="button"
                                        className="add-exercise"
                                        aria-label="New exercise"
                                        title="New exercise"
                                        onClick={startCreate}
                                        disabled={busy || editingId === NEW}
                                    >
                                        +
                                    </button>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {editingId === NEW && (
                                <ExerciseFormRow
                                    values={form}
                                    onChange={updateForm}
                                    onSubmit={saveExercise}
                                    onCancel={cancelEdit}
                                    busy={busy}
                                />
                            )}
                            {visibleExercises.map((exercise) => (exercise.id === editingId ? (
                                <ExerciseFormRow
                                    key={exercise.id}
                                    values={form}
                                    onChange={updateForm}
                                    onSubmit={saveExercise}
                                    onCancel={cancelEdit}
                                    busy={busy}
                                />
                            ) : (
                                <tr key={exercise.id}>
                                    <td>{exercise.name}</td>
                                    <td>{muscleGroupLabels[exercise.muscle_group] ?? exercise.muscle_group}</td>
                                    <td>{equipmentLabels[exercise.equipment] ?? exercise.equipment}</td>
                                    <td>{exercise.increment}</td>
                                    <td className="exercise-actions">
                                        {/* Default exercises have no owner and can't be edited or deleted */}
                                        {exercise.person_id && (
                                            <>
                                                <button type="button" onClick={() => startEdit(exercise)} disabled={busy}>Edit</button>
                                                <button type="button" className="danger" onClick={() => deleteExercise(exercise)} disabled={busy}>Delete</button>
                                            </>
                                        )}
                                    </td>
                                </tr>
                            )))}
                            {!visibleExercises.length && editingId !== NEW && (
                                <tr>
                                    <td className="exercise-empty" colSpan={5}>No exercises match your filters.</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </main>
    );
}

export default ExerciseLibraryPage;
