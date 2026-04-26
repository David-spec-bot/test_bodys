export default function PhotoUpload({ label, file, onChange }) {
  return (
    <label className="upload">
      <input
        type="file"
        accept="image/png,image/jpeg,image/webp"
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
      />
      <div>{label}</div>
      <div className="filename">{file ? file.name : "click to select"}</div>
    </label>
  );
}
