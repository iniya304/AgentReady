"use client";

import { useEffect, useMemo, useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://agentready-2.onrender.com";


type Payment = {
  id: string;
  customer_id: string;
  amount: number;
  currency: string;
  payment_status: string;
  failure_reason: string | null;
  payment_method?: string;
  created_at?: string;
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

type RecoveryAttempt = {
  id: string;
  payment_id: string;
  attempt_number: number;
  intervention: string;
  status: string;
  failure_reason?: string | null;
  recovery_action_id?: string | null;
  created_at: string;
  completed_at?: string | null;
};

type RecoveryWorkflow = {
  decision: string;
  reason: string;
  next_intervention?: string | null;
  attempt_number?: number;
  attempt?: RecoveryAttempt | null;
};

type AuditEvent = {
  id: string;
  payment_id: string | null;
  event_type: string;
  actor: string;
  decision: string | null;
  intervention: string | null;
  status: string | null;
  reason: string | null;
  metadata?: Record<string, unknown>;
  created_at: string;
};

type BatchResult = {
  payment_id: string;
  customer_id: string;
  amount: number;
  currency: string;
  failure_reason: string | null;
  payment_method?: string;
  recommended_intervention?: string;
  recovery_probability?: number;
  recovery_probability_percent?: number;
  expected_recovery_value?: number;
  policy_decision?: string;
  requires_human_review?: boolean;
  policy_reasons?: string[];
  error?: string;
};

type BatchData = {
  payment_count: number;
  total_revenue_at_risk: number;
  total_expected_recovery: number;
  recovery_opportunity_rate: number;
  recovery_opportunity_percent: number;
  average_recovery_probability: number;
  average_recovery_probability_percent: number;
  auto_recovery_count: number;
  human_review_count: number;
  results: BatchResult[];
};

type ModelComparison = {
  model: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  roc_auc: number;
  pr_auc: number;
  brier_score: number;
  roc_auc_gap: number;
};

type CalibrationPoint = {
  probability_bin: string;
  samples: number;
  predicted_probability: number;
  actual_recovery_rate: number;
};

type MLEvaluation = {
  model: {
    name: string;
    C: number;
    feature_count: number;
  };
  final_test: {
    accuracy: number;
    precision: number;
    recall: number;
    f1: number;
    roc_auc: number;
    pr_auc: number;
    brier_score: number;
  };
  cross_validation: {
    accuracy: number;
    precision: number;
    recall: number;
    f1: number;
    roc_auc: number;
    pr_auc: number;
    brier_score: number;
    train_cv_gap: number;
  };
  model_comparison: ModelComparison[];
  calibration: CalibrationPoint[];
  evaluation_note: string;
};

type AgentRecommendation = {
  payment_id: string;
  customer_id: string;
  amount: number;
  currency: string;
  failure_reason?: string | null;
  recommended_intervention?: string;
  recovery_probability?: number;
  expected_recovery_value?: number;
  policy_decision?: string;
};

type AgentResult = {
  intent: string;
  answer: string;
  source?: string;
  recommendations?: AgentRecommendation[];
  metrics?: {
    payment_count?: number;
    total_revenue_at_risk?: number;
    total_expected_recovery?: number;
    recovery_opportunity_percent?: number;
  };
};

type AgentResponse = {
  success: boolean;
  question: string;
  result: AgentResult;
};

export default function Home() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [recoveryActions, setRecoveryActions] = useState<RecoveryAction[]>(
    []
  );

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [batchData, setBatchData] = useState<BatchData | null>(null);
  const [mlEvaluation, setMLEvaluation] = useState<MLEvaluation | null>(null);

  const [loadingPayments, setLoadingPayments] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [loadingBatch, setLoadingBatch] = useState(false);
  const [loadingEvaluation, setLoadingEvaluation] = useState(true);

  const [error, setError] = useState<string | null>(null);
  const [lastBatchRun, setLastBatchRun] = useState<Date | null>(null);

  const [selectedRecoveryPayment, setSelectedRecoveryPayment] =
    useState<string>("");
  const [recoveryAttempts, setRecoveryAttempts] = useState<
    RecoveryAttempt[]
  >([]);
  const [workflowDecision, setWorkflowDecision] =
    useState<RecoveryWorkflow | null>(null);
  const [loadingWorkflow, setLoadingWorkflow] = useState(false);
  const [loadingAttempts, setLoadingAttempts] = useState(false);

  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [loadingAudit, setLoadingAudit] = useState(false);

  const [agentQuestion, setAgentQuestion] = useState("");
  const [agentResponse, setAgentResponse] = useState<AgentResponse | null>(null);
  const [loadingAgent, setLoadingAgent] = useState(false);

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

  async function loadRecoveryHistory() {
    try {
      setLoadingHistory(true);

      const response = await fetch(`${API_URL}/recovery-actions`);

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

  async function loadMLEvaluation() {
    try {
      setLoadingEvaluation(true);

      const response = await fetch(`${API_URL}/ml/evaluation`);

      if (!response.ok) {
        throw new Error("Unable to load ML evaluation");
      }

      const data = await response.json();

      if (data.success) {
        setMLEvaluation(data);
      }
    } catch (err) {
      console.error(err);
      setError("Unable to load ML model evaluation.");
    } finally {
      setLoadingEvaluation(false);
    }
  }

  async function loadAuditEvents(paymentId?: string) {
    try {
      setLoadingAudit(true);

      const endpoint = paymentId
        ? `${API_URL}/payments/${paymentId}/audit-events`
        : `${API_URL}/audit-events`;

      const response = await fetch(endpoint);

      if (!response.ok) {
        throw new Error("Unable to load audit events");
      }

      const data = await response.json();
      setAuditEvents(data.events || []);
    } catch (err) {
      console.error(err);
      setError("Unable to load audit trail.");
    } finally {
      setLoadingAudit(false);
    }
  }

  async function runBatchRecovery() {
    try {
      setError(null);
      setLoadingBatch(true);

      const response = await fetch(`${API_URL}/recovery/batch`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Unable to run recovery agent");
      }

      const data = await response.json();

      setBatchData(data.data);
      setLastBatchRun(new Date());
    } catch (err) {
      console.error(err);
      setError("Unable to run the recovery agent.");
    } finally {
      setLoadingBatch(false);
    }
  }

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

  async function loadRecoveryAttempts(paymentId: string) {
    if (!paymentId) return;

    try {
      setLoadingAttempts(true);

      const response = await fetch(
        `${API_URL}/payments/${paymentId}/recovery-attempts`
      );

      if (!response.ok) {
        throw new Error("Unable to load recovery attempts");
      }

      const data = await response.json();
      setRecoveryAttempts(data.attempts || []);
    } catch (err) {
      console.error(err);
      setError("Unable to load recovery attempt history.");
    } finally {
      setLoadingAttempts(false);
    }
  }

  async function runRecoveryWorkflow(paymentId: string) {
    if (!paymentId) return;

    try {
      setError(null);
      setLoadingWorkflow(true);

      const response = await fetch(
        `${API_URL}/payments/${paymentId}/recovery-workflow`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Unable to run recovery workflow");
      }

      const data = await response.json();
      const workflow = data.workflow || data;

      setWorkflowDecision(workflow);

      await loadRecoveryAttempts(paymentId);
      await loadAuditEvents(paymentId);
    } catch (err) {
      console.error(err);
      setError("Unable to run the recovery workflow.");
    } finally {
      setLoadingWorkflow(false);
    }
  }

  async function updateRecoveryAttempt(
    attemptId: string,
    status: "success" | "failed"
  ) {
    try {
      setError(null);

      const response = await fetch(
        `${API_URL}/recovery-attempts/${attemptId}`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            status,
            ...(status === "failed"
              ? { failure_reason: "demo_intervention_failed" }
              : {}),
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Unable to update recovery attempt");
      }

      if (selectedRecoveryPayment) {
        await loadRecoveryAttempts(selectedRecoveryPayment);
        await loadAuditEvents(selectedRecoveryPayment);
      }
    } catch (err) {
      console.error(err);
      setError("Unable to update the recovery attempt.");
    }
  }


  async function askRecoveryAgent(questionOverride?: string) {
    const question = (questionOverride ?? agentQuestion).trim();

    if (!question) return;

    try {
      setError(null);
      setLoadingAgent(true);

      const response = await fetch(`${API_URL}/agent/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || "Unable to process recovery agent query"
        );
      }

      const data: AgentResponse = await response.json();
      setAgentResponse(data);
      setAgentQuestion(question);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to process recovery agent query."
      );
    } finally {
      setLoadingAgent(false);
    }
  }

  useEffect(() => {
    loadPayments();
    loadRecoveryHistory();
    loadMLEvaluation();
  }, []);

  useEffect(() => {
    if (!selectedRecoveryPayment && payments.length > 0) {
      setSelectedRecoveryPayment(payments[0].id);
    }
  }, [payments, selectedRecoveryPayment]);

  useEffect(() => {
    if (selectedRecoveryPayment) {
      loadRecoveryAttempts(selectedRecoveryPayment);
      loadAuditEvents(selectedRecoveryPayment);
      setWorkflowDecision(null);
    }
  }, [selectedRecoveryPayment]);

  const totalFailedPayments = payments.length;

  const totalAtRisk = payments.reduce(
    (total, payment) => total + Number(payment.amount),
    0
  );

  const highPriorityActions = recoveryActions.filter(
    (action) => action.priority.toLowerCase() === "high"
  ).length;

  const recoveryQueue = useMemo(() => {
    if (!batchData) return [];

    return [...batchData.results].sort(
      (a, b) =>
        Number(b.expected_recovery_value || 0) -
        Number(a.expected_recovery_value || 0)
    );
  }, [batchData]);

  const topOpportunity = recoveryQueue[0] || null;

  const autoPercentage =
    batchData && batchData.payment_count > 0
      ? Math.round(
          (batchData.auto_recovery_count / batchData.payment_count) * 100
        )
      : 0;

  const topProbability = topOpportunity
    ? Number(
        topOpportunity.recovery_probability_percent ??
          Number(topOpportunity.recovery_probability || 0) * 100
      )
    : 0;

  return (
    <main className="dashboard">
      <div className="container">

        {/* HEADER */}
        <header className="header">
          <div className="brand">
            <div className="brandIcon">
              <span>AR</span>
            </div>

            <div>
              <div className="brandEyebrow">
                AI FINTECH INFRASTRUCTURE
              </div>

              <h1>AgentReady</h1>

              <p>Predictive revenue recovery intelligence</p>
            </div>
          </div>

          <div className="headerRight">
            <div className="systemStatus">
              <span className="statusDot" />

              <div>
                <strong>AGENT ONLINE</strong>
                <small>Recovery engine ready</small>
              </div>
            </div>

            <button
              className="agentButton"
              onClick={runBatchRecovery}
              disabled={loadingBatch}
            >
              <span>{loadingBatch ? "◌" : "✦"}</span>
              {loadingBatch
                ? "Analyzing portfolio..."
                : "Run Recovery Agent"}
            </button>
          </div>
        </header>

        {/* ERROR */}
        {error && (
          <div className="errorBox">
            <div className="errorIcon">!</div>

            <div>
              <strong>System notification</strong>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* CONVERSATIONAL RECOVERY AGENT */}
        <section className="agentCopilot">
          <div className="agentCopilotHeader">
            <div className="agentCopilotTitle">
              <div className="copilotIcon">✦</div>
              <div>
                <span className="eyebrow">RECOVERY COPILOT</span>
                <h2>Ask the agent what to recover next.</h2>
                <p>
                  Query live failed-payment data. AgentReady grounds every answer
                  in its recovery model, intervention optimizer, and policy guardrails.
                </p>
              </div>
            </div>

            <span className="copilotBadge">LIVE AGENT</span>
          </div>

          <div className="agentPromptRow">
            <input
              className="agentPromptInput"
              value={agentQuestion}
              onChange={(event) => setAgentQuestion(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  askRecoveryAgent();
                }
              }}
              placeholder="e.g. Which failed payments should I prioritize?"
              maxLength={500}
              aria-label="Ask the recovery agent"
            />

            <button
              className="agentAskButton"
              onClick={() => askRecoveryAgent()}
              disabled={loadingAgent || !agentQuestion.trim()}
            >
              {loadingAgent ? "Thinking..." : "Ask Agent"}
              <span>→</span>
            </button>
          </div>

          <div className="agentQuickPrompts">
            <span>TRY:</span>
            {[
              "Which failed payments should I prioritize?",
              "How much revenue is currently at risk?",
              "Which payments need human review?",
              "What should we do with cust_001?",
            ].map((prompt) => (
              <button
                key={prompt}
                className="quickPrompt"
                onClick={() => {
                  setAgentQuestion(prompt);
                  void askRecoveryAgent(prompt);
                }}
                disabled={loadingAgent}
              >
                {prompt}
              </button>
            ))}
          </div>

          {agentResponse && (
            <div className="agentResponse">
              <div className="agentResponseTop">
                <div>
                  <span className="miniLabel">AGENT RESPONSE</span>
                  <div className="agentIntent">
                    {formatStrategy(agentResponse.result.intent)}
                  </div>
                </div>
                <span className="agentGrounded">✓ GROUNDED IN RECOVERY INTELLIGENCE</span>
              </div>

              <p className="agentAnswer">{agentResponse.result.answer}</p>

              {agentResponse.result.metrics && (
                <div className="agentMetricStrip">
                  {agentResponse.result.metrics.payment_count !== undefined && (
                    <div>
                      <span>FAILED PAYMENTS</span>
                      <strong>{agentResponse.result.metrics.payment_count}</strong>
                    </div>
                  )}
                  {agentResponse.result.metrics.total_revenue_at_risk !== undefined && (
                    <div>
                      <span>REVENUE AT RISK</span>
                      <strong>
                        ₹{Number(
                          agentResponse.result.metrics.total_revenue_at_risk
                        ).toLocaleString("en-IN")}
                      </strong>
                    </div>
                  )}
                  {agentResponse.result.metrics.total_expected_recovery !== undefined && (
                    <div>
                      <span>EXPECTED RECOVERY</span>
                      <strong>
                        ₹{Number(
                          agentResponse.result.metrics.total_expected_recovery
                        ).toLocaleString("en-IN", {
                          maximumFractionDigits: 0,
                        })}
                      </strong>
                    </div>
                  )}
                  {agentResponse.result.metrics.recovery_opportunity_percent !== undefined && (
                    <div>
                      <span>OPPORTUNITY</span>
                      <strong>
                        {Number(
                          agentResponse.result.metrics.recovery_opportunity_percent
                        ).toFixed(1)}%
                      </strong>
                    </div>
                  )}
                </div>
              )}

              {agentResponse.result.recommendations &&
                agentResponse.result.recommendations.length > 0 && (
                  <div className="agentRecommendations">
                    <div className="agentRecommendationHeader">
                      <span>TOP RECOVERY OPPORTUNITIES</span>
                      <small>Ranked by expected recovery value</small>
                    </div>

                    <div className="agentRecommendationList">
                      {agentResponse.result.recommendations.map((item) => {
                        const probability = Number(item.recovery_probability || 0) * 100;
                        const isAuto = item.policy_decision === "AUTO_EXECUTE";

                        return (
                          <div
                            className="agentRecommendation"
                            key={item.payment_id}
                          >
                            <div className="agentRecommendationRank">
                              {String(
                                agentResponse.result.recommendations!.indexOf(item) + 1
                              ).padStart(2, "0")}
                            </div>

                            <div className="agentRecommendationMain">
                              <strong>{item.customer_id}</strong>
                              <small>
                                ₹{Number(item.amount).toLocaleString("en-IN")} ·{" "}
                                {formatStrategy(item.failure_reason || "unknown")}
                              </small>
                            </div>

                            <div className="agentRecommendationIntervention">
                              <span>INTERVENTION</span>
                              <strong>
                                {formatStrategy(
                                  item.recommended_intervention || "unknown"
                                )}
                              </strong>
                            </div>

                            <div className="agentRecommendationProbability">
                              <span>PROBABILITY</span>
                              <strong>{probability.toFixed(1)}%</strong>
                            </div>

                            <div className="agentRecommendationValue">
                              <span>EXPECTED RECOVERY</span>
                              <strong>
                                ₹{Number(
                                  item.expected_recovery_value || 0
                                ).toLocaleString("en-IN", {
                                  maximumFractionDigits: 0,
                                })}
                              </strong>
                            </div>

                            <span
                              className={
                                isAuto
                                  ? "agentAutoBadge"
                                  : "agentReviewBadge"
                              }
                            >
                              {isAuto ? "AUTO" : "REVIEW"}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

              <div className="agentSource">
                <span>Source</span>
                <strong>
                  {agentResponse.result.source || "AgentReady recovery intelligence"}
                </strong>
              </div>
            </div>
          )}
        </section>

        {/* PRE-RUN */}
        {!batchData && (
          <section className="preRun">
            <div className="preRunGlow" />

            <div className="preRunContent">
              <span className="eyebrow dark">
                RECOVERY INTELLIGENCE
              </span>

              <h2>
                Find revenue that&apos;s
                <br />
                <span>slipping away.</span>
              </h2>

              <p>
                AgentReady analyzes failed payments, evaluates recovery
                interventions, estimates expected recovery value, and
                applies policy guardrails before recommending action.
              </p>

              <button
                className="primaryLargeButton"
                onClick={runBatchRecovery}
                disabled={loadingBatch}
              >
                {loadingBatch
                  ? "Running recovery analysis..."
                  : "Run AI Recovery Analysis"}
                <span>→</span>
              </button>

              <div className="preRunMeta">
                <span>●</span>
                {payments.length} failed payments detected
                <span className="metaDivider">•</span>
                ₹{totalAtRisk.toLocaleString("en-IN")} at risk
              </div>
            </div>
          </section>
        )}

        {/* COMMAND CENTER */}
        {batchData && (
          <section className="commandCenter">
            <div className="commandGlow glowOne" />
            <div className="commandGlow glowTwo" />

            <div className="commandHeader">
              <div>
                <div className="commandEyebrow">
                  AI RECOVERY COMMAND CENTER
                </div>

                <h2>Recover revenue before it disappears.</h2>

                <p>
                  AgentReady evaluates failed payments, compares candidate
                  interventions, estimates expected recovery value, and
                  applies policy guardrails before recommending action.
                </p>
              </div>

              <div className="agentLive">
                <span className="livePulse" />

                <div>
                  <strong>ANALYSIS COMPLETE</strong>

                  <small>
                    {lastBatchRun
                      ? lastBatchRun.toLocaleTimeString("en-IN")
                      : "Portfolio analyzed"}
                  </small>
                </div>
              </div>
            </div>

            <div className="commandMetrics">
              <CommandMetric
                label="REVENUE AT RISK"
                value={`₹${Number(
                  batchData.total_revenue_at_risk
                ).toLocaleString("en-IN")}`}
                description="Failed transaction value"
              />

              <CommandMetric
                label="MODEL-ESTIMATED RECOVERY"
                value={`₹${Number(
                  batchData.total_expected_recovery
                ).toLocaleString("en-IN", {
                  maximumFractionDigits: 0,
                })}`}
                description="Expected value across optimized interventions"
                featured
              />

              <CommandMetric
                label="RECOVERY OPPORTUNITY"
                value={`${batchData.recovery_opportunity_percent}%`}
                description="Expected value / revenue at risk"
              />

              <CommandMetric
                label="AVG. PROBABILITY"
                value={`${batchData.average_recovery_probability_percent}%`}
                description="Across optimized interventions"
              />
            </div>

            <div className="commandBottom">
              <div className="opportunityCard">
                <div
                  className="opportunityRing"
                  style={{
                    background: `conic-gradient(
                      #818cf8 ${Math.min(
                        batchData.recovery_opportunity_percent,
                        100
                      )}%,
                      rgba(255,255,255,0.08) 0
                    )`,
                  }}
                >
                  <div className="ringInner">
                    <strong>
                      {Math.round(
                        batchData.recovery_opportunity_percent
                      )}
                      %
                    </strong>

                    <span>OPPORTUNITY</span>
                  </div>
                </div>
              </div>

              <div className="decisionCards">
                <div className="decisionCard autoDecision">
                  <div className="decisionIcon">✓</div>

                  <div>
                    <span>AUTO CANDIDATES</span>
                    <strong>{batchData.auto_recovery_count}</strong>
                    <small>Within policy limits</small>
                  </div>
                </div>

                <div className="decisionCard reviewDecision">
                  <div className="decisionIcon">!</div>

                  <div>
                    <span>HUMAN REVIEW</span>
                    <strong>{batchData.human_review_count}</strong>
                    <small>Guardrails triggered</small>
                  </div>
                </div>
              </div>

              <div className="commandExplanation">
                <div className="miniLabel">AGENT DECISION LOGIC</div>

                <p>
                  Candidate interventions are ranked by model-estimated
                  expected recovery value. Policy constraints then determine
                  whether the recommendation can proceed automatically or
                  requires human review.
                </p>

                <div className="guardrailTag">
                  <span>✓</span>
                  Policy guardrails active
                </div>
              </div>
            </div>
          </section>
        )}

        {/* WORKFLOW */}
        {batchData && (
          <section className="workflowCard">
            <div className="workflowHeader">
              <div>
                <span className="eyebrow">RECOVERY ORCHESTRATION</span>

                <h2>From failed payment to governed decision</h2>
              </div>

              <span className="workflowBadge">5-STAGE AGENT</span>
            </div>

            <div className="workflow">
              <WorkflowStep
                number="01"
                title="Detect"
                description="Failed payment"
              />

              <div className="workflowLine" />

              <WorkflowStep
                number="02"
                title="Predict"
                description="Recovery probability"
              />

              <div className="workflowLine" />

              <WorkflowStep
                number="03"
                title="Optimize"
                description="Best intervention"
              />

              <div className="workflowLine" />

              <WorkflowStep
                number="04"
                title="Govern"
                description="Policy guardrails"
              />

              <div className="workflowLine" />

              <WorkflowStep
                number="05"
                title="Decide"
                description="Auto / human"
              />
            </div>
          </section>
        )}

        {/* GOVERNED RECOVERY CONTROL */}
        {batchData && payments.length > 0 && (
          <section className="recoveryControlCard">
            <div className="sectionHeader">
              <div>
                <span className="eyebrow">
                  RECOVERY CONTROL PLANE
                </span>

                <h2>Execute the governed recovery loop</h2>

                <p>
                  Select a failed payment, create a bounded recovery attempt,
                  record its test outcome, and let the stopping rule decide
                  what happens next.
                </p>
              </div>

              <span className="workflowBadge">MAX 2 ATTEMPTS</span>
            </div>

            <div className="controlGrid">
              <div className="controlPanel">
                <label
                  className="controlLabel"
                  htmlFor="recovery-payment"
                >
                  FAILED PAYMENT
                </label>

                <select
                  id="recovery-payment"
                  className="paymentSelect"
                  value={selectedRecoveryPayment}
                  onChange={(event) =>
                    setSelectedRecoveryPayment(event.target.value)
                  }
                >
                  {payments.map((payment) => (
                    <option key={payment.id} value={payment.id}>
                      {payment.customer_id} · ₹
                      {Number(payment.amount).toLocaleString("en-IN")} ·{" "}
                      {formatStrategy(
                        payment.failure_reason || "unknown"
                      )}
                    </option>
                  ))}
                </select>

                <button
                  className="workflowRunButton"
                  onClick={() =>
                    runRecoveryWorkflow(selectedRecoveryPayment)
                  }
                  disabled={
                    loadingWorkflow || !selectedRecoveryPayment
                  }
                >
                  {loadingWorkflow
                    ? "Evaluating workflow..."
                    : "Start / Continue Recovery"}
                  <span>→</span>
                </button>

                <div className="controlNote">
                  <span>✓</span>
                  Backend-enforced stopping rule · no attempt 3
                </div>
              </div>

              <div className="workflowDecisionPanel">
                <div className="miniLabel">
                  LATEST WORKFLOW DECISION
                </div>

                {workflowDecision ? (
                  <>
                    <div
                      className={`workflowDecision ${workflowDecision.decision.toLowerCase()}`}
                    >
                      {formatStatus(workflowDecision.decision)}
                    </div>

                    <p className="workflowReason">
                      {workflowDecision.reason}
                    </p>

                    <div className="workflowDecisionMeta">
                      <span>
                        Attempt {workflowDecision.attempt_number ?? "—"}
                      </span>

                      <span>
                        Next:{" "}
                        {workflowDecision.next_intervention
                          ? formatStrategy(
                              workflowDecision.next_intervention
                            )
                          : "STOP / HUMAN REVIEW"}
                      </span>
                    </div>
                  </>
                ) : (
                  <div className="workflowEmpty">
                    Run the workflow to see the agent decision and stopping
                    rule.
                  </div>
                )}
              </div>
            </div>

            <div className="attemptHeader">
              <div>
                <strong>Recovery attempt ledger</strong>
                <span>Persistent state from Supabase</span>
              </div>

              <span className="countBadge">
                {recoveryAttempts.length} attempts
              </span>
            </div>

            {loadingAttempts ? (
              <LoadingState text="Loading attempt history..." />
            ) : recoveryAttempts.length === 0 ? (
              <div className="attemptEmpty">
                No recovery attempts recorded for this payment.
              </div>
            ) : (
              <div className="attemptTimeline">
                {recoveryAttempts.map((attempt) => (
                  <div className="attemptRow" key={attempt.id}>
                    <div className="attemptNumber">
                      {attempt.attempt_number}
                    </div>

                    <div className="attemptMain">
                      <strong>
                        {formatStrategy(attempt.intervention)}
                      </strong>

                      <small>
                        {new Date(
                          attempt.created_at
                        ).toLocaleString("en-IN")}

                        {attempt.failure_reason
                          ? ` · ${formatStrategy(
                              attempt.failure_reason
                            )}`
                          : ""}
                      </small>
                    </div>

                    <span
                      className={`attemptStatus ${attempt.status.toLowerCase()}`}
                    >
                      {formatStatus(attempt.status)}
                    </span>

                    {attempt.status === "pending" && (
                      <div className="attemptActions">
                        <button
                          className="attemptSuccessButton"
                          onClick={() =>
                            updateRecoveryAttempt(
                              attempt.id,
                              "success"
                            )
                          }
                        >
                          Record Success
                        </button>

                        <button
                          className="attemptFailButton"
                          onClick={() =>
                            updateRecoveryAttempt(
                              attempt.id,
                              "failed"
                            )
                          }
                        >
                          Record Failure
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div className="demoGuardrail">
              <span>DEMO SAFETY BOUNDARY</span>

              <p>
                Outcome buttons update the test workflow state only.
                AgentReady does not claim a real payment was executed or
                recovered.
              </p>
            </div>
          </section>
        )}

        {/* AUDIT TRAIL */}
        {selectedRecoveryPayment && (
          <section className="card">
            <div className="sectionHeader">
              <div>
                <span className="eyebrow">AUDIT TRAIL</span>

                <h2>Recovery decision history</h2>

                <p>
                  Every recovery decision and workflow outcome is recorded
                  for traceability.
                </p>
              </div>

              <span className="workflowBadge">
                {auditEvents.length} EVENTS
              </span>
            </div>

            {loadingAudit ? (
              <LoadingState text="Loading audit trail..." />
            ) : auditEvents.length === 0 ? (
              <div className="emptyState">
                No audit events recorded for this payment yet.
              </div>
            ) : (
              <div className="tableWrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Event</th>
                      <th>Decision</th>
                      <th>Intervention</th>
                      <th>Status</th>
                      <th>Reason</th>
                    </tr>
                  </thead>

                  <tbody>
                    {auditEvents.map((event) => (
                      <tr key={event.id}>
                        <td>
                          {event.created_at
                            ? new Date(
                                event.created_at
                              ).toLocaleString("en-IN")
                            : "—"}
                        </td>

                        <td>
                          {event.event_type
                            ?.replaceAll("_", " ")
                            .replace(/\b\w/g, (char: string) =>
                              char.toUpperCase()
                            )}
                        </td>

                        <td>{event.decision || "—"}</td>
                        <td>{event.intervention || "—"}</td>
                        <td>{event.status || "—"}</td>
                        <td>{event.reason || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {/* KPI CARDS */}
        <section className="metricsGrid">
          <MetricCard
            title="Failed Payments"
            value={totalFailedPayments.toString()}
            subtitle="Payments requiring attention"
            icon="!"
          />

          <MetricCard
            title="Revenue at Risk"
            value={`₹${totalAtRisk.toLocaleString("en-IN")}`}
            subtitle="Total failed transaction value"
            icon="₹"
          />

          <MetricCard
            title="Recovery Actions"
            value={recoveryActions.length.toString()}
            subtitle="AI recommendations persisted"
            icon="↗"
          />

          <MetricCard
            title="High Priority"
            value={highPriorityActions.toString()}
            subtitle="Priority recovery actions"
            icon="⚡"
          />
        </section>

        {/* RECOVERY INTELLIGENCE */}
        {batchData && topOpportunity && (
          <section className="intelligenceGrid">
            <div className="intelligenceCard featuredInsight">
              <span className="insightEyebrow">
                #1 RECOVERY OPPORTUNITY
              </span>

              <h3>Highest-value candidate</h3>

              <div className="insightCustomer">
                <div className="customerAvatar large">
                  {topOpportunity.customer_id
                    .replace("cust_", "")
                    .charAt(0)
                    .toUpperCase()}
                </div>

                <div>
                  <strong>{topOpportunity.customer_id}</strong>

                  <small>
                    ₹
                    {Number(
                      topOpportunity.amount
                    ).toLocaleString("en-IN")}{" "}
                    transaction at risk
                  </small>
                </div>
              </div>

              <div className="insightValue">
                ₹
                {Number(
                  topOpportunity.expected_recovery_value || 0
                ).toLocaleString("en-IN", {
                  maximumFractionDigits: 0,
                })}
              </div>

              <div className="insightLabel">
                MODEL-ESTIMATED EXPECTED RECOVERY
              </div>
            </div>

            <div className="intelligenceCard">
              <span className="insightEyebrow">
                OPTIMIZED INTERVENTION
              </span>

              <h3>Best recovery path</h3>

              <div className="pathIcon">↗</div>

              <div className="pathValue">
                {formatStrategy(
                  topOpportunity.recommended_intervention ||
                    "unknown"
                )}
              </div>

              <div className="pathProbability">
                <span>{Math.round(topProbability)}%</span>

                <div>
                  <div
                    style={{
                      width: `${Math.min(topProbability, 100)}%`,
                    }}
                  />
                </div>

                <small>model-estimated probability</small>
              </div>
            </div>

            <div className="intelligenceCard">
              <span className="insightEyebrow">GOVERNANCE</span>

              <h3>Decision coverage</h3>

              <div className="coverageRow">
                <div>
                  <strong>{batchData.auto_recovery_count}</strong>
                  <span>Auto candidates</span>
                </div>

                <div>
                  <strong>{batchData.human_review_count}</strong>
                  <span>Human review</span>
                </div>
              </div>

              <div className="coverageBar">
                <div style={{ width: `${autoPercentage}%` }} />
              </div>

              <p>
                {autoPercentage}% of recommendations fall within the
                current automatic policy boundary.
              </p>
            </div>
          </section>
        )}

        {/* ML MODEL EVALUATION */}
        <section className="card modelEvaluationCard">
          <div className="sectionHeader">
            <div>
              <span className="eyebrow">
                MODEL VALIDATION
              </span>

              <h2>AI Recovery Model Evaluation</h2>

              <p>
                Evidence-based evaluation of the deployed recovery
                probability model across test performance, cross-validation,
                model comparison, and calibration.
              </p>
            </div>

            {mlEvaluation && (
              <span className="workflowBadge">
                {mlEvaluation.model.name.toUpperCase()}
              </span>
            )}
          </div>

          {loadingEvaluation ? (
            <LoadingState text="Loading model evaluation..." />
          ) : !mlEvaluation ? (
            <div className="emptyState">
              Model evaluation is currently unavailable.
            </div>
          ) : (
            <>
              <div className="modelIdentity">
                <div>
                  <span>DEPLOYED MODEL</span>
                  <strong>{mlEvaluation.model.name}</strong>
                </div>

                <div>
                  <span>REGULARIZATION C</span>
                  <strong>{mlEvaluation.model.C}</strong>
                </div>

                <div>
                  <span>ENGINEERED FEATURES</span>
                  <strong>{mlEvaluation.model.feature_count}</strong>
                </div>

                <div className="modelReliability">
                  <span>TRAIN / CV GAP</span>
                  <strong>
                    {(
                      mlEvaluation.cross_validation.train_cv_gap * 100
                    ).toFixed(2)}
                    %
                  </strong>
                  <small>Lower gap indicates better generalization</small>
                </div>
              </div>

              <div className="evaluationSectionTitle">
                FINAL TEST PERFORMANCE
              </div>

              <div className="evaluationMetrics">
                <EvaluationMetric
                  label="ACCURACY"
                  value={mlEvaluation.final_test.accuracy}
                />

                <EvaluationMetric
                  label="PRECISION"
                  value={mlEvaluation.final_test.precision}
                />

                <EvaluationMetric
                  label="RECALL"
                  value={mlEvaluation.final_test.recall}
                  featured
                />

                <EvaluationMetric
                  label="F1 SCORE"
                  value={mlEvaluation.final_test.f1}
                  featured
                />

                <EvaluationMetric
                  label="ROC-AUC"
                  value={mlEvaluation.final_test.roc_auc}
                />

                <EvaluationMetric
                  label="PR-AUC"
                  value={mlEvaluation.final_test.pr_auc}
                  featured
                />

                <EvaluationMetric
                  label="BRIER SCORE"
                  value={mlEvaluation.final_test.brier_score}
                  inverse
                />
              </div>

              <div className="evaluationLowerGrid">
                <div className="evaluationPanel">
                  <div className="evaluationPanelHeader">
                    <div>
                      <span className="eyebrow">
                        CROSS-VALIDATION
                      </span>

                      <h3>5-fold validation</h3>
                    </div>

                    <span className="smallBadge">
                      GENERALIZATION
                    </span>
                  </div>

                  <div className="cvGrid">
                    <MiniMetric
                      label="ROC-AUC"
                      value={mlEvaluation.cross_validation.roc_auc}
                    />

                    <MiniMetric
                      label="PR-AUC"
                      value={mlEvaluation.cross_validation.pr_auc}
                    />

                    <MiniMetric
                      label="F1"
                      value={mlEvaluation.cross_validation.f1}
                    />

                    <MiniMetric
                      label="RECALL"
                      value={mlEvaluation.cross_validation.recall}
                    />
                  </div>

                  <div className="gapBox">
                    <div>
                      <span>TRAIN / CV ROC-AUC GAP</span>
                      <strong>
                        {(
                          mlEvaluation.cross_validation.train_cv_gap *
                          100
                        ).toFixed(2)}
                        %
                      </strong>
                    </div>

                    <div className="gapTrack">
                      <div
                        style={{
                          width: `${Math.min(
                            mlEvaluation.cross_validation.train_cv_gap *
                              100 *
                              5,
                            100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                </div>

                <div className="evaluationPanel">
                  <div className="evaluationPanelHeader">
                    <div>
                      <span className="eyebrow">
                        MODEL COMPARISON
                      </span>

                      <h3>Candidate models</h3>
                    </div>
                  </div>

                  <div className="modelComparison">
                    {mlEvaluation.model_comparison.map((model) => (
                      <div
                        className="modelComparisonRow"
                        key={model.model}
                      >
                        <div className="modelComparisonName">
                          <strong>{model.model}</strong>

                          <small>
                            Gap {(model.roc_auc_gap * 100).toFixed(1)}%
                          </small>
                        </div>

                        <div className="modelScoreTrack">
                          <div
                            style={{
                              width: `${Math.min(
                                model.roc_auc * 100,
                                100
                              )}%`,
                            }}
                          />
                        </div>

                        <strong className="modelScore">
                          {(model.roc_auc * 100).toFixed(1)}%
                        </strong>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="calibrationPanel">
                <div className="evaluationPanelHeader">
                  <div>
                    <span className="eyebrow">
                      PROBABILITY CALIBRATION
                    </span>

                    <h3>
                      Predicted probability vs actual recovery
                    </h3>
                  </div>

                  <span className="smallBadge">
                    {mlEvaluation.calibration.length} BINS
                  </span>
                </div>

                <div className="calibrationTable">
                  <div className="calibrationHeader">
                    <span>Probability Range</span>
                    <span>Samples</span>
                    <span>Predicted</span>
                    <span>Actual</span>
                    <span>Alignment</span>
                  </div>

                  {mlEvaluation.calibration.map((point) => {
                    const predicted =
                      point.predicted_probability * 100;

                    const actual =
                      point.actual_recovery_rate * 100;

                    const alignment = Math.max(
                      0,
                      100 - Math.abs(predicted - actual) * 3
                    );

                    return (
                      <div
                        className="calibrationRow"
                        key={point.probability_bin}
                      >
                        <span>{point.probability_bin}</span>

                        <span>{point.samples}</span>

                        <strong>{predicted.toFixed(1)}%</strong>

                        <strong>{actual.toFixed(1)}%</strong>

                        <div className="calibrationTrack">
                          <div
                            style={{
                              width: `${alignment}%`,
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="evaluationNote">
                <span>ⓘ</span>
                <p>{mlEvaluation.evaluation_note}</p>
              </div>
            </>
          )}
        </section>

        {/* AI DECISION QUEUE */}
        {batchData && (
          <section className="card decisionQueueCard">
            <div className="sectionHeader">
              <div>
                <span className="eyebrow">
                  AGENT DECISION QUEUE
                </span>

                <h2>AI Recovery Recommendations</h2>

                <p>
                  Ranked by model-estimated expected recovery value after
                  intervention optimization.
                </p>
              </div>

              <div className="countBadge">
                {recoveryQueue.length} decisions
              </div>
            </div>

            <div className="tableWrapper">
              <table className="decisionTable">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Customer</th>
                    <th>Amount</th>
                    <th>Failure</th>
                    <th>Intervention</th>
                    <th>Probability</th>
                    <th>Expected Recovery</th>
                    <th>Decision</th>
                  </tr>
                </thead>

                <tbody>
                  {recoveryQueue.map((item, index) => {
                    const probability = Number(
                      item.recovery_probability_percent ??
                        Number(item.recovery_probability || 0) * 100
                    );

                    const isAuto =
                      item.policy_decision === "AUTO_EXECUTE";

                    return (
                      <tr key={item.payment_id}>
                        <td>
                          <div className="queueRank">
                            {String(index + 1).padStart(2, "0")}
                          </div>
                        </td>

                        <td>
                          <div className="queueCustomer">
                            <div className="customerAvatar">
                              {item.customer_id
                                .replace("cust_", "")
                                .charAt(0)
                                .toUpperCase()}
                            </div>

                            <div>
                              <strong>{item.customer_id}</strong>

                              <small>
                                {item.payment_id.slice(0, 8)}...
                              </small>
                            </div>
                          </div>
                        </td>

                        <td>
                          <strong className="amount">
                            ₹
                            {Number(item.amount).toLocaleString("en-IN")}
                          </strong>
                        </td>

                        <td>
                          <span className="failureBadge">
                            {formatStrategy(
                              item.failure_reason || "unknown"
                            )}
                          </span>
                        </td>

                        <td>
                          <strong className="intervention">
                            {formatStrategy(
                              item.recommended_intervention || "unknown"
                            )}
                          </strong>
                        </td>

                        <td>
                          <div className="probability">
                            <strong>
                              {Math.round(probability)}%
                            </strong>

                            <div className="probabilityBar">
                              <div
                                className="probabilityFill"
                                style={{
                                  width: `${Math.min(
                                    probability,
                                    100
                                  )}%`,
                                }}
                              />
                            </div>
                          </div>
                        </td>

                        <td>
                          <strong className="recoveryValue">
                            ₹
                            {Number(
                              item.expected_recovery_value || 0
                            ).toLocaleString("en-IN", {
                              maximumFractionDigits: 0,
                            })}
                          </strong>
                        </td>

                        <td>
                          {isAuto ? (
                            <span className="autoBadge">
                              <span className="statusSmallDot" />
                              AUTO
                            </span>
                          ) : (
                            <span className="reviewBadge">
                              <span>!</span>
                              REVIEW
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* AI EXPLAINABILITY */}
        {analysis && (
          <section className="analysisCard">
            <div className="sectionHeader">
              <div>
                <span className="eyebrow">AI DECISION ENGINE</span>

                <h2>Why did the agent choose this?</h2>

                <p>
                  Transparent reasoning for the selected recovery
                  recommendation.
                </p>
              </div>

              <div className="decisionBadge">✦ AI Decision</div>
            </div>

            <div className="analysisGrid">
              <InfoBox
                label="Recommended Strategy"
                value={formatStrategy(analysis.strategy)}
              />

              <InfoBox
                label="Priority"
                value={analysis.priority.toUpperCase()}
                highlight={
                  analysis.priority.toLowerCase() === "high"
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
              <div className="reasonIcon">AI</div>

              <div>
                <strong>Agent reasoning</strong>

                <p>{analysis.reason}</p>
              </div>
            </div>

            <div className="explainFooter">
              <span>✓ Decision generated by recovery intelligence</span>
              <span>✓ Policy-aware recommendation</span>
              <span>✓ Audit-ready</span>
            </div>
          </section>
        )}

        {/* FAILED PAYMENTS */}
        <section className="card">
          <div className="sectionHeader">
            <div>
              <span className="eyebrow">PAYMENT MONITORING</span>

              <h2>Failed Payments</h2>

              <p>
                Failed transactions detected by AgentReady and available
                for recovery analysis.
              </p>
            </div>

            <div className="countBadge">
              {payments.length} payments
            </div>
          </div>

          {loadingPayments ? (
            <LoadingState text="Loading payments..." />
          ) : payments.length === 0 ? (
            <div className="emptyState">No failed payments found.</div>
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
                            <strong>{payment.customer_id}</strong>

                            <small>
                              ID {payment.id.slice(0, 8)}...
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
                            payment.failure_reason || "unknown"
                          )}
                        </span>
                      </td>

                      <td>
                        <span className="statusBadge">
                          <span className="statusSmallDot" />
                          {payment.payment_status}
                        </span>
                      </td>

                      <td>
                        <div className="actionButtons">
                          <button
                            className="analyzeButton"
                            onClick={() =>
                              handleAnalyze(payment.id)
                            }
                          >
                            Analyze
                          </button>

                          <button
                            className="recoverButton"
                            onClick={() =>
                              handleRecover(payment.id)
                            }
                            disabled={
                              loadingAction === payment.id
                            }
                          >
                            {loadingAction === payment.id
                              ? "Saving..."
                              : "Recommend"}
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

        {/* RECOVERY HISTORY */}
        <section className="card">
          <div className="sectionHeader">
            <div>
              <span className="eyebrow">AGENT ACTIVITY</span>

              <h2>Recovery History</h2>

              <p>
                Recovery recommendations persisted by the AgentReady
                backend.
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
            <LoadingState text="Loading recovery history..." />
          ) : recoveryActions.length === 0 ? (
            <div className="emptyState">No recovery actions yet.</div>
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
                  {recoveryActions.map((action) => (
                    <tr key={action.id}>
                      <td>
                        <span className="paymentId">
                          {action.payment_id.slice(0, 12)}...
                        </span>
                      </td>

                      <td>
                        <strong>
                          {formatStrategy(action.strategy)}
                        </strong>
                      </td>

                      <td>
                        <span
                          className={
                            action.priority.toLowerCase() === "high"
                              ? "priorityHigh"
                              : "priorityNormal"
                          }
                        >
                          {action.priority.toUpperCase()}
                        </span>
                      </td>

                      <td>
                        <div className="score">
                          <span>{action.priority_score}</span>

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
                          <span className="statusSmallDot" />
                          {formatStatus(action.status)}
                        </span>
                      </td>

                      <td>
                        <span className="createdAt">
                          {new Date(
                            action.created_at
                          ).toLocaleString("en-IN")}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* FOOTER */}
        <footer>
          <div className="footerBrand">
            <span className="footerLogo">AR</span>
            <strong>AgentReady</strong>
          </div>

          <span>Predictive AI Revenue Recovery System</span>

          <span>
            Razorpay AI Buildathon • Revenue Recovery
          </span>
        </footer>
      </div>

      <style jsx>{`
        * {
          box-sizing: border-box;
        }

        .dashboard {
          min-height: 100vh;
          padding: 30px 22px 70px;
          background:
            radial-gradient(circle at 50% -10%, #ffffff 0, #f5f7fb 42%, #edf1f6 100%);
          color: #172033;
          font-family: Inter, ui-sans-serif, system-ui, -apple-system,
            BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .container {
          max-width: 1320px;
          margin: 0 auto;
        }

        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 20px;
          margin-bottom: 24px;
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 13px;
        }

        .brandIcon {
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 14px;
          background: linear-gradient(145deg, #080d18, #263451);
          color: white;
          font-size: 12px;
          font-weight: 900;
          box-shadow: 0 10px 25px rgba(15, 23, 42, 0.16);
        }

        .brandEyebrow {
          margin-bottom: 2px;
          color: #6366f1;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 1.4px;
        }

        .brand h1 {
          margin: 0;
          color: #0f172a;
          font-size: 27px;
          font-weight: 900;
          letter-spacing: -1px;
        }

        .brand p {
          margin: 3px 0 0;
          color: #64748b;
          font-size: 10px;
        }

        .headerRight {
          display: flex;
          align-items: center;
          gap: 9px;
        }

        .systemStatus {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: white;
          border: 1px solid #dfe5ec;
          border-radius: 10px;
        }

        .statusDot,
        .livePulse {
          width: 7px;
          height: 7px;
          flex-shrink: 0;
          border-radius: 50%;
          background: #22c55e;
          box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.1);
        }

        .systemStatus strong,
        .systemStatus small {
          display: block;
        }

        .systemStatus strong {
          color: #166534;
          font-size: 8px;
          letter-spacing: 0.6px;
        }

        .systemStatus small {
          margin-top: 2px;
          color: #94a3b8;
          font-size: 8px;
        }

        .agentButton,
        .primaryLargeButton {
          border: none;
          color: white;
          background: linear-gradient(135deg, #111827, #293750);
          cursor: pointer;
          font-weight: 800;
          box-shadow: 0 9px 25px rgba(15, 23, 42, 0.16);
          transition: 0.18s ease;
        }

        .agentButton {
          padding: 11px 15px;
          border-radius: 10px;
          font-size: 10px;
        }

        .agentButton:hover,
        .primaryLargeButton:hover,
        .workflowRunButton:hover {
          transform: translateY(-1px);
        }

        .agentButton:disabled,
        .primaryLargeButton:disabled,
        .workflowRunButton:disabled {
          opacity: 0.55;
          cursor: not-allowed;
          transform: none;
        }

        /* CONVERSATIONAL RECOVERY AGENT */

        .agentCopilot {
          margin-bottom: 20px;
          padding: 22px 24px;
          border: 1px solid #c7d2fe;
          border-radius: 14px;
          background:
            radial-gradient(circle at 100% 0%, rgba(99,102,241,0.09), transparent 35%),
            linear-gradient(145deg, #ffffff, #f8faff);
          box-shadow: 0 8px 28px rgba(79,70,229,0.06);
        }

        .agentCopilotHeader {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 18px;
        }

        .agentCopilotTitle {
          display: flex;
          align-items: flex-start;
          gap: 11px;
        }

        .copilotIcon {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          border-radius: 10px;
          color: white;
          background: linear-gradient(135deg, #111827, #4f46e5);
          font-size: 14px;
          font-weight: 900;
          box-shadow: 0 7px 18px rgba(79,70,229,0.18);
        }

        .agentCopilot h2 {
          margin: 0;
          color: #111827;
          font-size: 18px;
          letter-spacing: -0.4px;
        }

        .agentCopilot p {
          margin: 5px 0 0;
          max-width: 760px;
          color: #64748b;
          font-size: 9px;
          line-height: 1.55;
        }

        .copilotBadge,
        .agentGrounded {
          padding: 6px 8px;
          border-radius: 6px;
          color: #4338ca;
          border: 1px solid #c7d2fe;
          background: #eef2ff;
          font-size: 6px;
          font-weight: 900;
          letter-spacing: 0.6px;
          white-space: nowrap;
        }

        .agentPromptRow {
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 8px;
          margin-top: 16px;
        }

        .agentPromptInput {
          width: 100%;
          min-width: 0;
          padding: 12px 13px;
          border: 1px solid #dbe2ea;
          border-radius: 8px;
          outline: none;
          color: #172033;
          background: white;
          font-size: 9px;
          font-weight: 600;
          transition: 0.15s ease;
        }

        .agentPromptInput:focus {
          border-color: #818cf8;
          box-shadow: 0 0 0 3px rgba(99,102,241,0.08);
        }

        .agentAskButton {
          display: inline-flex;
          align-items: center;
          justify-content: space-between;
          gap: 22px;
          min-width: 105px;
          padding: 10px 12px;
          border: none;
          border-radius: 8px;
          color: white;
          background: linear-gradient(135deg, #111827, #4338ca);
          cursor: pointer;
          font-size: 8px;
          font-weight: 900;
          box-shadow: 0 7px 18px rgba(79,70,229,0.14);
        }

        .agentAskButton:hover {
          transform: translateY(-1px);
        }

        .agentAskButton:disabled {
          opacity: 0.5;
          cursor: not-allowed;
          transform: none;
        }

        .agentQuickPrompts {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 5px;
          margin-top: 9px;
        }

        .agentQuickPrompts > span {
          color: #94a3b8;
          font-size: 6px;
          font-weight: 900;
          letter-spacing: 0.7px;
        }

        .quickPrompt {
          padding: 5px 7px;
          border: 1px solid #e2e8f0;
          border-radius: 6px;
          color: #475569;
          background: white;
          cursor: pointer;
          font-size: 6px;
          font-weight: 700;
        }

        .quickPrompt:hover {
          color: #4338ca;
          border-color: #c7d2fe;
          background: #f8faff;
        }

        .quickPrompt:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .agentResponse {
          margin-top: 15px;
          padding: 15px;
          border: 1px solid #e2e8f0;
          border-radius: 10px;
          background: white;
        }

        .agentResponseTop {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
        }

        .agentIntent {
          margin-top: 4px;
          color: #111827;
          font-size: 11px;
          font-weight: 900;
        }

        .agentGrounded {
          color: #047857;
          border-color: #a7f3d0;
          background: #ecfdf5;
        }

        .agentAnswer {
          margin: 11px 0 0 !important;
          color: #334155 !important;
          font-size: 9px !important;
          line-height: 1.6 !important;
        }

        .agentMetricStrip {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 7px;
          margin-top: 12px;
        }

        .agentMetricStrip > div {
          padding: 9px;
          border: 1px solid #edf1f5;
          border-radius: 7px;
          background: #f8fafc;
        }

        .agentMetricStrip span,
        .agentMetricStrip strong {
          display: block;
        }

        .agentMetricStrip span {
          color: #64748b;
          font-size: 6px;
          font-weight: 900;
          letter-spacing: 0.5px;
        }

        .agentMetricStrip strong {
          margin-top: 5px;
          color: #111827;
          font-size: 13px;
        }

        .agentRecommendations {
          margin-top: 12px;
        }

        .agentRecommendationHeader {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          gap: 10px;
          margin-bottom: 7px;
        }

        .agentRecommendationHeader > span {
          color: #64748b;
          font-size: 6px;
          font-weight: 900;
          letter-spacing: 0.7px;
        }

        .agentRecommendationHeader small {
          color: #94a3b8;
          font-size: 6px;
        }

        .agentRecommendationList {
          display: grid;
          gap: 5px;
        }

        .agentRecommendation {
          display: grid;
          grid-template-columns: 26px 1.4fr 1.1fr 0.8fr 1fr auto;
          align-items: center;
          gap: 8px;
          padding: 8px;
          border: 1px solid #edf1f5;
          border-radius: 8px;
          background: #fbfcfe;
        }

        .agentRecommendationRank {
          color: #94a3b8;
          font-family: monospace;
          font-size: 8px;
          font-weight: 900;
        }

        .agentRecommendationMain strong,
        .agentRecommendationMain small,
        .agentRecommendationIntervention span,
        .agentRecommendationIntervention strong,
        .agentRecommendationProbability span,
        .agentRecommendationProbability strong,
        .agentRecommendationValue span,
        .agentRecommendationValue strong {
          display: block;
        }

        .agentRecommendationMain strong {
          color: #1e293b;
          font-size: 8px;
        }

        .agentRecommendationMain small {
          margin-top: 2px;
          color: #94a3b8;
          font-size: 6px;
        }

        .agentRecommendationIntervention span,
        .agentRecommendationProbability span,
        .agentRecommendationValue span {
          color: #94a3b8;
          font-size: 5px;
          font-weight: 900;
          letter-spacing: 0.4px;
        }

        .agentRecommendationIntervention strong {
          margin-top: 2px;
          color: #4338ca;
          font-size: 7px;
        }

        .agentRecommendationProbability strong {
          margin-top: 2px;
          color: #111827;
          font-size: 8px;
        }

        .agentRecommendationValue strong {
          margin-top: 2px;
          color: #047857;
          font-size: 8px;
        }

        .agentAutoBadge,
        .agentReviewBadge {
          padding: 4px 6px;
          border-radius: 5px;
          font-size: 5px;
          font-weight: 900;
          letter-spacing: 0.5px;
        }

        .agentAutoBadge {
          color: #047857;
          border: 1px solid #a7f3d0;
          background: #ecfdf5;
        }

        .agentReviewBadge {
          color: #b45309;
          border: 1px solid #fde68a;
          background: #fffbeb;
        }

        .agentSource {
          display: flex;
          gap: 5px;
          align-items: center;
          margin-top: 10px;
          color: #94a3b8;
          font-size: 6px;
        }

        .agentSource strong {
          color: #64748b;
          font-weight: 800;
        }

        .preRun {
          position: relative;
          overflow: hidden;
          min-height: 390px;
          display: flex;
          align-items: center;
          margin-bottom: 22px;
          padding: 55px;
          border-radius: 20px;
          color: white;
          background: linear-gradient(135deg, #070b14, #111827 55%, #1e1b4b);
          box-shadow: 0 25px 60px rgba(15, 23, 42, 0.18);
        }

        .preRunGlow {
          position: absolute;
          right: -80px;
          top: -120px;
          width: 400px;
          height: 400px;
          border-radius: 50%;
          background: rgba(99, 102, 241, 0.2);
          filter: blur(60px);
        }

        .preRunContent {
          position: relative;
          z-index: 2;
          max-width: 700px;
        }

        .eyebrow.dark {
          color: #a5b4fc;
        }

        .preRun h2 {
          margin: 10px 0 14px;
          font-size: 43px;
          line-height: 1.02;
          letter-spacing: -1.8px;
        }

        .preRun h2 span {
          color: #a5b4fc;
        }

        .preRun p {
          max-width: 620px;
          margin: 0;
          color: #aeb9ca;
          font-size: 12px;
          line-height: 1.7;
        }

        .primaryLargeButton {
          display: inline-flex;
          align-items: center;
          gap: 25px;
          margin-top: 25px;
          padding: 13px 17px;
          border-radius: 9px;
          font-size: 10px;
        }

        .primaryLargeButton span {
          font-size: 15px;
        }

        .preRunMeta {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 18px;
          color: #8794a8;
          font-size: 8px;
        }

        .preRunMeta > span:first-child {
          color: #34d399;
        }

        .metaDivider {
          color: #475569;
        }

        .commandCenter {
          position: relative;
          overflow: hidden;
          padding: 28px;
          margin-bottom: 20px;
          border-radius: 19px;
          color: white;
          background: linear-gradient(135deg, #080d18, #101827 52%, #172554);
          box-shadow: 0 22px 55px rgba(15, 23, 42, 0.18);
        }

        .commandGlow {
          position: absolute;
          border-radius: 50%;
          filter: blur(55px);
          pointer-events: none;
        }

        .glowOne {
          width: 230px;
          height: 230px;
          right: -80px;
          top: -100px;
          background: rgba(99, 102, 241, 0.22);
        }

        .glowTwo {
          width: 180px;
          height: 180px;
          left: 35%;
          bottom: -140px;
          background: rgba(59, 130, 246, 0.1);
        }

        .commandHeader {
          position: relative;
          z-index: 2;
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 25px;
          margin-bottom: 23px;
        }

        .commandEyebrow,
        .miniLabel,
        .insightEyebrow {
          color: #a5b4fc;
          font-size: 8px;
          font-weight: 900;
          letter-spacing: 1.3px;
        }

        .commandHeader h2 {
          margin: 8px 0 0;
          font-size: 28px;
          letter-spacing: -1px;
        }

        .commandHeader p {
          max-width: 720px;
          margin: 8px 0 0;
          color: #aeb9ca;
          font-size: 10px;
          line-height: 1.65;
        }

        .agentLive {
          display: flex;
          align-items: center;
          gap: 9px;
          padding: 9px 12px;
          border: 1px solid rgba(255,255,255,0.09);
          border-radius: 9px;
          background: rgba(255,255,255,0.045);
          white-space: nowrap;
        }

        .agentLive strong,
        .agentLive small {
          display: block;
        }

        .agentLive strong {
          font-size: 8px;
        }

        .agentLive small {
          margin-top: 3px;
          color: #8794a8;
          font-size: 7px;
        }

        .commandMetrics {
          position: relative;
          z-index: 2;
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 9px;
        }

        .commandMetric {
          min-height: 120px;
          padding: 16px;
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 11px;
          background: rgba(255,255,255,0.045);
        }

        .commandMetric.featured {
          border-color: rgba(129,140,248,0.3);
          background: linear-gradient(
            145deg,
            rgba(99,102,241,0.24),
            rgba(255,255,255,0.04)
          );
        }

        .commandMetricLabel {
          color: #94a3b8;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.8px;
        }

        .commandMetricValue {
          margin-top: 15px;
          font-size: 23px;
          font-weight: 900;
          letter-spacing: -0.7px;
        }

        .commandMetricDescription {
          margin-top: 6px;
          color: #77869b;
          font-size: 7px;
        }

        .commandBottom {
          position: relative;
          z-index: 2;
          display: grid;
          grid-template-columns: 140px 1fr 1.55fr;
          gap: 10px;
          margin-top: 10px;
        }

        .opportunityCard,
        .commandExplanation {
          min-height: 140px;
          border: 1px solid rgba(255,255,255,0.08);
          border-radius: 11px;
          background: rgba(255,255,255,0.04);
        }

        .opportunityCard {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .opportunityRing {
          width: 104px;
          height: 104px;
          padding: 7px;
          border-radius: 50%;
        }

        .ringInner {
          width: 100%;
          height: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          background: #111827;
        }

        .ringInner strong {
          font-size: 23px;
        }

        .ringInner span {
          margin-top: 2px;
          color: #8794a8;
          font-size: 6px;
          font-weight: 900;
          letter-spacing: 0.8px;
        }

        .decisionCards {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 9px;
        }

        .decisionCard {
          min-height: 140px;
          display: flex;
          gap: 10px;
          padding: 16px;
          border-radius: 11px;
        }

        .autoDecision {
          border: 1px solid rgba(52,211,153,0.2);
          background: rgba(5,46,27,0.55);
        }

        .reviewDecision {
          border: 1px solid rgba(251,191,36,0.2);
          background: rgba(69,43,8,0.55);
        }

        .decisionIcon {
          width: 27px;
          height: 27px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          background: rgba(255,255,255,0.07);
          font-size: 11px;
          font-weight: 900;
        }

        .decisionCard span,
        .decisionCard small {
          display: block;
        }

        .decisionCard span {
          color: #94a3b8;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.7px;
        }

        .decisionCard strong {
          display: block;
          margin-top: 8px;
          font-size: 24px;
        }

        .decisionCard small {
          margin-top: 3px;
          color: #8b98aa;
          font-size: 7px;
        }

        .commandExplanation {
          padding: 16px;
        }

        .commandExplanation p {
          margin: 8px 0 12px;
          color: #aeb9ca;
          font-size: 8px;
          line-height: 1.65;
        }

        .guardrailTag {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 8px;
          border: 1px solid rgba(52,211,153,0.15);
          border-radius: 6px;
          color: #6ee7b7;
          background: rgba(52,211,153,0.07);
          font-size: 7px;
          font-weight: 800;
        }

        .workflowCard,
        .card,
        .analysisCard,
        .intelligenceCard,
        .metricCard {
          border: 1px solid #dfe5ec;
          background: rgba(255,255,255,0.97);
          box-shadow: 0 3px 13px rgba(15,23,42,0.035);
        }

        .workflowCard {
          padding: 22px 24px;
          margin-bottom: 20px;
          border-radius: 14px;
        }

        .workflowHeader {
          display: flex;
          justify-content: space-between;
          gap: 20px;
          margin-bottom: 22px;
        }

        .workflowHeader h2,
        .sectionHeader h2 {
          margin: 0;
          color: #111827;
          font-size: 18px;
          letter-spacing: -0.4px;
        }

        .workflowBadge,
        .countBadge,
        .decisionBadge,
        .smallBadge {
          align-self: flex-start;
          padding: 6px 8px;
          border-radius: 6px;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.5px;
          white-space: nowrap;
        }

        .workflowBadge,
        .countBadge,
        .smallBadge {
          color: #475569;
          background: #f1f5f9;
        }

        .workflow {
          display: flex;
          align-items: center;
        }

        .workflowStep {
          min-width: 120px;
          text-align: center;
        }

        .workflowNumber {
          width: 37px;
          height: 37px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 7px;
          border-radius: 10px;
          color: white;
          background: #111827;
          font-size: 8px;
          font-weight: 900;
        }

        .workflowTitle {
          color: #111827;
          font-size: 10px;
          font-weight: 900;
        }

        .workflowDescription {
          margin-top: 3px;
          color: #94a3b8;
          font-size: 7px;
        }

        .workflowLine {
          flex: 1;
          height: 1px;
          margin: 0 7px 25px;
          background: linear-gradient(
            90deg,
            #cbd5e1,
            #818cf8,
            #cbd5e1
          );
        }

        .recoveryControlCard {
          margin-bottom: 20px;
          padding: 22px 24px;
          border: 1px solid #dfe5ec;
          border-radius: 14px;
          background: rgba(255,255,255,0.97);
          box-shadow: 0 3px 13px rgba(15,23,42,0.035);
        }

        .controlGrid {
          display: grid;
          grid-template-columns: 1.1fr 1fr;
          gap: 12px;
          margin-top: 20px;
        }

        .controlPanel,
        .workflowDecisionPanel {
          padding: 17px;
          border: 1px solid #e5e7eb;
          border-radius: 11px;
          background: #f8fafc;
        }

        .controlLabel,
        .miniLabel {
          color: #64748b;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 1px;
        }

        .paymentSelect {
          width: 100%;
          margin-top: 9px;
          padding: 11px 12px;
          border: 1px solid #dbe2ea;
          border-radius: 8px;
          outline: none;
          color: #172033;
          background: white;
          font-size: 9px;
          font-weight: 700;
        }

        .workflowRunButton {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-top: 10px;
          padding: 11px 13px;
          border: none;
          border-radius: 8px;
          color: white;
          background: linear-gradient(135deg, #111827, #4338ca);
          cursor: pointer;
          font-size: 9px;
          font-weight: 900;
        }

        .controlNote {
          display: flex;
          align-items: center;
          gap: 6px;
          margin-top: 10px;
          color: #64748b;
          font-size: 7px;
        }

        .controlNote span {
          color: #059669;
          font-weight: 900;
        }

        .workflowDecisionPanel {
          background: linear-gradient(145deg, #f7f8ff, #ffffff);
        }

        .workflowDecision {
          display: inline-flex;
          margin-top: 10px;
          padding: 7px 9px;
          border-radius: 7px;
          font-size: 8px;
          font-weight: 900;
          letter-spacing: 0.6px;
        }

        .workflowDecision.pending,
        .workflowDecision.continue {
          color: #92400e;
          background: #fef3c7;
        }

        .workflowDecision.human_review,
        .workflowDecision.stop {
          color: #991b1b;
          background: #fee2e2;
        }

        .workflowDecision.success {
          color: #166534;
          background: #dcfce7;
        }

        .workflowReason {
          margin: 10px 0 8px;
          color: #475569;
          font-size: 9px;
          line-height: 1.55;
        }

        .workflowDecisionMeta {
          display: flex;
          gap: 7px;
          flex-wrap: wrap;
        }

        .workflowDecisionMeta span {
          padding: 5px 7px;
          border: 1px solid #e2e8f0;
          border-radius: 6px;
          color: #64748b;
          background: white;
          font-size: 7px;
          font-weight: 800;
        }

        .workflowEmpty {
          margin-top: 14px;
          color: #94a3b8;
          font-size: 9px;
          line-height: 1.5;
        }

        .attemptHeader {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 15px;
          margin-top: 20px;
          margin-bottom: 10px;
        }

        .attemptHeader strong,
        .attemptHeader span {
          display: block;
        }

        .attemptHeader strong {
          color: #111827;
          font-size: 10px;
        }

        .attemptHeader > div > span {
          margin-top: 3px;
          color: #94a3b8;
          font-size: 7px;
        }

        .attemptTimeline {
          display: grid;
          gap: 7px;
        }

        .attemptRow {
          display: grid;
          grid-template-columns: 31px 1fr auto auto;
          align-items: center;
          gap: 10px;
          padding: 10px;
          border: 1px solid #e5e7eb;
          border-radius: 9px;
          background: white;
        }

        .attemptNumber {
          width: 27px;
          height: 27px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 7px;
          color: white;
          background: #111827;
          font-size: 8px;
          font-weight: 900;
        }

        .attemptMain strong,
        .attemptMain small {
          display: block;
        }

        .attemptMain strong {
          color: #1e293b;
          font-size: 9px;
        }

        .attemptMain small {
          margin-top: 3px;
          color: #94a3b8;
          font-size: 7px;
        }

        .attemptStatus {
          padding: 5px 7px;
          border-radius: 6px;
          font-size: 7px;
          font-weight: 900;
        }

        .attemptStatus.pending {
          color: #92400e;
          background: #fef3c7;
        }

        .attemptStatus.failed {
          color: #991b1b;
          background: #fee2e2;
        }

        .attemptStatus.success {
          color: #166534;
          background: #dcfce7;
        }

        .attemptActions {
          display: flex;
          gap: 5px;
        }

        .attemptSuccessButton,
        .attemptFailButton {
          padding: 6px 8px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 7px;
          font-weight: 900;
        }

        .attemptSuccessButton {
          border: 1px solid #bbf7d0;
          color: #166534;
          background: #f0fdf4;
        }

        .attemptFailButton {
          border: 1px solid #fecaca;
          color: #991b1b;
          background: #fff7f7;
        }

        .attemptEmpty {
          padding: 17px;
          border: 1px dashed #cbd5e1;
          border-radius: 9px;
          color: #94a3b8;
          background: #f8fafc;
          font-size: 8px;
        }

        .demoGuardrail {
          display: flex;
          gap: 10px;
          align-items: center;
          margin-top: 12px;
          padding: 9px 10px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #f8fafc;
        }

        .demoGuardrail span {
          color: #6366f1;
          font-size: 6px;
          font-weight: 900;
          letter-spacing: 0.8px;
          white-space: nowrap;
        }

        .demoGuardrail p {
          margin: 0;
          color: #64748b;
          font-size: 7px;
          line-height: 1.5;
        }

        .metricsGrid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 13px;
          margin-bottom: 20px;
        }

        .metricCard {
          padding: 18px;
          border-radius: 12px;
          transition: 0.18s ease;
        }

        .metricCard:hover,
        .intelligenceCard:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 25px rgba(15,23,42,0.07);
        }

        .metricTop {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .metricTitle {
          color: #64748b;
          font-size: 9px;
          font-weight: 800;
        }

        .metricIcon {
          width: 29px;
          height: 29px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          color: #4338ca;
          background: #eef2ff;
          font-size: 10px;
          font-weight: 900;
        }

        .metricValue {
          color: #111827;
          font-size: 25px;
          font-weight: 900;
          letter-spacing: -0.7px;
        }

        .metricSubtitle {
          margin-top: 5px;
          color: #94a3b8;
          font-size: 8px;
        }

        .intelligenceGrid {
          display: grid;
          grid-template-columns: 1.2fr 1fr 1fr;
          gap: 13px;
          margin-bottom: 20px;
        }

        .intelligenceCard {
          padding: 20px;
          border-radius: 13px;
          transition: 0.18s ease;
        }

        .featuredInsight {
          border-color: #c7d2fe;
          background: linear-gradient(145deg, #f7f8ff, white);
        }

        .intelligenceCard h3 {
          margin: 8px 0 18px;
          color: #111827;
          font-size: 13px;
        }

        .insightEyebrow {
          color: #6366f1;
        }

        .insightCustomer,
        .customerCell,
        .queueCustomer {
          display: flex;
          align-items: center;
          gap: 9px;
        }

        .customerAvatar {
          width: 31px;
          height: 31px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          border-radius: 8px;
          color: #4338ca;
          background: #eef2ff;
          font-size: 9px;
          font-weight: 900;
        }

        .customerAvatar.large {
          width: 38px;
          height: 38px;
        }

        .insightCustomer strong,
        .insightCustomer small,
        .customerCell strong,
        .customerCell small,
        .queueCustomer strong,
        .queueCustomer small {
          display: block;
        }

        .insightCustomer strong,
        .customerCell strong,
        .queueCustomer strong {
          color: #1e293b;
          font-size: 9px;
        }

        .insightCustomer small,
        .customerCell small,
        .queueCustomer small {
          margin-top: 3px;
          color: #94a3b8;
          font-size: 7px;
        }

        .insightValue {
          margin-top: 17px;
          color: #047857;
          font-size: 24px;
          font-weight: 900;
        }

        .insightLabel {
          margin-top: 3px;
          color: #94a3b8;
          font-size: 6px;
          font-weight: 900;
          letter-spacing: 0.6px;
        }

        .pathIcon {
          width: 38px;
          height: 38px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 9px;
          color: #4338ca;
          background: #eef2ff;
          font-size: 14px;
          font-weight: 900;
        }

        .pathValue {
          margin-top: 12px;
          color: #111827;
          font-size: 15px;
          font-weight: 900;
        }

        .pathProbability {
          margin-top: 12px;
        }

        .pathProbability > span {
          color: #047857;
          font-size: 12px;
          font-weight: 900;
        }

        .pathProbability > div {
          height: 5px;
          margin-top: 6px;
          overflow: hidden;
          border-radius: 99px;
          background: #e2e8f0;
        }

        .pathProbability > div > div {
          height: 100%;
          border-radius: 99px;
          background: #10b981;
        }

        .pathProbability small {
          display: block;
          margin-top: 4px;
          color: #94a3b8;
          font-size: 7px;
        }

        .coverageRow {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }

        .coverageRow > div {
          padding: 10px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #f8fafc;
        }

        .coverageRow strong,
        .coverageRow span {
          display: block;
        }

        .coverageRow strong {
          color: #111827;
          font-size: 17px;
        }

        .coverageRow span {
          margin-top: 3px;
          color: #94a3b8;
          font-size: 7px;
        }

        .coverageBar {
          height: 5px;
          margin-top: 12px;
          overflow: hidden;
          border-radius: 99px;
          background: #e2e8f0;
        }

        .coverageBar > div {
          height: 100%;
          border-radius: 99px;
          background: #10b981;
        }

        .intelligenceCard p {
          margin: 7px 0 0;
          color: #64748b;
          font-size: 8px;
          line-height: 1.55;
        }

        .card,
        .analysisCard {
          padding: 23px;
          margin-bottom: 20px;
          border-radius: 13px;
        }

        .analysisCard {
          border-left: 4px solid #4f46e5;
        }

        .sectionHeader {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 20px;
          margin-bottom: 19px;
        }

        .eyebrow {
          display: block;
          margin-bottom: 6px;
          color: #4f46e5;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 1.3px;
        }

        .sectionHeader p {
          margin: 5px 0 0;
          color: #64748b;
          font-size: 9px;
          line-height: 1.55;
        }

        .decisionBadge {
          color: #4338ca;
          border: 1px solid #c7d2fe;
          background: #eef2ff;
        }

        /* MODEL EVALUATION */

        .modelEvaluationCard {
          background: linear-gradient(145deg, #ffffff, #f8faff);
        }

        .modelIdentity {
          display: grid;
          grid-template-columns: 1.5fr 1fr 1fr 1.5fr;
          gap: 9px;
          margin-bottom: 22px;
        }

        .modelIdentity > div {
          padding: 13px;
          border: 1px solid #e2e8f0;
          border-radius: 9px;
          background: #f8fafc;
        }

        .modelIdentity span,
        .modelIdentity strong,
        .modelIdentity small {
          display: block;
        }

        .modelIdentity span {
          color: #64748b;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.7px;
        }

        .modelIdentity strong {
          margin-top: 7px;
          color: #111827;
          font-size: 15px;
        }

        .modelIdentity small {
          margin-top: 4px;
          color: #94a3b8;
          font-size: 7px;
        }

        .modelReliability {
          border-color: #c7d2fe !important;
          background: #f5f3ff !important;
        }

        .modelReliability strong {
          color: #4338ca;
        }

        .evaluationSectionTitle {
          margin-bottom: 9px;
          color: #64748b;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 1px;
        }

        .evaluationMetrics {
          display: grid;
          grid-template-columns: repeat(7, 1fr);
          gap: 8px;
        }

        .evaluationMetric {
          min-height: 91px;
          padding: 13px;
          border: 1px solid #e2e8f0;
          border-radius: 9px;
          background: white;
        }

        .evaluationMetric.featured {
          border-color: #c7d2fe;
          background: #f5f3ff;
        }

        .evaluationMetric.inverse {
          background: #f8fafc;
        }

        .evaluationMetric span {
          color: #64748b;
          font-size: 7px;
          font-weight: 900;
          letter-spacing: 0.6px;
        }

        .evaluationMetric strong {
          display: block;
          margin-top: 13px;
          color: #111827;
          font-size: 20px;
          font-weight: 900;
        }

        .evaluationMetric.featured strong {
          color: #4338ca;
        }

        .evaluationLowerGrid {
          display: grid;
          grid-template-columns: 1fr 1.2fr;
          gap: 10px;
          margin-top: 10px;
        }

        .evaluationPanel,
        .calibrationPanel {
          padding: 16px;
          border: 1px solid #e2e8f0;
          border-radius: 10px;
          background: white;
        }

        .evaluationPanelHeader {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 15px;
          margin-bottom: 15px;
        }

        .evaluationPanelHeader h3 {
          margin: 5px 0 0;
          color: #111827;
          font-size: 12px;
        }

        .evaluationPanelHeader .eyebrow {
          margin-bottom: 0;
        }

        .smallBadge {
          border: 1px solid #e2e8f0;
          font-size: 6px;
        }

        .cvGrid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 7px;
        }

        .miniMetric {
          padding: 9px;
          border: 1px solid #edf1f5;
          border-radius: 7px;
          background: #f8fafc;
        }

        .miniMetric span,
        .miniMetric strong {
          display: block;
        }

        .miniMetric span {
          color: #64748b;
          font-size: 6px;
          font-weight: 900;
        }

        .miniMetric strong {
          margin-top: 5px;
          color: #111827;
          font-size: 14px;
        }

        .gapBox {
          margin-top: 9px;
          padding: 9px;
          border-radius: 7px;
          background: #f8fafc;
        }

        .gapBox span {
          color: #64748b;
          font-size: 6px;
          font-weight: 900;
        }

        .gapBox strong {
          float: right;
          color: #4338ca;
          font-size: 9px;
        }

        .gapTrack {
          clear: both;
          height: 4px;
          margin-top: 8px;
          overflow: hidden;
          border-radius: 99px;
          background: #e2e8f0;
        }

        .gapTrack > div {
          height: 100%;
          border-radius: 99px;
          background: #6366f1;
        }

        .modelComparison {
          display: grid;
          gap: 11px;
        }

        .modelComparisonRow {
          display: grid;
          grid-template-columns: 1.35fr 1fr 55px;
          align-items: center;
          gap: 8px;
        }

        .modelComparisonName strong,
        .modelComparisonName small {
          display: block;
        }

        .modelComparisonName strong {
          color: #1e293b;
          font-size: 8px;
        }

        .modelComparisonName small {
          margin-top: 2px;
          color: #94a3b8;
          font-size: 6px;
        }

        .modelScoreTrack {
          height: 5px;
          overflow: hidden;
          border-radius: 99px;
          background: #e2e8f0;
        }

        .modelScoreTrack > div {
          height: 100%;
          border-radius: 99px;
          background: #6366f1;
        }

        .modelScore {
          color: #111827;
          text-align: right;
          font-size: 8px;
        }

        .calibrationPanel {
          margin-top: 10px;
        }

        .calibrationTable {
          display: grid;
          gap: 1px;
          overflow: hidden;
          border: 1px solid #edf1f5;
          border-radius: 8px;
        }

        .calibrationHeader,
        .calibrationRow {
          display: grid;
          grid-template-columns: 1.3fr 0.7fr 0.8fr 0.8fr 1.2fr;
          gap: 8px;
          align-items: center;
          padding: 8px 10px;
        }

        .calibrationHeader {
          color: #64748b;
          background: #f8fafc;
          font-size: 6px;
          font-weight: 900;
          text-transform: uppercase;
        }

        .calibrationRow {
          border-top: 1px solid #edf1f5;
          color: #475569;
          font-size: 7px;
          background: white;
        }

        .calibrationRow strong {
          color: #111827;
        }

        .calibrationTrack {
          height: 4px;
          overflow: hidden;
          border-radius: 99px;
          background: #e2e8f0;
        }

        .calibrationTrack > div {
          height: 100%;
          border-radius: 99px;
          background: #10b981;
        }

        .evaluationNote {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          margin-top: 10px;
          padding: 10px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          color: #64748b;
          background: #f8fafc;
        }

        .evaluationNote span {
          color: #6366f1;
          font-size: 10px;
        }

        .evaluationNote p {
          margin: 0;
          font-size: 7px;
          line-height: 1.5;
        }

        /* TABLE */

        .tableWrapper {
          overflow-x: auto;
          border: 1px solid #edf1f5;
          border-radius: 9px;
        }

        table {
          width: 100%;
          min-width: 780px;
          border-collapse: collapse;
        }

        th {
          padding: 10px;
          color: #64748b;
          background: #f8fafc;
          border-bottom: 1px solid #e2e8f0;
          text-align: left;
          font-size: 7px;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 0.45px;
          white-space: nowrap;
        }

        td {
          padding: 12px 10px;
          border-bottom: 1px solid #edf1f5;
          color: #334155;
          font-size: 9px;
          vertical-align: middle;
        }

        tbody tr:hover {
          background: #fafbff;
        }

        tbody tr:last-child td {
          border-bottom: none;
        }

        .queueRank {
          color: #94a3b8;
          font-family: monospace;
          font-size: 9px;
          font-weight: 800;
        }

        .amount {
          color: #111827;
          font-size: 10px;
        }

        .failureBadge {
          display: inline-block;
          padding: 4px 6px;
          border: 1px solid #fed7aa;
          border-radius: 5px;
          color: #c2410c;
          background: #fff7ed;
          font-size: 7px;
          font-weight: 800;
          white-space: nowrap;
        }

        .intervention {
          color: #4338ca;
          font-size: 8px;
          white-space: nowrap;
        }

        .probability {
          min-width: 75px;
        }

        .probability strong {
          color: #111827;
          font-size: 9px;
        }

        .probabilityBar {
          width: 65px;
          height: 4px;
          margin-top: 5px;
          overflow: hidden;
          border-radius: 99px;
          background: #e2e8f0;
        }

        .probabilityFill {
          height: 100%;
          border-radius: 99px;
          background: #4f46e5;
        }

        .recoveryValue {
          color: #047857;
          font-size: 9px;
          white-space: nowrap;
        }

        .autoBadge,
        .reviewBadge,
        .statusBadge,
        .recommendedBadge {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 4px 6px;
          border-radius: 5px;
          font-size: 7px;
          font-weight: 900;
          white-space: nowrap;
        }

        .autoBadge {
          color: #047857;
          border: 1px solid #a7f3d0;
          background: #ecfdf5;
        }

        .reviewBadge {
          color: #b45309;
          border: 1px solid #fde68a;
          background: #fffbeb;
        }

        .statusBadge {
          color: #b91c1c;
          background: #fef2f2;
        }

        .statusSmallDot {
          width: 5px;
          height: 5px;
          border-radius: 50%;
          background: #10b981;
        }

        .statusBadge .statusSmallDot {
          background: #ef4444;
        }

        .actionButtons {
          display: flex;
          gap: 5px;
        }

        .analyzeButton,
        .recoverButton,
        .refreshButton {
          padding: 6px 8px;
          border-radius: 6px;
          font-size: 8px;
          font-weight: 800;
          cursor: pointer;
          transition: 0.15s ease;
        }

        .analyzeButton,
        .refreshButton {
          color: #334155;
          border: 1px solid #cbd5e1;
          background: white;
        }

        .analyzeButton:hover,
        .refreshButton:hover {
          background: #f8fafc;
        }

        .recoverButton {
          color: white;
          border: 1px solid #111827;
          background: #111827;
        }

        .recoverButton:hover {
          background: #374151;
        }

        .recoverButton:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        .analysisGrid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 10px;
        }

        .infoBox {
          padding: 13px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #f8fafc;
        }

        .infoLabel {
          margin-bottom: 6px;
          color: #64748b;
          font-size: 7px;
          font-weight: 800;
          letter-spacing: 0.5px;
          text-transform: uppercase;
        }

        .infoValue {
          color: #111827;
          font-size: 13px;
          font-weight: 900;
        }

        .infoValue.highlight {
          color: #dc2626;
        }

        .reasonBox {
          display: flex;
          gap: 10px;
          align-items: flex-start;
          margin-top: 11px;
          padding: 13px;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          background: #f8fafc;
        }

        .reasonIcon {
          width: 30px;
          height: 30px;
          min-width: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
          color: white;
          background: #111827;
          font-size: 7px;
          font-weight: 900;
        }

        .reasonBox strong {
          color: #111827;
          font-size: 9px;
        }

        .reasonBox p {
          margin: 4px 0 0;
          color: #475569;
          font-size: 9px;
          line-height: 1.55;
        }

        .explainFooter {
          display: flex;
          gap: 18px;
          margin-top: 11px;
          color: #047857;
          font-size: 7px;
          font-weight: 800;
        }

        .paymentId {
          color: #64748b;
          font-family: monospace;
          font-size: 8px;
        }

        .priorityHigh,
        .priorityNormal {
          padding: 4px 6px;
          border-radius: 5px;
          font-size: 7px;
          font-weight: 900;
        }

        .priorityHigh {
          color: #dc2626;
          border: 1px solid #fecaca;
          background: #fef2f2;
        }

        .priorityNormal {
          color: #475569;
          background: #f1f5f9;
        }

        .score {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .score > span {
          min-width: 20px;
          color: #111827;
          font-size: 8px;
          font-weight: 800;
        }

        .scoreBar {
          width: 45px;
          height: 4px;
          overflow: hidden;
          border-radius: 99px;
          background: #e2e8f0;
        }

        .scoreFill {
          height: 100%;
          border-radius: 99px;
          background: #4f46e5;
        }

        .recommendedBadge {
          color: #047857;
          border: 1px solid #a7f3d0;
          background: #ecfdf5;
        }

        .createdAt {
          color: #64748b;
          font-size: 7px;
        }

        .loading,
        .emptyState {
          padding: 38px;
          text-align: center;
          color: #64748b;
          font-size: 9px;
        }

        .loadingSpinner {
          width: 18px;
          height: 18px;
          margin: 0 auto 8px;
          border: 2px solid #e2e8f0;
          border-top-color: #4f46e5;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .errorBox {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 18px;
          padding: 11px 14px;
          border: 1px solid #fecdd3;
          border-radius: 9px;
          color: #9f1239;
          background: #fff1f2;
        }

        .errorIcon {
          width: 27px;
          height: 27px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 7px;
          background: #ffe4e6;
          font-weight: 900;
        }

        .errorBox strong,
        .errorBox span {
          display: block;
        }

        .errorBox strong {
          font-size: 9px;
        }

        .errorBox span {
          margin-top: 2px;
          font-size: 8px;
        }

        footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 15px;
          padding: 6px 2px;
          color: #94a3b8;
          font-size: 7px;
        }

        .footerBrand {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #475569;
        }

        .footerLogo {
          width: 21px;
          height: 21px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 5px;
          color: white;
          background: #111827;
          font-size: 6px;
          font-weight: 900;
        }

        @media (max-width: 1100px) {
          .commandMetrics {
            grid-template-columns: repeat(2, 1fr);
          }

          .commandBottom {
            grid-template-columns: 130px 1fr;
          }

          .commandExplanation {
            grid-column: 1 / -1;
          }

          .intelligenceGrid {
            grid-template-columns: 1fr 1fr;
          }

          .featuredInsight {
            grid-column: 1 / -1;
          }

          .modelIdentity {
            grid-template-columns: 1fr 1fr;
          }

          .evaluationMetrics {
            grid-template-columns: repeat(4, 1fr);
          }
        }

        @media (max-width: 900px) {
          .metricsGrid {
            grid-template-columns: repeat(2, 1fr);
          }

          .analysisGrid {
            grid-template-columns: repeat(2, 1fr);
          }

          .evaluationLowerGrid {
            grid-template-columns: 1fr;
          }

          .workflow {
            overflow-x: auto;
            padding-bottom: 8px;
          }
        }

        @media (max-width: 700px) {
          .agentCopilotHeader {
            flex-direction: column;
          }

          .agentPromptRow {
            grid-template-columns: 1fr;
          }

          .agentAskButton {
            width: 100%;
          }

          .agentMetricStrip {
            grid-template-columns: repeat(2, 1fr);
          }

          .agentRecommendation {
            grid-template-columns: 24px 1fr 1fr;
          }

          .agentRecommendationProbability,
          .agentRecommendationValue,
          .agentRecommendation > .agentAutoBadge,
          .agentRecommendation > .agentReviewBadge {
            display: none;
          }

          .agentCopilotHeader {
            margin-bottom: 2px;
          }

          .dashboard {
            padding: 20px 13px 45px;
          }

          .header {
            flex-direction: column;
            align-items: flex-start;
          }

          .headerRight {
            width: 100%;
            justify-content: space-between;
          }

          .commandHeader {
            flex-direction: column;
          }

          .commandMetrics {
            grid-template-columns: 1fr;
          }

          .commandBottom {
            grid-template-columns: 1fr;
          }

          .decisionCards {
            grid-template-columns: 1fr 1fr;
          }

          .intelligenceGrid {
            grid-template-columns: 1fr;
          }

          .featuredInsight {
            grid-column: auto;
          }

          footer {
            flex-direction: column;
            align-items: flex-start;
          }

          .modelIdentity {
            grid-template-columns: 1fr;
          }

          .evaluationMetrics {
            grid-template-columns: repeat(2, 1fr);
          }

          .calibrationHeader,
          .calibrationRow {
            grid-template-columns: 1.2fr 0.7fr 0.8fr 0.8fr;
          }

          .calibrationHeader span:last-child,
          .calibrationRow .calibrationTrack {
            display: none;
          }
        }

        @media (max-width: 520px) {
          .agentMetricStrip {
            grid-template-columns: 1fr 1fr;
          }

          .agentRecommendation {
            grid-template-columns: 22px 1fr;
          }

          .agentRecommendationIntervention {
            grid-column: 2;
          }

          .agentCopilot {
            padding: 18px;
          }

          .agentGrounded {
            display: none;
          }

          .headerRight {
            flex-direction: column;
            align-items: stretch;
          }

          .systemStatus {
            justify-content: center;
          }

          .agentButton {
            width: 100%;
          }

          .preRun {
            padding: 32px 22px;
          }

          .preRun h2 {
            font-size: 33px;
          }

          .commandCenter {
            padding: 20px;
          }

          .commandHeader h2 {
            font-size: 23px;
          }

          .metricsGrid,
          .analysisGrid,
          .controlGrid {
            grid-template-columns: 1fr;
          }

          .evaluationMetrics {
            grid-template-columns: 1fr 1fr;
          }

          .decisionCards {
            grid-template-columns: 1fr;
          }

          .sectionHeader {
            flex-direction: column;
          }

          .actionButtons {
            flex-direction: column;
          }

          .explainFooter {
            flex-direction: column;
            gap: 6px;
          }

          .attemptRow {
            grid-template-columns: 31px 1fr auto;
          }

          .attemptActions {
            grid-column: 2 / -1;
          }

          .demoGuardrail {
            align-items: flex-start;
            flex-direction: column;
          }
        }
      `}</style>
    </main>
  );
}

/* COMMAND METRIC */

function CommandMetric({
  label,
  value,
  description,
  featured = false,
}: {
  label: string;
  value: string;
  description: string;
  featured?: boolean;
}) {
  return (
    <div className={`commandMetric ${featured ? "featured" : ""}`}>
      <div className="commandMetricLabel">{label}</div>
      <div className="commandMetricValue">{value}</div>
      <div className="commandMetricDescription">{description}</div>
    </div>
  );
}

/* WORKFLOW STEP */

function WorkflowStep({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="workflowStep">
      <div className="workflowNumber">{number}</div>
      <div className="workflowTitle">{title}</div>
      <div className="workflowDescription">{description}</div>
    </div>
  );
}

/* METRIC CARD */

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
        <span className="metricTitle">{title}</span>

        <div className="metricIcon">{icon}</div>
      </div>

      <div className="metricValue">{value}</div>

      <div className="metricSubtitle">{subtitle}</div>
    </div>
  );
}

/* EVALUATION METRIC */

function EvaluationMetric({
  label,
  value,
  featured = false,
  inverse = false,
}: {
  label: string;
  value: number;
  featured?: boolean;
  inverse?: boolean;
}) {
  return (
    <div
      className={`evaluationMetric ${
        featured ? "featured" : ""
      } ${inverse ? "inverse" : ""}`}
    >
      <span>{label}</span>

      <strong>
        {inverse
          ? value.toFixed(3)
          : `${(value * 100).toFixed(1)}%`}
      </strong>
    </div>
  );
}

/* MINI METRIC */

function MiniMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="miniMetric">
      <span>{label}</span>

      <strong>{(value * 100).toFixed(1)}%</strong>
    </div>
  );
}

/* INFO BOX */

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
      <div className="infoLabel">{label}</div>

      <div className={`infoValue ${highlight ? "highlight" : ""}`}>
        {value}
      </div>
    </div>
  );
}

/* LOADING */

function LoadingState({
  text,
}: {
  text: string;
}) {
  return (
    <div className="loading">
      <div className="loadingSpinner" />
      {text}
    </div>
  );
}

/* HELPERS */

function formatStrategy(strategy: string) {
  return strategy
    .split("_")
    .map(
      (word) =>
        word.charAt(0).toUpperCase() + word.slice(1)
    )
    .join(" ");
}

function formatStatus(status: string) {
  return status
    .split("_")
    .map(
      (word) =>
        word.charAt(0).toUpperCase() + word.slice(1)
    )
    .join(" ");
}