import { useState } from 'react';
import Login from './Login';
import Dashboard from './Dashboard';
import './App.css';

function App() {
  const [currentUser, setCurrentUser] = useState<string | null>(null);

  if (!currentUser) {
    return <Login onLoginSuccess={setCurrentUser} />;
  }

  return <Dashboard currentUser={currentUser} />;
}

export default App;
