import { useEffect, useState } from "react";

import { api } from "./api";
import { AuthContext } from "./authContext";

export function AuthProvider({ children }) {
	const [user, setUser] = useState(null);
	const [loading, setLoading] = useState(true);

	// the session cookie is httponly, so asking the backend is the only way to
	// find out whether we're logged in
	useEffect(() => {
		api("/user")
			.then(setUser)
			.catch(() => setUser(null))
			.finally(() => setLoading(false));
	}, []);

	async function signup(email, password, name) {
		await api("/auth/signup", {
			method: "POST",
			body: JSON.stringify({ email, password, name }),
		});
		setUser(await api("/user"));
	}

	async function login(email, password) {
		await api("/auth/login", {
			method: "POST",
			body: JSON.stringify({ email, password }),
		});
		setUser(await api("/user"));
	}

	async function logout() {
		await api("/auth/logout", { method: "POST" });
		setUser(null);
	}

	const value = { user, loading, signup, login, logout };
	return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
