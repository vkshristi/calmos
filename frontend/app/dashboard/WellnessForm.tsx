"use client";

import { useState } from "react";

const USER_EMAIL = "test@calmos.dev";

export default function WellnessForm({ onSuccess }: { onSuccess: () => void }) {
  const [mood, setMood] = useState(3);
  const [sleep, setSleep] = useState(7);
  const [water, setWater] = useState(8);
  const [stress, setStress] = useState(3);
  const [exercise, setExercise] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submitWellness = async (e: React.FormEvent) => {
  e.preventDefault();
  setError("");
  setLoading(true);

  try {
    const params = new URLSearchParams({
      user_email: USER_EMAIL,
      mood: mood.toString(),
      sleep_hours: sleep.toString(),
      water_intake: water.toString(),
      stress: stress.toString(),
      exercise: exercise.toString(),
    });

    const res = await fetch(
      `http://127.0.0.1:8000/wellness?${params.toString()}`,
      {
        method: "POST",
      }
    );

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data?.detail || "Failed to save wellness");
    }

    onSuccess();
  } catch (err: any) {
    setError(err?.message || "Something went wrong");
  } finally {
    setLoading(false);
  }
};


  return (
    <form onSubmit={submitWellness}>
      <h2>Log Today’s Wellness</h2>

      <label>Mood (1–5)</label>
      <input type="number" min={1} max={5} value={mood} onChange={(e) => setMood(+e.target.value)} />

      <label>Sleep Hours</label>
      <input type="number" value={sleep} onChange={(e) => setSleep(+e.target.value)} />

      <label>Water Intake (glasses)</label>
      <input type="number" value={water} onChange={(e) => setWater(+e.target.value)} />

      <label>Stress (1–5)</label>
      <input type="number" min={0} max={5} value={stress} onChange={(e) => setStress(+e.target.value)} />

      <label>
        <input type="checkbox" checked={exercise} onChange={() => setExercise(!exercise)} />
        Exercised today
      </label>

      <button type="submit" disabled={loading}>
        {loading ? "Saving..." : "Save Wellness"}
      </button>

      {error && <p style={{ color: "red" }}>{String(error)}</p>}

    </form>
  );
}
