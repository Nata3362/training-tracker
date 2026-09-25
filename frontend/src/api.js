const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// FastAPI puts a plain string in `detail` for our own HTTPException(...) calls,
// but a list of {msg, loc, ...} objects for its own request validation errors
// (e.g. a malformed email rejected by Pydantic's EmailStr) — those messages are
// written for API debugging, not end users, so show one generic line instead.
function errorMessage(detail, status) {
	if (typeof detail === "string") return detail;
	if (Array.isArray(detail)) return "An error occurred";
	return `Request failed (${status})`;
}

export async function api(path, options = {}) {
	const resp = await fetch(BASE + path, {
		// required for the browser to send/store the session cookie cross-origin
		credentials: "include",
		headers: { "Content-Type": "application/json" },
		...options,
	});

	if (!resp.ok) {
		const body = await resp.json().catch(() => ({}));
		throw new Error(errorMessage(body.detail, resp.status));
	}

	// 204 No Content (e.g. DELETE) has no body to parse
	if (resp.status === 204) return null;

	return resp.json();
}
