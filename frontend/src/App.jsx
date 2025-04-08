import React, { useState } from "react";
import UploadForm from "./components/UploadForm";
import ResultDisplay from "./components/ResultDisplay";

function App() {
  const [results, setResults] = useState([]);

  return (
    <div
      style={{
        maxWidth: "800px",
        margin: "20px auto",
        padding: "20px",
        background: "white",
        borderRadius: "10px",
        boxShadow: "0px 4px 6px rgba(0, 0, 0, 0.1)",
        textAlign: "center",
      }}
    >
      <h1 style={{ color: "#333" }}>Pose Estimation App</h1>
      <UploadForm setResults={setResults} />
      <ResultDisplay results={results} />
    </div>
  );
}

export default App;
