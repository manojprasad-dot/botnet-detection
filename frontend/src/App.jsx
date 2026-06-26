import { useState, useEffect } from 'react';
import KovirXDashboard from './components/KovirXDashboard';
import Login from './components/Login';
import { isAuthenticated } from './services/api';

function App() {
  const [authenticated, setAuthenticated] = useState(isAuthenticated());

  useEffect(() => {
    const handleAuthChange = () => {
      setAuthenticated(isAuthenticated());
    };

    window.addEventListener('auth_change', handleAuthChange);
    return () => {
      window.removeEventListener('auth_change', handleAuthChange);
    };
  }, []);

  return authenticated ? <KovirXDashboard /> : <Login />;
}

export default App;
