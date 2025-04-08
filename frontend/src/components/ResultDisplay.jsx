import React from "react";

const ResultDisplay = ({ results }) => {
  return (
    <div>
      {results.length > 0 && <h2 style={{ color: "#333" }}>Results</h2>}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "10px",
          marginTop: "20px",
        }}
      >
        {results.map((res, index) => (
          <div
            key={index}
            style={{
              background: "white",
              padding: "10px",
              borderRadius: "5px",
              boxShadow: "0px 2px 4px rgba(0, 0, 0, 0.1)",
              textAlign: "center",
            }}
          >
            <h3>{res.filename}</h3>
            <div>
              <img
                src={res.imageUrl}
                alt={res.filename}
                style={{
                  maxWidth: "100%",
                  height: "auto",
                  borderRadius: "5px",
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ResultDisplay;
