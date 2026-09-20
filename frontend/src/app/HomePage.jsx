import { useAuth } from "../features/auth/authContext";

function HomePage() {
    const { user } = useAuth();

    return (
        <main id="center">
            <h1>Training Tracker</h1>
            <p>Signed in as {user.name ?? user.email}</p>
        </main>
    );
}

export default HomePage;