import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import Overview from "./pages/Overview";
import Incidents from "./pages/Incidents";
import Endpoints from "./pages/Endpoints";
import Reports from "./pages/Reports";
import Logs from "./pages/Logs";
import Profile from "./pages/Profile";
import SecuritySettings from "./pages/SecuritySettings";
import ActiveSessions from "./pages/ActiveSessions";
import UserManagement from "./pages/UserManagement";
import Login from "./pages/Login";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import { isAuthenticated } from "./services/api";

function PrivateRoute({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" replace />;
}

function App() {
  const [authenticated, setAuthenticated] = useState(isAuthenticated());

  useEffect(() => {
    const handleAuthChange = () => {
      setAuthenticated(isAuthenticated());
    };

    window.addEventListener("auth_change", handleAuthChange);
    return () => {
      window.removeEventListener("auth_change", handleAuthChange);
    };
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <PrivateRoute>
              <AppLayout />
            </PrivateRoute>
          }
        >
          <Route index element={<Overview />} />
          <Route path="alerts" element={<Incidents />} />
          <Route path="devices" element={<Endpoints />} />
          <Route path="reports" element={<Reports />} />
          <Route path="logs" element={<Logs />} />
          <Route path="profile" element={<Profile />} />
          <Route path="security" element={<SecuritySettings />} />
          <Route path="sessions" element={<ActiveSessions />} />
          <Route path="users" element={<UserManagement />} />
        </Route>
        <Route
          path="/login"
          element={
            authenticated ? <Navigate to="/" replace /> : <Login />
          }
        />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
