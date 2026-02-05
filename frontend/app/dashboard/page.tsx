"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/login");
  };

  return (
    <main style={{ padding: "2rem" }}>
      <h1>Dashboard</h1>
      <p>You are logged in.</p>

      <button onClick={handleLogout}>Logout</button>
    </main>
  );
}
