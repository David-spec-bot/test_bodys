import { useState } from "react";
import ParameterPanel from "./components/ParameterPanel.jsx";
import ModelViewer from "./components/ModelViewer.jsx";
import { generateBody } from "./api.js";

export default function App() {
  const [meshUrl, setMeshUrl] = useState(null);
  const [faceUrl, setFaceUrl] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (payload) => {
    setBusy(true);
    setError(null);
    try {
      const result = await generateBody(payload);
      // Cache-bust so the GLB loader doesn't reuse the old job's mesh.
      setMeshUrl(`${result.mesh_url}?t=${Date.now()}`);
      setFaceUrl(result.face_url ?? null);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="app">
      <ParameterPanel
        onSubmit={handleSubmit}
        busy={busy}
        error={error}
        faceUrl={faceUrl}
      />
      <ModelViewer meshUrl={meshUrl} />
    </div>
  );
}
