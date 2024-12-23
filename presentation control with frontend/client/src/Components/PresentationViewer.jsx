import React, { useEffect } from "react";

const PresentationViewer = () => {
  useEffect(() => {
    // Start the camera as soon as the component loads
    const startCamera = async () => {
      try {
        await fetch("http://127.0.0.1:5000/start_camera", { method: "POST" });
      } catch (error) {
        console.error("Error starting camera:", error);
      }
    };

    startCamera();
  }, []);

  return (
    <div style={{ textAlign: "center", padding: "20px" }}>
      <h3>Slides Viewer</h3>
      <img
        src="http://127.0.0.1:5000/video_feed"
        alt="Slides Viewer"
        style={{ maxWidth: "100%", height: "auto", borderRadius: "10px" }}
      />
    </div>
  );
};

export default PresentationViewer;
