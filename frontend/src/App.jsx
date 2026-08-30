import { useEffect, useState } from "react";

function App() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/health")
      .then((response) => response.json())
      .then((data) => {
        setMessage(data.status);
      });
  }, []);

  return (
    <div>
      <h1>Training Tracker</h1>
      <p>Backend status: {message}</p>
    </div>
  );
}

export default App;