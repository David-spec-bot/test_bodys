import { useState } from "react";
import PhotoUpload from "./PhotoUpload.jsx";

const DEFAULTS = {
  height_cm: 168,
  bust_cm: 88,
  waist_cm: 68,
  hips_cm: 94,
  gender: "female",
  skin_tone: "",
};

export default function ParameterPanel({ onSubmit, busy, error, faceUrl }) {
  const [values, setValues] = useState(DEFAULTS);
  const [photoFront, setPhotoFront] = useState(null);
  const [photoSide, setPhotoSide] = useState(null);

  const update = (key) => (e) =>
    setValues((v) => ({ ...v, [key]: e.target.value }));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      measurements: {
        height_cm: Number(values.height_cm),
        bust_cm: Number(values.bust_cm),
        waist_cm: Number(values.waist_cm),
        hips_cm: Number(values.hips_cm),
        gender: values.gender,
        skin_tone: values.skin_tone || null,
      },
      photoFront,
      photoSide,
    });
  };

  return (
    <form className="panel" onSubmit={handleSubmit}>
      <h1>Virtual Try-On — Body Builder</h1>

      <h2>Body measurements (cm)</h2>
      <div className="field">
        <label>Height</label>
        <input type="number" min="80" max="230" value={values.height_cm} onChange={update("height_cm")} />
      </div>
      <div className="field">
        <label>Bust</label>
        <input type="number" min="40" max="200" value={values.bust_cm} onChange={update("bust_cm")} />
      </div>
      <div className="field">
        <label>Waist</label>
        <input type="number" min="30" max="200" value={values.waist_cm} onChange={update("waist_cm")} />
      </div>
      <div className="field">
        <label>Hips</label>
        <input type="number" min="40" max="220" value={values.hips_cm} onChange={update("hips_cm")} />
      </div>
      <div className="field">
        <label>Gender</label>
        <select value={values.gender} onChange={update("gender")}>
          <option value="female">Female</option>
          <option value="male">Male</option>
          <option value="neutral">Neutral</option>
        </select>
      </div>

      <h2>Photos (optional)</h2>
      <PhotoUpload label="Front photo" file={photoFront} onChange={setPhotoFront} />
      <PhotoUpload label="Side photo" file={photoSide} onChange={setPhotoSide} />

      <h2>Skin tone override</h2>
      <div className="field">
        <label>Hex (leave blank to sample from photo)</label>
        <input
          type="text"
          placeholder="#d8a98a"
          value={values.skin_tone}
          onChange={update("skin_tone")}
        />
      </div>

      <button className="primary" type="submit" disabled={busy}>
        {busy ? "Generating…" : "Generate 3D body"}
      </button>

      {error && <div className="error">{error}</div>}

      {faceUrl && (
        <div className="face-preview">
          <img src={faceUrl} alt="extracted face" />
        </div>
      )}
    </form>
  );
}
