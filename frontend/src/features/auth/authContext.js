import { createContext, useContext } from "react";

// kept out of auth.jsx so that file only exports components (react fast refresh)
export const AuthContext = createContext(null);

export function useAuth() {
	return useContext(AuthContext);
}
