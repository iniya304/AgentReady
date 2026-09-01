"use client";

import { useEffect, useState } from "react";

type BackendHealth = {
  status: string;
  service: string;
  message: string;
  running: boolean;
};

export default function Home() {
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;

    if (!apiUrl) {
      setError("Backend URL is not configured.");
      setLoading(false);
      return;
    }

    fetch(`${apiUrl}/health`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Backend returned ${response.status}`);
        }

        return response.json();
      })
      .then((data: BackendHealth) => {
        setHealth(data);
        setError("");
      })
      .catch(() => {
        setError("Could not connect to the AgentReady backend.");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-zinc-950 px-6 py-16 text-white">
      <div className="w-full max-w-2xl rounded-2xl border border-zinc-800 bg-zinc-900 p-8 shadow-2xl">
        <div className="mb-8">
          <p className="mb-2 text-sm font-medium text-emerald-400">
            SYSTEM STATUS
          </p>

          <h1 className="text-4xl font-bold tracking-tight">
            AgentReady
          </h1>

          <p className="mt-3 text-zinc-400">
            AI-powered payment recovery infrastructure.
          </p>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
          <div className="flex items-center justify-between">
            <span className="text-zinc-400">Backend connection</span>

            {loading ? (
              <span className="text-yellow-400">Checking...</span>
            ) : health?.running ? (
              <span className="text-emerald-400">● Connected</span>
            ) : (
              <span className="text-red-400">● Offline</span>
            )}
          </div>

          {health && (
            <div className="mt-5 space-y-2 text-sm text-zinc-400">
              <p>
                Service:{" "}
                <span className="text-white">{health.service}</span>
              </p>

              <p>
                Status:{" "}
                <span className="text-white">{health.status}</span>
              </p>

              <p>
                Message:{" "}
                <span className="text-white">{health.message}</span>
              </p>
            </div>
          )}

          {error && (
            <p className="mt-4 text-sm text-red-400">
              {error}
            </p>
          )}
        </div>
      </div>
    </main>
  );
}