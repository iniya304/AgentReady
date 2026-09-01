"use client";

import { useEffect, useState } from "react";

type Payment = {
  id: string;
  customer_id: string;
  amount: number;
  currency: string;
  payment_status: string;
  failure_reason: string;
  created_at: string;
};

type Analysis = {
  payment_id: string;
  customer_id: string;
  amount: number;
  failure_reason: string;
  strategy: string;
  reason: string;
  recommended_delay_hours: number;
  confidence: number;
  priority?: string;
  priority_score?: number;
};

type RecoveryResult = {
  success: boolean;
  payment_id: string;
  action: string;
  priority: string;
  priority_score: number;
  message: string;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [recoveringId, setRecoveringId] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [recoveryResult, setRecoveryResult] =
    useState<RecoveryResult | null>(null);

  useEffect(() => {
    async function loadPayments() {
      try {
        const response = await fetch(`${API_URL}/payments`);

        if (!response.ok) {
          throw new Error("Failed to fetch payments");
        }

        const data = await response.json();
        setPayments(data.payments || []);
      } catch (err) {
        console.error(err);
        setError("Unable to connect to AgentReady backend.");
      } finally {
        setLoading(false);
      }
    }

    loadPayments();
  }, []);

  const totalValue = payments.reduce(
    (sum, payment) => sum + payment.amount,
    0
  );

  async function analyzePayment(paymentId: string) {
    try {
      setAnalyzingId(paymentId);
      setError("");
      setRecoveryResult(null);

      const response = await fetch(
        `${API_URL}/payments/${paymentId}/analyze`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Recovery analysis failed");
      }

      const data = await response.json();

      setAnalysis(data.analysis);
    } catch (err) {
      console.error(err);
      setError("Unable to analyze this payment.");
    } finally {
      setAnalyzingId(null);
    }
  }

  async function recoverPayment(paymentId: string) {
    try {
      setRecoveringId(paymentId);
      setError("");

      const response = await fetch(
        `${API_URL}/payments/${paymentId}/recover`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Recovery execution failed");
      }

      const data: RecoveryResult = await response.json();

      setRecoveryResult(data);
    } catch (err) {
      console.error(err);
      setError("Unable to execute recovery action.");
    } finally {
      setRecoveringId(null);
    }
  }

  function formatStrategy(strategy: string) {
    return strategy
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  return (
    <main className="min-h-screen bg-[#09090b] px-6 py-10 text-white">
      <div className="mx-auto max-w-6xl">

        {/* Header */}
        <header className="mb-10 flex items-center justify-between">
          <div>
            <p className="mb-2 text-sm font-medium uppercase tracking-widest text-emerald-400">
              Payment Recovery Infrastructure
            </p>

            <h1 className="text-4xl font-bold tracking-tight">
              AgentReady
            </h1>

            <p className="mt-2 text-zinc-400">
              AI-powered payment recovery intelligence.
            </p>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            System Online
          </div>
        </header>

        {/* Error */}
        {error && (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-red-400">
            {error}
          </div>
        )}

        {/* Recovery Result */}
        {recoveryResult && (
          <section className="mb-8 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-6">

            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium uppercase tracking-wider text-emerald-400">
                  Recovery Action Executed
                </p>

                <h2 className="mt-1 text-2xl font-semibold">
                  Agent has selected a recovery path
                </h2>
              </div>

              <button
                onClick={() => setRecoveryResult(null)}
                className="text-sm text-zinc-500 hover:text-white"
              >
                Close
              </button>
            </div>

            <div className="mt-5 grid gap-5 md:grid-cols-4">

              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <p className="text-sm text-zinc-500">
                  Action
                </p>

                <p className="mt-2 text-lg font-semibold text-emerald-400">
                  {formatStrategy(recoveryResult.action)}
                </p>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <p className="text-sm text-zinc-500">
                  Priority
                </p>

                <p className="mt-2 text-lg font-semibold uppercase text-yellow-400">
                  {recoveryResult.priority}
                </p>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <p className="text-sm text-zinc-500">
                  Priority Score
                </p>

                <p className="mt-2 text-lg font-semibold">
                  {recoveryResult.priority_score}/100
                </p>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <p className="text-sm text-zinc-500">
                  Status
                </p>

                <p className="mt-2 text-lg font-semibold text-emerald-400">
                  Ready
                </p>
              </div>

            </div>

            <div className="mt-5 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
              <p className="text-sm text-zinc-500">
                Agent Message
              </p>

              <p className="mt-2 text-zinc-300">
                {recoveryResult.message}
              </p>
            </div>

          </section>
        )}

        {/* Overview Cards */}
        <section className="mb-8 grid gap-5 md:grid-cols-3">

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6">
            <p className="text-sm text-zinc-400">
              Failed Payments
            </p>

            <p className="mt-3 text-3xl font-bold">
              {loading ? "—" : payments.length}
            </p>

            <p className="mt-2 text-sm text-zinc-500">
              Payments requiring recovery
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6">
            <p className="text-sm text-zinc-400">
              Recovery Value
            </p>

            <p className="mt-3 text-3xl font-bold">
              {loading
                ? "—"
                : `₹${totalValue.toLocaleString("en-IN")}`}
            </p>

            <p className="mt-2 text-sm text-zinc-500">
              Total failed transaction value
            </p>
          </div>

          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6">
            <p className="text-sm text-zinc-400">
              Agent Status
            </p>

            <p className="mt-3 text-3xl font-bold text-emerald-400">
              Ready
            </p>

            <p className="mt-2 text-sm text-zinc-500">
              Recovery engine available
            </p>
          </div>

        </section>

        {/* Analysis */}
        {analysis && (
          <section className="mb-8 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-6">

            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm uppercase tracking-wider text-emerald-400">
                  Agent Recommendation
                </p>

                <h2 className="mt-1 text-2xl font-semibold">
                  Recovery Strategy
                </h2>
              </div>

              <button
                onClick={() => setAnalysis(null)}
                className="text-sm text-zinc-500 hover:text-white"
              >
                Close
              </button>
            </div>

            <div className="grid gap-5 md:grid-cols-4">

              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <p className="text-sm text-zinc-500">
                  Recommended Action
                </p>

                <p className="mt-2 text-xl font-semibold text-emerald-400">
                  {formatStrategy(analysis.strategy)}
                </p>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <p className="text-sm text-zinc-500">
                  Confidence
                </p>

                <p className="mt-2 text-xl font-semibold">
                  {(analysis.confidence * 100).toFixed(0)}%
                </p>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <p className="text-sm text-zinc-500">
                  Priority
                </p>

                <p className="mt-2 text-xl font-semibold uppercase text-yellow-400">
                  {analysis.priority || "Pending"}
                </p>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
                <p className="text-sm text-zinc-500">
                  Priority Score
                </p>

                <p className="mt-2 text-xl font-semibold">
                  {analysis.priority_score ?? "—"}/100
                </p>
              </div>

            </div>

            <div className="mt-5 rounded-xl border border-zinc-800 bg-zinc-900 p-5">
              <p className="text-sm text-zinc-500">
                Agent Reasoning
              </p>

              <p className="mt-2 text-zinc-300">
                {analysis.reason}
              </p>
            </div>

          </section>
        )}

        {/* Payments Table */}
        <section className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900/70">

          <div className="border-b border-zinc-800 px-6 py-5">
            <h2 className="text-xl font-semibold">
              Failed Payments
            </h2>

            <p className="mt-1 text-sm text-zinc-500">
              Transactions detected by AgentReady
            </p>
          </div>

          {loading ? (
            <div className="p-10 text-center text-zinc-500">
              Loading payment data...
            </div>
          ) : payments.length === 0 ? (
            <div className="p-10 text-center text-zinc-500">
              No failed payments found.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left">

                <thead className="border-b border-zinc-800 text-sm text-zinc-500">
                  <tr>
                    <th className="px-6 py-4 font-medium">
                      Customer
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Amount
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Failure Reason
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Status
                    </th>

                    <th className="px-6 py-4 font-medium">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {payments.map((payment) => (
                    <tr
                      key={payment.id}
                      className="border-b border-zinc-800/70 last:border-0 hover:bg-zinc-800/30"
                    >

                      <td className="px-6 py-5 font-medium">
                        {payment.customer_id}
                      </td>

                      <td className="px-6 py-5">
                        ₹{payment.amount.toLocaleString("en-IN")}
                      </td>

                      <td className="px-6 py-5">
                        <span className="rounded-md bg-red-500/10 px-3 py-1 text-sm capitalize text-red-400">
                          {payment.failure_reason?.replaceAll(
                            "_",
                            " "
                          ) || "Unknown"}
                        </span>
                      </td>

                      <td className="px-6 py-5">
                        <span className="text-yellow-400">
                          ● Pending Recovery
                        </span>
                      </td>

                      <td className="px-6 py-5">
                        <div className="flex gap-2">

                          <button
                            className="rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-sm font-medium text-zinc-300 transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-50"
                            onClick={() => analyzePayment(payment.id)}
                            disabled={analyzingId === payment.id}
                          >
                            {analyzingId === payment.id
                              ? "Analyzing..."
                              : "Analyze"}
                          </button>

                          <button
                            className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-sm font-medium text-emerald-400 transition hover:bg-emerald-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                            onClick={() => recoverPayment(payment.id)}
                            disabled={recoveringId === payment.id}
                          >
                            {recoveringId === payment.id
                              ? "Executing..."
                              : "Recover"}
                          </button>

                        </div>
                      </td>

                    </tr>
                  ))}
                </tbody>

              </table>
            </div>
          )}
        </section>

        {/* Footer */}
        <footer className="mt-8 text-center text-sm text-zinc-600">
          AgentReady • Intelligent Payment Recovery
        </footer>

      </div>
    </main>
  );
}