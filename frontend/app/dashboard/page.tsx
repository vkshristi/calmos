"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import WellnessForm from "./WellnessForm";

const USER_EMAIL = "test@calmos.dev";

export default function DashboardPage() {
  const router = useRouter();
  const [today, setToday] = useState<any>(null);
  const [week, setWeek] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    loadWellness();
  }, [router]);

  const loadWellness = async () => {
    setLoading(true);

    const todayRes = await fetch(
      `http://127.0.0.1:8000/wellness/today?user_email=${USER_EMAIL}`
    );
    const weekRes = await fetch(
      `http://127.0.0.1:8000/wellness/week?user_email=${USER_EMAIL}`
    );

    const todayData = todayRes.ok ? await todayRes.json() : null;
    const weekData = weekRes.ok ? await weekRes.json() : [];

    setToday(todayData);
    setWeek(weekData);
    setLoading(false);
  };

  const logout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <main style={{ padding: "2rem" }}>
      <h1>Dashboard</h1>
      <button onClick={logout}>Logout</button>

      <hr />

      {loading && <p>Loading...</p>}

      {!loading && !today && (
        <WellnessForm onSuccess={loadWellness} />
      )}


      {today && (
        <>
          <h2>Today’s Wellness</h2>
          <ul>
            <li>Mood: {today.mood}</li>
            <li>Sleep: {today.sleep_hours} hrs</li>
            <li>Water: {today.water_intake} glasses</li>
            <li>Stress: {today.stress}</li>
            <li>Exercise: {today.exercise ? "Yes" : "No"}</li>
          </ul>
        </>
      )}

      <h2>Last 7 Days</h2>
      <ul>
        {week.map((log) => (
          <li key={log.date}>
            {log.date} — Mood {log.mood}, Sleep {log.sleep_hours}h
          </li>
        ))}
      </ul>
    </main>
  );
}
