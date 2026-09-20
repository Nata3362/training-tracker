import { useState } from "react";

import { useAuth } from "./authContext";

export default function AuthForm() {
	const { login, signup } = useAuth();
	const [isSignup, setIsSignup] = useState(false);
	const [name, setName] = useState("");
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [error, setError] = useState(null);
	const [busy, setBusy] = useState(false);

	async function onSubmit(event) {
		event.preventDefault();
		setError(null);
		setBusy(true);
		try {
			if (isSignup) {
				await signup(email, password, name);
			} else {
				await login(email, password);
			}
		} catch (err) {
			setError(err.message);
		} finally {
			setBusy(false);
		}
	}

	return (
		<form id="auth" onSubmit={onSubmit}>
			<h1>{isSignup ? "Create account" : "Sign in"}</h1>

			{isSignup && (
				<label>
					Name
					<input
						value={name}
						onChange={(event) => setName(event.target.value)}
						autoComplete="name"
						required
					/>
				</label>
			)}

			<label>
				Email
				<input
					type="email"
					value={email}
					onChange={(event) => setEmail(event.target.value)}
					autoComplete="email"
					required
				/>
			</label>

			<label>
				Password
				<input
					type="password"
					value={password}
					onChange={(event) => setPassword(event.target.value)}
					autoComplete={isSignup ? "new-password" : "current-password"}
					required
				/>
			</label>

			{error && (
				<p className="error" role="alert">
					{error}
				</p>
			)}

			<button type="submit" disabled={busy}>
				{isSignup ? "Create account" : "Sign in"}
			</button>

			<button
				type="button"
				className="toggle"
				onClick={() => {
					setIsSignup(!isSignup);
					setError(null);
				}}
			>
				{isSignup
					? "Already have an account? Sign in"
					: "Need an account? Sign up"}
			</button>
		</form>
	);
}
