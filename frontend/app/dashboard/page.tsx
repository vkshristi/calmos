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
  const [flowScore, setFlowScore] = useState<number | null>(null);
  const [weekFlow, setWeekFlow] = useState<any>(null);

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

    // ---- Fetch Flow Score ----
    const flowRes = await fetch(
      `http://127.0.0.1:8000/flow/today?user_email=${USER_EMAIL}`
    );

    const flowData = flowRes.ok ? await flowRes.json() : null;

    setFlowScore(flowData?.flow_score ?? null);

    // ---- Set Summary ----
    setSummary(data);
    setLoading(false);

    const weekFlowRes = await fetch(
      `http://127.0.0.1:8000/flow/week?user_email=${USER_EMAIL}`
    );

    const weekFlowData = weekFlowRes.ok ? await weekFlowRes.json() : null;

    setWeekFlow(weekFlowData);
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
          {/* Flow Score */}
          <hr />
          <h2>Flow Score</h2>

          <div
            style={{
              fontSize: "3rem",
              fontWeight: "bold",
              color:
                flowScore && flowScore >= 75
                  ? "green"
                  : flowScore && flowScore >= 50
                  ? "orange"
                  : "red",
            }}
          >
            {flowScore !== null ? flowScore : "N/A"}
          </div>

          <p>
            {flowScore && flowScore >= 75
              ? "High Flow Day"
              : flowScore && flowScore >= 50
              ? "Moderate Flow"
              : "Low Flow — adjust inputs"}
          </p>
          <hr />

          <hr />
          <h2>Weekly Flow Trend</h2>

          {weekFlow && weekFlow.records.length === 0 && (
            <p>No data yet.</p>
          )}

          {weekFlow && weekFlow.records.length > 0 && (
            <>
              <p>7-Day Average Flow: {weekFlow.average_flow}</p>
              <p>7-Day Average Accuracy: {weekFlow.average_accuracy ?? "N/A"}</p>

              <ul>
                {weekFlow.records.map((r: any) => (
                  <li key={r.id}>
                    {r.flow_date} — Flow: {r.predicted_score}
                    {r.accuracy !== null && ` | Accuracy: ${r.accuracy}%`}
                  </li>
                ))}
              </ul>
            </>
          )}

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
