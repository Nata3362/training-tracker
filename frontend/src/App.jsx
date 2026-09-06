import "./App.css";

import AuthForm from "./AuthForm";
import { useAuth } from "./authContext";

function App() {
	const { user, loading, logout } = useAuth();

	if (loading) return null;
	if (!user) return <AuthForm />;

	return (
		<div id="center">
			<h1>Training Tracker</h1>
			<p>Signed in as {user.name ?? user.email}</p>
			<button onClick={logout}>Log out</button>
		</div>
	);
}

export default App;
