import { useState } from "react";

const UploadForm = ({ setResults }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async (event) => {
    event.preventDefault();
    setLoading(true);

    const responses = await Promise.all(
      files.map(async (file) => {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("http://localhost:8000/upload/", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) throw new Error("Upload failed");

        const imageBlob = await response.blob();
        const contentType =
          response.headers.get("Content-Type") || "image/jpeg";
        const imageUrl = URL.createObjectURL(imageBlob);

        return { filename: file.name, imageUrl, contentType };
      })
    );

    setResults(responses);
    setLoading(false);
  };

  return (
    <div style={{ marginTop: "20px" }}>
      <h2 style={{ color: "#333" }}>Upload Images</h2>
      <input
        type="file"
        multiple
        onChange={(e) => setFiles([...e.target.files])}
        style={{
          display: "block",
          padding: "10px",
          margin: "10px auto",
          border: "1px solid #ccc",
          borderRadius: "5px",
        }}
      />
      <button
        onClick={handleUpload}
        disabled={loading}
        style={{
          backgroundColor: loading ? "#ccc" : "#007bff",
          color: "white",
          padding: "10px 15px",
          border: "none",
          borderRadius: "5px",
          cursor: loading ? "not-allowed" : "pointer",
          fontSize: "16px",
        }}
      >
        {loading ? "Processing..." : "Upload"}
      </button>
    </div>
  );
};

export default UploadForm;
