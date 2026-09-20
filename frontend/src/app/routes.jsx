import { Navigate, Route, Routes } from "react-router-dom";
import AuthForm from "../features/auth/AuthForm";
import { useAuth } from "../features/auth/authContext";
import AppLayout from "./AppLayout";
import HomePage from "./HomePage";
import ExerciseLibraryPage from "../features/exercises/ExerciseLibraryPage";
import CreateWorkoutPage from "../features/exercises/CreateWorkoutPage";
import PerformWorkoutPage from "../features/exercises/PerformWorkoutPage";

export default function AppRoutes() {
    const { user, loading } = useAuth();

    if (loading) return null;

    return (
        <Routes>
            <Route
                path="/login"
                element={
                    user ? <Navigate to="/" replace /> : <AuthForm />
                }
            />

            <Route element={
                user ? ( <AppLayout /> ) : ( <Navigate to="/login" replace /> ) } >
                <Route path="/" element={<HomePage />} />
                <Route path="/exerciselibrary" element={<ExerciseLibraryPage />} />
                <Route path="/createworkout" element={<CreateWorkoutPage />} />
                <Route path="/performworkout" element={<PerformWorkoutPage />} />
            </Route>

            <Route
                path="*"
                element={<Navigate to={user ? "/" : "/login"} replace />}
            />
        </Routes>
    );
}