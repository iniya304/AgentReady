"use client";

import { useEffect, useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Payment = {
  id: string;
  customer_id: string;
  amount: number;
  currency: string;
  payment_status: string;
  failure_reason: string | null;
};

type Analysis = {
  payment_id: string;
  customer_id: string;
  amount: number;
  failure_reason: string | null;
  strategy: string;
  reason: string;
  recommended_delay_hours: number;
  confidence: number;
  priority: string;
  priority_score: number;
};

type RecoveryAction = {
  id: string;
  payment_id: string;
  strategy: string;
  priority: string;
  priority_score: number;
  status: string;
  created_at: string;
};

export default function Home() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [recoveryActions, setRecoveryActions] = useState<
    RecoveryAction[]
  >([]);

  const [analysis, setAnalysis] = useState<Analysis | null>(null);

  const [loadingPayments, setLoadingPayments] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const [error, setError] = useState<string | null>(null);

  // ---------------------------------------------------------
  // LOAD PAYMENTS
  // ---------------------------------------------------------

  async function loadPayments() {
    try {
      setLoadingPayments(true);

      const response = await fetch(`${API_URL}/payments`);

      if (!response.ok) {
        throw new Error("Unable to load payments");
      }

      const data = await response.json();

      setPayments(data.payments || []);
    } catch (err) {
      console.error(err);
      setError("Unable to load payments.");
    } finally {
      setLoadingPayments(false);
    }
  }

  // ---------------------------------------------------------
  // LOAD RECOVERY HISTORY
  // ---------------------------------------------------------

  async function loadRecoveryHistory() {
    try {
      setLoadingHistory(true);

      const response = await fetch(
        `${API_URL}/recovery-actions`
      );

      if (!response.ok) {
        throw new Error("Unable to load recovery history");
      }

      const data = await response.json();

      setRecoveryActions(data.recovery_actions || []);
    } catch (err) {
      console.error(err);
      setError("Unable to load recovery history.");
    } finally {
      setLoadingHistory(false);
    }
  }

  // ---------------------------------------------------------
  // INITIAL LOAD
  // ---------------------------------------------------------

  useEffect(() => {
    loadPayments();
    loadRecoveryHistory();
  }, []);

  // ---------------------------------------------------------
  // ANALYZE PAYMENT
  // ---------------------------------------------------------

  async function handleAnalyze(paymentId: string) {
    try {
      setError(null);

      const response = await fetch(
        `${API_URL}/payments/${paymentId}/analyze`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Unable to analyze payment");
      }

      const data = await response.json();

      setAnalysis(data.analysis);
    } catch (err) {
      console.error(err);
      setError("Unable to analyze payment.");
    }
  }

  // ---------------------------------------------------------
  // RECOVER PAYMENT
  // ---------------------------------------------------------

  async function handleRecover(paymentId: string) {
    try {
      setError(null);
      setLoadingAction(paymentId);

      const response = await fetch(
        `${API_URL}/payments/${paymentId}/recover`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Unable to create recovery action");
      }

      const data = await response.json();

      setAnalysis({
        payment_id: data.payment_id,
        customer_id: "",
        amount: 0,
        failure_reason: null,
        strategy: data.action,
        reason: data.message,
        recommended_delay_hours: 0,
        confidence: 0,
        priority: data.priority,
        priority_score: data.priority_score,
      });

      await loadRecoveryHistory();
    } catch (err) {
      console.error(err);
      setError("Unable to create recovery action.");
    } finally {
      setLoadingAction(null);
    }
  }

  // ---------------------------------------------------------
  // DASHBOARD METRICS
  // ---------------------------------------------------------

  const totalFailedPayments = payments.length;

  const totalAtRisk = payments.reduce(
    (total, payment) => total + Number(payment.amount),
    0
  );

  const highPriorityActions = recoveryActions.filter(
    (action) =>
      action.priority.toLowerCase() === "high"
  ).length;

  return (
    <main className="dashboard">
      <div className="container">

        {/* =====================================================
            HEADER
        ===================================================== */}

        <header className="header">

          <div>
            <div className="brand">
              <div className="brandIcon">A</div>

              <div>
                <h1>AgentReady</h1>

                <p>
                  AI-powered revenue recovery orchestration
                </p>
              </div>
            </div>
          </div>

          <div className="systemStatus">
            <span className="statusDot"></span>
            System Online
          </div>

        </header>


        {/* =====================================================
            ERROR
        ===================================================== */}

        {error && (
          <div className="errorBox">
            <strong>Something went wrong</strong>
            <span>{error}</span>
          </div>
        )}


        {/* =====================================================
            METRICS
        ===================================================== */}

        <section className="metricsGrid">

          <MetricCard
            title="Failed Payments"
            value={totalFailedPayments.toString()}
            subtitle="Payments requiring attention"
            icon="!"
          />

          <MetricCard
            title="Revenue at Risk"
            value={`₹${totalAtRisk.toLocaleString(
              "en-IN"
            )}`}
            subtitle="Total failed transaction value"
            icon="₹"
          />

          <MetricCard
            title="Recovery Actions"
            value={recoveryActions.length.toString()}
            subtitle="AI recommendations generated"
            icon="↗"
          />

          <MetricCard
            title="High Priority"
            value={highPriorityActions.toString()}
            subtitle="Requires priority handling"
            icon="⚡"
          />

        </section>


        {/* =====================================================
            AI ANALYSIS
        ===================================================== */}

        {analysis && (
          <section className="analysisCard">

            <div className="sectionHeader">

              <div>
                <span className="eyebrow">
                  AI DECISION ENGINE
                </span>

                <h2>Recovery Analysis</h2>

                <p>
                  AgentReady analyzed this failed payment
                  and selected a recovery strategy.
                </p>
              </div>

              <div className="decisionBadge">
                AI Decision
              </div>

            </div>


            <div className="analysisGrid">

              <InfoBox
                label="Recommended Strategy"
                value={formatStrategy(
                  analysis.strategy
                )}
              />

              <InfoBox
                label="Priority"
                value={analysis.priority.toUpperCase()}
                highlight={
                  analysis.priority.toLowerCase() ===
                  "high"
                }
              />

              <InfoBox
                label="Priority Score"
                value={`${analysis.priority_score}/100`}
              />

              {analysis.confidence > 0 && (
                <InfoBox
                  label="AI Confidence"
                  value={`${Math.round(
                    analysis.confidence * 100
                  )}%`}
                />
              )}

            </div>


            <div className="reasonBox">

              <div className="reasonIcon">
                AI
              </div>

              <div>
                <strong>Why this action?</strong>

                <p>
                  {analysis.reason}
                </p>
              </div>

            </div>

          </section>
        )}


        {/* =====================================================
            FAILED PAYMENTS
        ===================================================== */}

        <section className="card">

          <div className="sectionHeader">

            <div>
              <span className="eyebrow">
                PAYMENT MONITORING
              </span>

              <h2>Failed Payments</h2>

              <p>
                Payments detected by AgentReady that may
                require recovery intervention.
              </p>
            </div>

            <div className="countBadge">
              {payments.length} payments
            </div>

          </div>


          {loadingPayments ? (
            <div className="loading">
              Loading payments...
            </div>
          ) : payments.length === 0 ? (
            <div className="emptyState">
              No failed payments found.
            </div>
          ) : (
            <div className="tableWrapper">

              <table>

                <thead>
                  <tr>
                    <th>Customer</th>
                    <th>Amount</th>
                    <th>Failure Reason</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>

                <tbody>

                  {payments.map((payment) => (

                    <tr key={payment.id}>

                      <td>
                        <div className="customerCell">

                          <div className="customerAvatar">
                            {payment.customer_id
                              .replace("cust_", "")
                              .charAt(0)
                              .toUpperCase()}
                          </div>

                          <div>
                            <strong>
                              {payment.customer_id}
                            </strong>

                            <small>
                              Payment ID{" "}
                              {payment.id.slice(0, 8)}...
                            </small>
                          </div>

                        </div>
                      </td>


                      <td>
                        <strong className="amount">
                          ₹
                          {Number(
                            payment.amount
                          ).toLocaleString("en-IN")}
                        </strong>
                      </td>


                      <td>
                        <span className="failureBadge">
                          {formatStrategy(
                            payment.failure_reason ||
                              "unknown"
                          )}
                        </span>
                      </td>


                      <td>
                        <span className="statusBadge">
                          <span className="statusSmallDot"></span>
                          {payment.payment_status}
                        </span>
                      </td>


                      <td>

                        <div className="actionButtons">

                          <button
                            className="analyzeButton"
                            onClick={() =>
                              handleAnalyze(
                                payment.id
                              )
                            }
                          >
                            Analyze
                          </button>

                          <button
                            className="recoverButton"
                            onClick={() =>
                              handleRecover(
                                payment.id
                              )
                            }
                            disabled={
                              loadingAction ===
                              payment.id
                            }
                          >
                            {loadingAction ===
                            payment.id
                              ? "Saving..."
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


        {/* =====================================================
            RECOVERY HISTORY
        ===================================================== */}

        <section className="card">

          <div className="sectionHeader">

            <div>
              <span className="eyebrow">
                AGENT ACTIVITY
              </span>

              <h2>Recovery History</h2>

              <p>
                Recovery decisions persisted by the
                AgentReady backend.
              </p>
            </div>

            <button
              className="refreshButton"
              onClick={loadRecoveryHistory}
            >
              ↻ Refresh
            </button>

          </div>


          {loadingHistory ? (
            <div className="loading">
              Loading recovery history...
            </div>
          ) : recoveryActions.length === 0 ? (
            <div className="emptyState">
              No recovery actions yet.
            </div>
          ) : (

            <div className="tableWrapper">

              <table>

                <thead>
                  <tr>
                    <th>Payment</th>
                    <th>Strategy</th>
                    <th>Priority</th>
                    <th>Score</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>

                <tbody>

                  {recoveryActions.map(
                    (action) => (

                      <tr key={action.id}>

                        <td>

                          <span className="paymentId">
                            {action.payment_id.slice(
                              0,
                              12
                            )}
                            ...
                          </span>

                        </td>


                        <td>

                          <strong>
                            {formatStrategy(
                              action.strategy
                            )}
                          </strong>

                        </td>


                        <td>

                          <span
                            className={
                              action.priority.toLowerCase() ===
                              "high"
                                ? "priorityHigh"
                                : "priorityNormal"
                            }
                          >
                            {action.priority.toUpperCase()}
                          </span>

                        </td>


                        <td>

                          <div className="score">

                            <span>
                              {action.priority_score}
                            </span>

                            <div className="scoreBar">
                              <div
                                className="scoreFill"
                                style={{
                                  width: `${Math.min(
                                    action.priority_score,
                                    100
                                  )}%`,
                                }}
                              />
                            </div>

                          </div>

                        </td>


                        <td>

                          <span className="recommendedBadge">
                            <span className="statusSmallDot"></span>
                            {formatStatus(
                              action.status
                            )}
                          </span>

                        </td>


                        <td>

                          <span className="createdAt">
                            {new Date(
                              action.created_at
                            ).toLocaleString(
                              "en-IN"
                            )}
                          </span>

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>


        {/* =====================================================
            FOOTER
        ===================================================== */}

        <footer>

          <span>
            AgentReady
          </span>

          <span>
            AI Revenue Recovery System
          </span>

        </footer>

      </div>


      {/* =======================================================
          STYLES
      ======================================================= */}

      <style jsx>{`

        * {
          box-sizing: border-box;
        }

        .dashboard {
          min-height: 100vh;
          background: #f4f7fb;
          color: #172033;
          padding: 38px 24px 60px;
          font-family:
            Arial,
            Helvetica,
            sans-serif;
        }

        .container {
          max-width: 1240px;
          margin: 0 auto;
        }

        /* HEADER */

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 34px;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 14px;
        }

        .brandIcon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          background: #111827;
          color: #ffffff;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 22px;
          font-weight: 800;
        }

        .brand h1 {
          margin: 0;
          color: #111827;
          font-size: 30px;
          font-weight: 800;
          letter-spacing: -0.8px;
        }

        .brand p {
          margin: 5px 0 0;
          color: #64748b;
          font-size: 14px;
        }

        .systemStatus {
          display: flex;
          align-items: center;
          gap: 8px;
          background: #ffffff;
          border: 1px solid #dbe2ea;
          border-radius: 999px;
          padding: 9px 14px;
          color: #334155;
          font-size: 13px;
          font-weight: 600;
        }

        .statusDot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #16a34a;
        }

        /* ERROR */

        .errorBox {
          display: flex;
          flex-direction: column;
          gap: 4px;
          background: #fff1f2;
          border: 1px solid #fecdd3;
          color: #9f1239;
          padding: 14px 18px;
          border-radius: 10px;
          margin-bottom: 22px;
          font-size: 14px;
        }

        /* METRICS */

        .metricsGrid {
          display: grid;
          grid-template-columns:
            repeat(4, 1fr);
          gap: 18px;
          margin-bottom: 24px;
        }

        .metricCard {
          background: #ffffff;
          border: 1px solid #dfe5ec;
          border-radius: 14px;
          padding: 22px;
          box-shadow:
            0 3px 12px rgba(15, 23, 42, 0.04);
        }

        .metricTop {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 18px;
        }

        .metricIcon {
          width: 34px;
          height: 34px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 9px;
          background: #eef2ff;
          color: #3730a3;
          font-weight: 800;
        }

        .metricTitle {
          color: #64748b;
          font-size: 13px;
          font-weight: 600;
        }

        .metricValue {
          color: #111827;
          font-size: 29px;
          font-weight: 800;
          letter-spacing: -0.7px;
        }

        .metricSubtitle {
          color: #94a3b8;
          font-size: 12px;
          margin-top: 6px;
        }

        /* CARDS */

        .card,
        .analysisCard {
          background: #ffffff;
          border: 1px solid #dfe5ec;
          border-radius: 14px;
          padding: 26px;
          margin-bottom: 24px;
          box-shadow:
            0 3px 12px rgba(15, 23, 42, 0.04);
        }

        .analysisCard {
          border-left: 4px solid #4f46e5;
        }

        .sectionHeader {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 20px;
          margin-bottom: 22px;
        }

        .eyebrow {
          display: block;
          color: #4f46e5;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 1.2px;
          margin-bottom: 7px;
        }

        .sectionHeader h2 {
          margin: 0;
          color: #111827;
          font-size: 21px;
          font-weight: 750;
        }

        .sectionHeader p {
          margin: 6px 0 0;
          color: #64748b;
          font-size: 13px;
          line-height: 1.5;
        }

        .decisionBadge {
          background: #eef2ff;
          color: #4338ca;
          border: 1px solid #c7d2fe;
          padding: 8px 12px;
          border-radius: 8px;
          font-size: 12px;
          font-weight: 700;
        }

        .countBadge {
          background: #f1f5f9;
          color: #475569;
          padding: 8px 12px;
          border-radius: 8px;
          font-size: 12px;
          font-weight: 700;
        }

        /* ANALYSIS */

        .analysisGrid {
          display: grid;
          grid-template-columns:
            repeat(4, 1fr);
          gap: 14px;
        }

        .infoBox {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 10px;
          padding: 16px;
        }

        .infoLabel {
          color: #64748b;
          font-size: 11px;
          font-weight: 700;
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .infoValue {
          color: #111827;
          font-size: 16px;
          font-weight: 750;
        }

        .infoValue.highlight {
          color: #dc2626;
        }

        .reasonBox {
          display: flex;
          gap: 13px;
          align-items: flex-start;
          margin-top: 16px;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 10px;
          padding: 16px;
        }

        .reasonIcon {
          width: 34px;
          height: 34px;
          min-width: 34px;
          border-radius: 8px;
          background: #111827;
          color: #ffffff;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: 800;
        }

        .reasonBox strong {
          color: #111827;
          font-size: 13px;
        }

        .reasonBox p {
          color: #475569;
          margin: 5px 0 0;
          font-size: 13px;
          line-height: 1.5;
        }

        /* TABLE */

        .tableWrapper {
          overflow-x: auto;
        }

        table {
          width: 100%;
          border-collapse: collapse;
        }

        th {
          text-align: left;
          padding: 13px 12px;
          color: #64748b;
          background: #f8fafc;
          border-bottom: 1px solid #e2e8f0;
          font-size: 11px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.4px;
        }

        td {
          padding: 15px 12px;
          color: #334155;
          border-bottom: 1px solid #edf1f5;
          font-size: 13px;
          vertical-align: middle;
        }

        tbody tr:hover {
          background: #fafbfc;
        }

        tbody tr:last-child td {
          border-bottom: none;
        }

        /* CUSTOMER */

        .customerCell {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .customerAvatar {
          width: 34px;
          height: 34px;
          border-radius: 9px;
          background: #eef2ff;
          color: #4338ca;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 12px;
          font-weight: 800;
        }

        .customerCell strong {
          display: block;
          color: #1e293b;
          font-size: 13px;
        }

        .customerCell small {
          display: block;
          color: #94a3b8;
          font-size: 10px;
          margin-top: 3px;
        }

        .amount {
          color: #111827;
          font-size: 14px;
        }

        .failureBadge {
          display: inline-block;
          background: #fff7ed;
          color: #c2410c;
          border: 1px solid #fed7aa;
          padding: 5px 8px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 700;
        }

        .statusBadge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: #fef2f2;
          color: #b91c1c;
          padding: 5px 8px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 700;
        }

        .statusSmallDot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: #ef4444;
        }

        /* BUTTONS */

        .actionButtons {
          display: flex;
          gap: 7px;
        }

        .analyzeButton,
        .recoverButton,
        .refreshButton {
          border-radius: 7px;
          padding: 8px 12px;
          font-size: 11px;
          font-weight: 700;
          cursor: pointer;
          transition: 0.15s ease;
        }

        .analyzeButton {
          background: #ffffff;
          border: 1px solid #cbd5e1;
          color: #334155;
        }

        .analyzeButton:hover {
          background: #f8fafc;
          border-color: #94a3b8;
        }

        .recoverButton {
          background: #111827;
          border: 1px solid #111827;
          color: #ffffff;
        }

        .recoverButton:hover {
          background: #374151;
        }

        .recoverButton:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        .refreshButton {
          background: #ffffff;
          border: 1px solid #cbd5e1;
          color: #334155;
        }

        .refreshButton:hover {
          background: #f8fafc;
        }

        /* RECOVERY HISTORY */

        .paymentId {
          color: #64748b;
          font-family: monospace;
          font-size: 11px;
        }

        .priorityHigh {
          color: #dc2626;
          background: #fef2f2;
          border: 1px solid #fecaca;
          padding: 5px 8px;
          border-radius: 6px;
          font-size: 10px;
          font-weight: 800;
        }

        .priorityNormal {
          color: #475569;
          background: #f1f5f9;
          padding: 5px 8px;
          border-radius: 6px;
          font-size: 10px;
          font-weight: 800;
        }

        .score {
          display: flex;
          align-items: center;
          gap: 9px;
        }

        .score > span {
          min-width: 24px;
          color: #111827;
          font-weight: 800;
        }

        .scoreBar {
          width: 55px;
          height: 5px;
          background: #e2e8f0;
          border-radius: 99px;
          overflow: hidden;
        }

        .scoreFill {
          height: 100%;
          background: #4f46e5;
          border-radius: 99px;
        }

        .recommendedBadge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: #ecfdf5;
          color: #047857;
          border: 1px solid #a7f3d0;
          padding: 5px 8px;
          border-radius: 6px;
          font-size: 10px;
          font-weight: 800;
        }

        .recommendedBadge .statusSmallDot {
          background: #10b981;
        }

        .createdAt {
          color: #64748b;
          font-size: 11px;
        }

        /* STATES */

        .loading,
        .emptyState {
          padding: 35px;
          text-align: center;
          color: #64748b;
          font-size: 13px;
        }

        /* FOOTER */

        footer {
          display: flex;
          justify-content: space-between;
          color: #94a3b8;
          font-size: 11px;
          padding: 10px 4px;
        }

        /* RESPONSIVE */

        @media (max-width: 900px) {

          .metricsGrid {
            grid-template-columns:
              repeat(2, 1fr);
          }

          .analysisGrid {
            grid-template-columns:
              repeat(2, 1fr);
          }

        }

        @media (max-width: 600px) {

          .dashboard {
            padding: 22px 14px;
          }

          .header {
            flex-direction: column;
            align-items: flex-start;
            gap: 16px;
          }

          .metricsGrid {
            grid-template-columns: 1fr;
          }

          .analysisGrid {
            grid-template-columns: 1fr;
          }

          .sectionHeader {
            flex-direction: column;
          }

          .actionButtons {
            flex-direction: column;
          }

          footer {
            flex-direction: column;
            gap: 6px;
          }

        }

      `}</style>
    </main>
  );
}


// =========================================================
// COMPONENTS
// =========================================================

function MetricCard({
  title,
  value,
  subtitle,
  icon,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: string;
}) {
  return (
    <div className="metricCard">

      <div className="metricTop">

        <span className="metricTitle">
          {title}
        </span>

        <div className="metricIcon">
          {icon}
        </div>

      </div>

      <div className="metricValue">
        {value}
      </div>

      <div className="metricSubtitle">
        {subtitle}
      </div>

    </div>
  );
}


function InfoBox({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="infoBox">

      <div className="infoLabel">
        {label}
      </div>

      <div
        className={`infoValue ${
          highlight ? "highlight" : ""
        }`}
      >
        {value}
      </div>

    </div>
  );
}


// =========================================================
// HELPERS
// =========================================================

function formatStrategy(strategy: string) {
  return strategy
    .split("_")
    .map(
      (word) =>
        word.charAt(0).toUpperCase() +
        word.slice(1)
    )
    .join(" ");
}


function formatStatus(status: string) {
  return status
    .split("_")
    .map(
      (word) =>
        word.charAt(0).toUpperCase() +
        word.slice(1)
    )
    .join(" ");
}