import { useEffect, useMemo, useState } from "react";

import { api } from "../../api";

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

const emptyForm = {
    name: "",
    muscle_group: "chest",
    equipment: "barbell",
    increment: "1.25",
};

function ExerciseLibraryPage() {
    const [exercises, setExercises] = useState([]);
    const [search, setSearch] = useState("");
    const [muscleGroup, setMuscleGroup] = useState("");
    const [equipment, setEquipment] = useState("");
    const [form, setForm] = useState(emptyForm);
    const [showForm, setShowForm] = useState(false);
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

    async function createExercise(event) {
        event.preventDefault();
        setError(null);
        setBusy(true);

        try {
            const created = await api("/exercise/new", {
                method: "POST",
                body: JSON.stringify({
                    ...form,
                    increment: Number(form.increment),
                }),
            });
            setExercises((current) => [...current, created]);
            setForm(emptyForm);
            setShowForm(false);
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
                <button type="button" onClick={() => setShowForm((current) => !current)}>
                    {showForm ? "Cancel" : "New exercise"}
                </button>
            </header>

            {showForm && (
                <form className="exercise-form" onSubmit={createExercise}>
                    <h2>Create exercise</h2>
                    <label>
                        Name
                        <input name="name" value={form.name} onChange={updateForm} required />
                    </label>
                    <label>
                        Muscle group
                        <select name="muscle_group" value={form.muscle_group} onChange={updateForm}>
                            {muscleGroups.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                        </select>
                    </label>
                    <label>
                        Equipment
                        <select name="equipment" value={form.equipment} onChange={updateForm}>
                            {equipmentOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                        </select>
                    </label>
                    <label>
                        Weight increment
                        <input name="increment" type="number" min="0" step="0.25" value={form.increment} onChange={updateForm} required />
                    </label>
                    <button type="submit" disabled={busy}>{busy ? "Creating..." : "Create exercise"}</button>
                </form>
            )}

            <section className="exercise-controls" aria-label="Exercise filters">
                <input
                    type="search"
                    placeholder="Search exercises"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                />
                <select value={muscleGroup} onChange={(event) => setMuscleGroup(event.target.value)}>
                    <option value="">All muscle groups</option>
                    {muscleGroups.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
                <select value={equipment} onChange={(event) => setEquipment(event.target.value)}>
                    <option value="">All equipment</option>
                    {equipmentOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
            </section>

            {error && <p className="error" role="alert">{error}</p>}
            {loading ? <p>Loading exercises...</p> : (
                <section className="exercise-grid">
                    {visibleExercises.map((exercise) => (
                        <article className="exercise-card" key={exercise.id}>
                            <h2>{exercise.name}</h2>
                            <p>{exercise.muscle_group} · {exercise.equipment}</p>
                            <small>Increment: {exercise.increment}</small>
                        </article>
                    ))}
                    {!visibleExercises.length && <p>No exercises match your filters.</p>}
                </section>
            )}
        </main>
    );
}

export default ExerciseLibraryPage;