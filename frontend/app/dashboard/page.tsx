"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import WellnessForm from "./WellnessForm";
import FocusTimer from "./FocusTimer";

const USER_EMAIL = "test@calmos.dev";

export default function DashboardPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    loadSummary();
  }, [router]);

  const loadSummary = async () => {
    setLoading(true);

    const res = await fetch(
      `http://127.0.0.1:8000/summary/today?user_email=${USER_EMAIL}`
    );

    const data = res.ok ? await res.json() : null;

    setSummary(data);
    setLoading(false);
  };

  const logout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <main style={{ padding: "2rem" }}>
      <h1>CalmOS Dashboard</h1>
      <button onClick={logout}>Logout</button>

      <hr />

      {loading && <p>Loading...</p>}

      {summary && (
        <>
          {/* Wellness */}
          {!summary.wellness && <WellnessForm onSuccess={loadSummary} />}

          {summary.wellness && (
            <>
              <h2>Today’s Wellness</h2>
              <ul>
                <li>Mood: {summary.wellness.mood}</li>
                <li>Sleep: {summary.wellness.sleep_hours} hrs</li>
                <li>Water: {summary.wellness.water_intake}</li>
                <li>Stress: {summary.wellness.stress}</li>
                <li>Exercise: {summary.wellness.exercise ? "Yes" : "No"}</li>
              </ul>
            </>
          )}

          <hr />

          {/* Focus */}
          <FocusTimer onComplete={loadSummary} />

          <h3>Today’s Focus</h3>
          <p>Total Minutes: {summary.focus.total_minutes}</p>
          <p>Average Flow: {summary.focus.average_flow ?? "N/A"}</p>
          <p>Sessions: {summary.focus.session_count}</p>
        </>
      )}
    </main>
  );
}
