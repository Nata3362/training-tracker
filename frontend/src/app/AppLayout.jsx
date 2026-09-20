import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../features/auth/authContext";

function AppLayout() {
    const { user } = useAuth();

    const { logout } = useAuth();

    return (
        <>
            <nav className="navbar">
                <div className="navbar-links">
                    <NavLink to="/" className="navbar-brand">
                        Training Tracker
                    </NavLink>

                    <NavLink to="/exerciselibrary">
                        Exercise Library
                    </NavLink>

                    <NavLink to="/createworkout">
                        Create Workout
                    </NavLink>

                    <NavLink to="/performworkout">
                        Perform Workout
                    </NavLink>
                </div>


                <div className="navbar-account">
                    <p>Signed in as {user.name ?? user.email}</p>

                    <button type="button" onClick={logout}>
                        Log out
                    </button>
                </div>
            </nav>

            <Outlet />
        </>
    );
}

export default AppLayout;