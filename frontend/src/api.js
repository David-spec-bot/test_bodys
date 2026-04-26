export async function generateBody({ measurements, photoFront, photoSide }) {
  const fd = new FormData();
  fd.append("height_cm", measurements.height_cm);
  fd.append("bust_cm", measurements.bust_cm);
  fd.append("waist_cm", measurements.waist_cm);
  fd.append("hips_cm", measurements.hips_cm);
  fd.append("gender", measurements.gender);
  if (measurements.skin_tone) fd.append("skin_tone", measurements.skin_tone);
  if (photoFront) fd.append("photo_front", photoFront);
  if (photoSide) fd.append("photo_side", photoSide);

  const res = await fetch("/api/generate", { method: "POST", body: fd });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Generation failed (${res.status}): ${text}`);
  }
  return res.json();
}
