import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
	plugins: [react()],
	base: "/",
	// vite preview serves the built app on Railway. Since Vite 6 it rejects any
	// request whose Host header isn't listed here, so the custom domain must be
	// named or the deployed site answers every request with "Blocked request".
	// A leading dot covers the apex and every subdomain of it.
	preview: {
		allowedHosts: ['.natoli.dk'],
	},
})
