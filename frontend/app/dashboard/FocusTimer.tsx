"use client";

import { useState, useEffect } from "react";

const USER_EMAIL = "test@calmos.dev";
const DEFAULT_DURATION = 25 * 60;

export default function FocusTimer({ onComplete }: { onComplete: () => void }) {
  const [seconds, setSeconds] = useState(DEFAULT_DURATION);
  const [running, setRunning] = useState(false);
  const [flowRating, setFlowRating] = useState(3);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    let timer: any;
    if (running && seconds > 0) {
      timer = setInterval(() => {
        setSeconds((prev) => prev - 1);
      }, 1000);
    }
    if (seconds === 0) {
      setRunning(false);
      setCompleted(true);
    }
    return () => clearInterval(timer);
  }, [running, seconds]);

  const start = () => setRunning(true);
  const reset = () => {
    setSeconds(DEFAULT_DURATION);
    setRunning(false);
    setCompleted(false);
  };

  const saveSession = async () => {
  const res = await fetch("http://127.0.0.1:8000/focus", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_email: USER_EMAIL,
      duration_minutes: Math.floor(DEFAULT_DURATION / 60),
      flow_rating: flowRating,
    }),
  });

  if (res.ok) {
    // WAIT briefly to ensure DB commit
    setTimeout(() => {
      onComplete();
    }, 300);
  }

  reset();
};

  return (
    <div>
      <h2>Focus Timer</h2>
      <p>{Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}</p>

      {!running && seconds === DEFAULT_DURATION && (
        <button onClick={start}>Start</button>
      )}

      {completed && (
        <>
          <p>Rate your Flow (1–5)</p>
          <input
            type="number"
            min={1}
            max={5}
            value={flowRating}
            onChange={(e) => setFlowRating(+e.target.value)}
          />
          <button onClick={saveSession}>Save Session</button>
        </>
      )}

      {!completed && seconds !== DEFAULT_DURATION && (
        <button onClick={reset}>Reset</button>
      )}
    </div>
  );
}
