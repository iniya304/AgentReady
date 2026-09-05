from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.supabase_client import supabase
from app.recovery_engine import analyze_payment

from ml.recovery_context import get_payment_context
from ml.prediction_service import predict_recovery
from ml.intervention_optimizer import optimize_intervention
from ml.policy_engine import evaluate_policy
from ml.recovery_workflow import get_next_intervention
from ml.recovery_attempt_service import (
    get_recovery_attempts,
    create_recovery_attempt,
    update_recovery_attempt,
)
from ml.batch_recovery_service import analyze_batch_recovery
from ml.audit_service import log_audit_event, get_audit_events
from ml.evaluation_service import get_model_evaluation
from ml.recovery_agent import answer_recovery_question

from razorpay_recovery_service import create_recovery_payment_link


app = FastAPI(title="AgentReady")


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# REQUEST MODELS
# =========================================================

class PaymentCreate(BaseModel):
    customer_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = "INR"
    payment_status: str = "failed"
    failure_reason: str | None = None
    payment_method: str = "card"


class PredictionRequest(BaseModel):
    intervention: str = "retry_later"


class AgentQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class RecoveryAttemptUpdate(BaseModel):
    status: str
    failure_reason: str | None = None


class RecoveryExecutionRequest(BaseModel):
    recovery_action_id: str = Field(min_length=1)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "AgentReady",
        "message": "AgentReady backend is running",
        "running": True,
    }


# =========================================================
# GET PAYMENTS
# =========================================================

@app.get("/payments")
def get_payments():
    try:
        response = (
            supabase
            .table("payments")
            .select("*")
            .execute()
        )

        return {
            "success": True,
            "payments": response.data,
        }

    except Exception as exc:
        print("========== GET PAYMENTS ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("========================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =========================================================
# CREATE PAYMENT
# =========================================================

@app.post("/payments")
def create_payment(payment: PaymentCreate):
    try:
        response = (
            supabase
            .table("payments")
            .insert(payment.model_dump())
            .execute()
        )

        return {
            "success": True,
            "payment": response.data[0],
        }

    except Exception as exc:
        print("========== PAYMENT CREATION ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("============================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =========================================================
# ANALYZE PAYMENT
# =========================================================

@app.post("/payments/{payment_id}/analyze")
def analyze_payment_recovery(payment_id: str):
    try:
        print("========== ANALYZE PAYMENT ==========")
        print("REQUEST ID:", repr(payment_id))

        response = (
            supabase
            .table("payments")
            .select("*")
            .execute()
        )

        payments = response.data

        print("PAYMENTS FOUND:", len(payments))

        payment = next(
            (
                item
                for item in payments
                if str(item.get("id", "")).strip()
                == str(payment_id).strip()
            ),
            None,
        )

        print("MATCHED PAYMENT:", payment)

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        analysis = analyze_payment(payment)

        print("ANALYSIS:", analysis)

        log_audit_event(
            event_type="payment_analysis",
            payment_id=payment_id,
            decision=analysis.get("strategy"),
            intervention=analysis.get("strategy"),
            status="completed",
            reason=analysis.get("reasoning"),
            metadata={
                "priority": analysis.get("priority"),
                "priority_score": analysis.get("priority_score"),
                "amount": payment.get("amount"),
                "currency": payment.get("currency"),
                "failure_reason": payment.get("failure_reason"),
            },
        )

        print("====================================")

        return {
            "success": True,
            "analysis": analysis,
        }

    except HTTPException:
        raise

    except Exception as exc:
        print("========== ANALYSIS ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("====================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =========================================================
# ML RECOVERY PREDICTION
# =========================================================

@app.post("/payments/{payment_id}/predict")
def predict_payment_recovery(
    payment_id: str,
    request: PredictionRequest,
):
    try:
        print("========== ML RECOVERY PREDICTION ==========")
        print("PAYMENT ID:", repr(payment_id))
        print("INTERVENTION:", request.intervention)

        context = get_payment_context(
            payment_id=payment_id,
            intervention=request.intervention,
        )

        print("ML CONTEXT CREATED")
        print("CUSTOMER:", context.get("customer_id"))
        print("AMOUNT:", context.get("amount"))
        print("FAILURE:", context.get("failure_reason"))

        prediction = predict_recovery(context)

        print("ML PREDICTION:", prediction)

        log_audit_event(
            event_type="ml_recovery_prediction",
            payment_id=payment_id,
            intervention=request.intervention,
            status="completed",
            reason="Recovery probability generated by trained ML model",
            metadata={
                "prediction": prediction,
                "customer_id": context.get("customer_id"),
                "amount": context.get("amount"),
                "failure_reason": context.get("failure_reason"),
            },
        )

        print("============================================")

        return {
            "success": True,
            "payment_id": payment_id,
            "intervention": request.intervention,
            "prediction": prediction,
        }

    except ValueError as exc:
        print("ML CONTEXT ERROR:", repr(exc))

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print("========== ML PREDICTION ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("=========================================")

        raise HTTPException(
            status_code=500,
            detail="Unable to generate recovery prediction",
        ) from exc


# =========================================================
# INTERVENTION OPTIMIZER + POLICY ENGINE
# =========================================================

@app.post("/payments/{payment_id}/optimize")
def optimize_payment_recovery(payment_id: str):
    try:
        print("========== OPTIMIZE RECOVERY ==========")
        print("PAYMENT ID:", repr(payment_id))

        context = get_payment_context(
            payment_id=payment_id,
            intervention="retry_later",
        )

        print("PAYMENT CONTEXT CREATED")
        print("CUSTOMER:", context.get("customer_id"))
        print("AMOUNT:", context.get("amount"))
        print("FAILURE:", context.get("failure_reason"))

        optimization = optimize_intervention(context)

        print("OPTIMIZATION RESULT:", optimization)

        policy = evaluate_policy(
            payment_context=context,
            optimization=optimization,
        )

        print("POLICY RESULT:", policy)

        selected_intervention = None

        if isinstance(optimization, dict):
            selected_intervention = (
                optimization.get("selected_intervention")
                or optimization.get("best_intervention")
                or optimization.get("recommended_intervention")
            )

        policy_decision = None

        if isinstance(policy, dict):
            policy_decision = (
                policy.get("decision")
                or policy.get("action")
                or policy.get("policy_decision")
            )

        log_audit_event(
            event_type="intervention_optimization",
            payment_id=payment_id,
            decision=policy_decision,
            intervention=selected_intervention,
            status="completed",
            reason=(
                "Candidate recovery interventions evaluated "
                "and policy guardrails applied"
            ),
            metadata={
                "optimization": optimization,
                "policy": policy,
                "customer_id": context.get("customer_id"),
                "amount": context.get("amount"),
                "failure_reason": context.get("failure_reason"),
            },
        )

        print("======================================")

        return {
            "success": True,
            "payment_id": payment_id,
            "optimization": optimization,
            "policy": policy,
        }

    except ValueError as exc:
        print("OPTIMIZATION CONTEXT ERROR:", repr(exc))

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print("========== OPTIMIZATION ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("=========================================")

        raise HTTPException(
            status_code=500,
            detail="Unable to optimize recovery intervention",
        ) from exc


# =========================================================
# RECOVER PAYMENT
# =========================================================

@app.post("/payments/{payment_id}/recover")
def recover_payment(payment_id: str):
    try:
        print("========== RECOVER PAYMENT ==========")
        print("REQUEST ID:", repr(payment_id))

        response = (
            supabase
            .table("payments")
            .select("*")
            .execute()
        )

        payments = response.data

        print("PAYMENTS FOUND:", len(payments))

        payment = next(
            (
                item
                for item in payments
                if str(item.get("id", "")).strip()
                == str(payment_id).strip()
            ),
            None,
        )

        print("MATCHED PAYMENT:", payment)

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        analysis = analyze_payment(payment)

        print("ANALYSIS:", analysis)

        existing_response = (
            supabase
            .table("recovery_actions")
            .select("*")
            .eq("payment_id", payment["id"])
            .eq("status", "recommended")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        existing_actions = existing_response.data or []

        if existing_actions:
            existing_action = existing_actions[0]

            print("EXISTING RECOVERY ACTION FOUND:")
            print(existing_action)
            print("NO DUPLICATE ACTION CREATED")

            log_audit_event(
                event_type="recovery_recommendation_reused",
                payment_id=payment["id"],
                intervention=existing_action["strategy"],
                status=existing_action["status"],
                reason=(
                    "Existing recovery recommendation reused "
                    "to prevent duplicate actions"
                ),
                metadata={
                    "recovery_action_id": existing_action["id"],
                    "priority": existing_action["priority"],
                    "priority_score": existing_action["priority_score"],
                    "amount": payment.get("amount"),
                    "currency": payment.get("currency"),
                },
            )

            print("====================================")

            return {
                "success": True,
                "payment_id": payment["id"],
                "action": existing_action["strategy"],
                "priority": existing_action["priority"],
                "priority_score": existing_action["priority_score"],
                "recovery_action_id": existing_action["id"],
                "status": existing_action["status"],
                "already_exists": True,
                "message": (
                    f"Recovery action '{existing_action['strategy']}' "
                    "already exists and is ready to execute."
                ),
            }

        recovery_data = {
            "payment_id": payment["id"],
            "strategy": analysis["strategy"],
            "priority": analysis["priority"],
            "priority_score": analysis["priority_score"],
            "status": "recommended",
        }

        print("CREATING NEW RECOVERY DATA:")
        print(recovery_data)

        recovery_response = (
            supabase
            .table("recovery_actions")
            .insert(recovery_data)
            .execute()
        )

        print(
            "RECOVERY ACTION RESPONSE:",
            recovery_response.data,
        )

        if not recovery_response.data:
            raise HTTPException(
                status_code=500,
                detail="Recovery action was not saved",
            )

        saved_action = recovery_response.data[0]

        print("SAVED ACTION:", saved_action)

        log_audit_event(
            event_type="recovery_recommendation_created",
            payment_id=payment["id"],
            intervention=analysis["strategy"],
            status=saved_action["status"],
            reason=analysis.get("reasoning"),
            metadata={
                "recovery_action_id": saved_action["id"],
                "priority": analysis["priority"],
                "priority_score": analysis["priority_score"],
                "amount": payment.get("amount"),
                "currency": payment.get("currency"),
                "failure_reason": payment.get("failure_reason"),
            },
        )

        print("====================================")

        return {
            "success": True,
            "payment_id": payment["id"],
            "action": analysis["strategy"],
            "priority": analysis["priority"],
            "priority_score": analysis["priority_score"],
            "recovery_action_id": saved_action["id"],
            "status": saved_action["status"],
            "already_exists": False,
            "message": (
                f"Recovery action '{analysis['strategy']}' "
                "is ready to execute."
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        print("========== RECOVERY ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("====================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =========================================================
# EXECUTE GOVERNED RAZORPAY RECOVERY
# =========================================================

@app.post("/payments/{payment_id}/recovery-actions/execute")
def execute_recovery_action(
    payment_id: str,
    request: RecoveryExecutionRequest,
):
    """
    Execute a governed recovery action through Razorpay Test Mode.

    Governance:
    - Payment must exist.
    - Recovery action must belong to the payment.
    - Existing provider executions are reused.
    - Successful previous recovery stops execution.
    - Pending attempts block duplicate execution.
    - Maximum recovery attempts are enforced.
    - Policy must allow AUTO_EXECUTE.
    - Only request_alternative_payment has a Razorpay executor.

    This endpoint operates only in Razorpay Test Mode.
    """

    try:
        print("========== EXECUTE RECOVERY ACTION ==========")
        print("PAYMENT ID:", repr(payment_id))
        print(
            "RECOVERY ACTION ID:",
            repr(request.recovery_action_id),
        )

        # -------------------------------------------------
        # 1. Load payment
        # -------------------------------------------------

        payment_response = (
            supabase
            .table("payments")
            .select("*")
            .eq("id", payment_id)
            .limit(1)
            .execute()
        )

        payments = payment_response.data or []

        if not payments:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        payment = payments[0]

        print("PAYMENT FOUND:", payment)

        # -------------------------------------------------
        # 2. Load recovery action
        # -------------------------------------------------

        action_response = (
            supabase
            .table("recovery_actions")
            .select("*")
            .eq("id", request.recovery_action_id)
            .eq("payment_id", payment_id)
            .limit(1)
            .execute()
        )

        actions = action_response.data or []

        if not actions:
            raise HTTPException(
                status_code=404,
                detail="Recovery action not found for this payment",
            )

        recovery_action = actions[0]

        print("RECOVERY ACTION:", recovery_action)

        # -------------------------------------------------
        # 3. Action status validation
        # -------------------------------------------------

        if recovery_action.get("status") != "recommended":
            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "Only recovery actions in recommended "
                        "status can be executed."
                    ),
                    "current_status": recovery_action.get(
                        "status"
                    ),
                },
            )

        # -------------------------------------------------
        # 4. Idempotency check
        # -------------------------------------------------

        if recovery_action.get("provider_reference"):
            print("EXISTING RAZORPAY EXECUTION FOUND")

            return {
                "success": True,
                "payment_id": payment_id,
                "recovery_action_id": recovery_action["id"],
                "already_executed": True,
                "provider": recovery_action.get("provider"),
                "provider_reference": recovery_action.get(
                    "provider_reference"
                ),
                "provider_url": recovery_action.get(
                    "provider_url"
                ),
                "provider_status": recovery_action.get(
                    "provider_status"
                ),
                "message": (
                    "Existing Razorpay recovery action returned. "
                    "No duplicate Payment Link was created."
                ),
            }

        # -------------------------------------------------
        # 5. Load previous recovery attempts
        # -------------------------------------------------

        previous_attempts = get_recovery_attempts(payment_id)

        print(
            "PREVIOUS RECOVERY ATTEMPTS:",
            previous_attempts,
        )

        # -------------------------------------------------
        # 6. Stop if already recovered
        # -------------------------------------------------

        successful_attempts = [
            attempt
            for attempt in previous_attempts
            if attempt.get("status") == "success"
        ]

        if successful_attempts:
            log_audit_event(
                event_type="recovery_execution_blocked",
                payment_id=payment_id,
                intervention=recovery_action.get("strategy"),
                status="blocked",
                reason=(
                    "Recovery execution stopped because a "
                    "previous recovery attempt succeeded"
                ),
                metadata={
                    "recovery_action_id": recovery_action["id"],
                    "successful_attempt_count": len(
                        successful_attempts
                    ),
                },
            )

            raise HTTPException(
                status_code=409,
                detail=(
                    "Recovery execution stopped because "
                    "this payment has already been recovered."
                ),
            )

        # -------------------------------------------------
        # 7. Stop if an attempt is already pending
        # -------------------------------------------------

        pending_attempts = [
            attempt
            for attempt in previous_attempts
            if attempt.get("status") == "pending"
        ]

        if pending_attempts:
            existing_attempt = pending_attempts[-1]

            log_audit_event(
                event_type="recovery_execution_blocked",
                payment_id=payment_id,
                intervention=recovery_action.get("strategy"),
                status="blocked",
                reason=(
                    "Recovery execution stopped because "
                    "another recovery attempt is already pending"
                ),
                metadata={
                    "recovery_action_id": recovery_action["id"],
                    "pending_attempt_id": existing_attempt.get(
                        "id"
                    ),
                },
            )

            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "A recovery attempt is already pending "
                        "for this payment."
                    ),
                    "pending_attempt": existing_attempt,
                },
            )

        # -------------------------------------------------
        # 8. Enforce maximum recovery attempts
        # -------------------------------------------------

        completed_attempts = [
            attempt
            for attempt in previous_attempts
            if attempt.get("status") in {
                "success",
                "failed",
            }
        ]

        if len(completed_attempts) >= 2:
            log_audit_event(
                event_type="recovery_execution_blocked",
                payment_id=payment_id,
                intervention=recovery_action.get("strategy"),
                status="blocked",
                reason=(
                    "Recovery execution stopped because "
                    "maximum recovery attempts were reached"
                ),
                metadata={
                    "recovery_action_id": recovery_action["id"],
                    "attempt_count": len(completed_attempts),
                    "max_attempts": 2,
                },
            )

            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "Maximum recovery attempts reached. "
                        "Payment requires human review."
                    ),
                    "attempt_count": len(completed_attempts),
                    "max_attempts": 2,
                },
            )

        # -------------------------------------------------
        # 9. Recompute current ML decision
        # -------------------------------------------------

        context = get_payment_context(
            payment_id=payment_id,
            intervention="retry_later",
        )

        print("RECOVERY CONTEXT CREATED")

        optimization = optimize_intervention(context)

        print(
            "CURRENT OPTIMIZATION:",
            optimization,
        )

        policy = evaluate_policy(
            payment_context=context,
            optimization=optimization,
        )

        print(
            "CURRENT POLICY:",
            policy,
        )

        recommended_intervention = (
            optimization.get("recommended_intervention")
        )

        policy_decision = (
            policy.get("decision")
            or policy.get("action")
            or policy.get("policy_decision")
        )

        print(
            "RECOMMENDED INTERVENTION:",
            recommended_intervention,
        )

        print(
            "POLICY DECISION:",
            policy_decision,
        )

        # -------------------------------------------------
        # 10. Ensure stored action agrees with AI decision
        # -------------------------------------------------

        stored_intervention = recovery_action.get("strategy")

        if stored_intervention != recommended_intervention:
            log_audit_event(
                event_type="recovery_execution_blocked",
                payment_id=payment_id,
                decision=policy_decision,
                intervention=recommended_intervention,
                status="blocked",
                reason=(
                    "Stored recovery recommendation no longer "
                    "matches the current ML optimizer decision"
                ),
                metadata={
                    "recovery_action_id": recovery_action["id"],
                    "stored_intervention": stored_intervention,
                    "current_intervention": (
                        recommended_intervention
                    ),
                    "policy": policy,
                },
            )

            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "Recovery recommendation is stale. "
                        "Run recovery analysis again before execution."
                    ),
                    "stored_intervention": stored_intervention,
                    "current_intervention": (
                        recommended_intervention
                    ),
                },
            )

        # -------------------------------------------------
        # 11. Governance gate
        # -------------------------------------------------

        if policy_decision not in {
            "AUTO_EXECUTE",
            "AUTO",
        }:
            log_audit_event(
                event_type="recovery_execution_blocked",
                payment_id=payment_id,
                decision=policy_decision,
                intervention=recommended_intervention,
                status="blocked",
                reason=(
                    "Recovery execution blocked by policy "
                    "guardrails"
                ),
                metadata={
                    "recovery_action_id": recovery_action["id"],
                    "policy": policy,
                    "amount": payment.get("amount"),
                    "currency": payment.get("currency"),
                },
            )

            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "Recovery action requires human review "
                        "and cannot be auto-executed."
                    ),
                    "policy_decision": policy_decision,
                    "policy_reasons": policy.get(
                        "reasons",
                        [],
                    ),
                },
            )

        # -------------------------------------------------
        # 12. Verify supported Razorpay executor
        # -------------------------------------------------

        if recommended_intervention != (
            "request_alternative_payment"
        ):
            log_audit_event(
                event_type="recovery_execution_blocked",
                payment_id=payment_id,
                decision=policy_decision,
                intervention=recommended_intervention,
                status="blocked",
                reason=(
                    "No Razorpay sandbox executor is registered "
                    "for the selected intervention"
                ),
                metadata={
                    "recovery_action_id": recovery_action["id"],
                    "supported_executor": (
                        "request_alternative_payment"
                    ),
                },
            )

            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "This intervention does not have a "
                        "Razorpay sandbox executor yet."
                    ),
                    "intervention": recommended_intervention,
                    "supported_executor": (
                        "request_alternative_payment"
                    ),
                },
            )

        # -------------------------------------------------
        # 13. Create Razorpay Test Mode Payment Link
        # -------------------------------------------------

        razorpay_result = create_recovery_payment_link(
            amount=float(payment["amount"]),
            customer_id=payment["customer_id"],
            payment_id=payment["id"],
            description=(
                f"AgentReady recovery payment for "
                f"{payment['customer_id']}"
            ),
        )

        print(
            "RAZORPAY PAYMENT LINK:",
            razorpay_result,
        )

        # -------------------------------------------------
        # 14. Persist provider execution
        # -------------------------------------------------

        update_response = (
            supabase
            .table("recovery_actions")
            .update({
                "provider": "razorpay",
                "provider_reference": razorpay_result.get(
                    "payment_link_id"
                ),
                "provider_url": razorpay_result.get(
                    "short_url"
                ),
                "provider_status": razorpay_result.get(
                    "status"
                ),
            })
            .eq("id", recovery_action["id"])
            .execute()
        )

        if not update_response.data:
            raise HTTPException(
                status_code=500,
                detail=(
                    "Razorpay Payment Link was created but "
                    "recovery action could not be updated."
                ),
            )

        saved_action = update_response.data[0]

        print(
            "UPDATED RECOVERY ACTION:",
            saved_action,
        )

        # -------------------------------------------------
        # 15. Create governed recovery attempt
        # -------------------------------------------------

        next_attempt_number = len(completed_attempts) + 1

        attempt = create_recovery_attempt(
            payment_id=payment_id,
            attempt_number=next_attempt_number,
            intervention=recommended_intervention,
            recovery_action_id=recovery_action["id"],
        )

        print(
            "RECOVERY ATTEMPT CREATED:",
            attempt,
        )

        # -------------------------------------------------
        # 16. Audit successful sandbox execution
        # -------------------------------------------------

        log_audit_event(
            event_type="razorpay_recovery_execution",
            payment_id=payment_id,
            decision=policy_decision,
            intervention=recommended_intervention,
            status=razorpay_result.get("status"),
            reason=(
                "Razorpay Test Mode recovery Payment Link "
                "created under AgentReady policy governance"
            ),
            metadata={
                "recovery_action_id": recovery_action["id"],
                "attempt_id": attempt.get("id"),
                "attempt_number": attempt.get(
                    "attempt_number"
                ),
                "provider": "razorpay",
                "provider_reference": razorpay_result.get(
                    "payment_link_id"
                ),
                "provider_status": razorpay_result.get(
                    "status"
                ),
                "amount": payment.get("amount"),
                "currency": payment.get("currency"),
                "customer_id": payment.get("customer_id"),
            },
        )

        print("=============================================")

        return {
            "success": True,
            "payment_id": payment_id,
            "recovery_action_id": recovery_action["id"],
            "decision": policy_decision,
            "intervention": recommended_intervention,
            "provider": "razorpay",
            "provider_reference": razorpay_result.get(
                "payment_link_id"
            ),
            "provider_url": razorpay_result.get(
                "short_url"
            ),
            "provider_status": razorpay_result.get(
                "status"
            ),
            "amount": razorpay_result.get("amount"),
            "currency": razorpay_result.get("currency"),
            "attempt": attempt,
            "already_executed": False,
            "message": (
                "Razorpay Test Mode recovery Payment Link "
                "created successfully."
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        print("========== RAZORPAY EXECUTION ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("===============================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =========================================================
# RECOVERY WORKFLOW
# =========================================================

@app.post("/payments/{payment_id}/recovery-workflow")
def start_recovery_workflow(payment_id: str):
    try:
        print("========== RECOVERY WORKFLOW ==========")
        print("PAYMENT ID:", repr(payment_id))

        payment_response = (
            supabase
            .table("payments")
            .select("*")
            .eq("id", payment_id)
            .limit(1)
            .execute()
        )

        payments = payment_response.data or []

        if not payments:
            raise HTTPException(
                status_code=404,
                detail="Payment not found",
            )

        payment = payments[0]

        print("PAYMENT FOUND:", payment)

        previous_attempts = get_recovery_attempts(payment_id)

        print("PREVIOUS ATTEMPTS:", previous_attempts)

        workflow = get_next_intervention(previous_attempts)

        print("WORKFLOW DECISION:", workflow)

        log_audit_event(
            event_type="recovery_workflow_decision",
            payment_id=payment_id,
            decision=workflow.get("decision"),
            intervention=workflow.get("next_intervention"),
            status="evaluated",
            reason=workflow.get("reason"),
            metadata={
                "attempt_number": workflow.get("attempt_number"),
                "previous_attempt_count": len(previous_attempts),
                "failure_reason": payment.get("failure_reason"),
                "amount": payment.get("amount"),
                "currency": payment.get("currency"),
            },
        )

        if workflow["decision"] != "CONTINUE":
            existing_attempt = None

            if workflow["decision"] == "PENDING":
                pending_attempts = [
                    attempt
                    for attempt in previous_attempts
                    if attempt.get("status") == "pending"
                ]

                if pending_attempts:
                    existing_attempt = pending_attempts[-1]

            print("WORKFLOW STOPPED")
            print("EXISTING ATTEMPT:", existing_attempt)
            print("======================================")

            return {
                "success": True,
                "payment_id": payment_id,
                "workflow": workflow,
                "attempt": existing_attempt,
            }

        attempt = create_recovery_attempt(
            payment_id=payment_id,
            attempt_number=workflow["attempt_number"],
            intervention=workflow["next_intervention"],
        )

        print("CREATED ATTEMPT:", attempt)

        log_audit_event(
            event_type="recovery_attempt_created",
            payment_id=payment_id,
            decision=workflow.get("decision"),
            intervention=workflow.get("next_intervention"),
            status=attempt.get("status"),
            reason=workflow.get("reason"),
            metadata={
                "attempt_id": attempt.get("id"),
                "attempt_number": attempt.get("attempt_number"),
                "failure_reason": payment.get("failure_reason"),
                "amount": payment.get("amount"),
                "currency": payment.get("currency"),
            },
        )

        print("======================================")

        return {
            "success": True,
            "payment_id": payment_id,
            "workflow": workflow,
            "attempt": attempt,
        }

    except HTTPException:
        raise

    except Exception as exc:
        print("========== RECOVERY WORKFLOW ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("==============================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =========================================================
# COMPLETE RECOVERY ATTEMPT
# =========================================================

@app.patch("/recovery-attempts/{attempt_id}")
def complete_recovery_attempt(
    attempt_id: str,
    request: RecoveryAttemptUpdate,
):
    try:
        print("========== COMPLETE RECOVERY ATTEMPT ==========")
        print("ATTEMPT ID:", repr(attempt_id))
        print("STATUS:", request.status)

        updated_attempt = update_recovery_attempt(
            attempt_id=attempt_id,
            status=request.status,
            failure_reason=request.failure_reason,
        )

        print("UPDATED ATTEMPT:", updated_attempt)

        outcome_payment_id = updated_attempt.get("payment_id")
        outcome_intervention = updated_attempt.get("intervention")

        if request.status == "success":
            outcome_reason = (
                request.failure_reason
                or "Recovery attempt marked successful"
            )
        else:
            outcome_reason = (
                request.failure_reason
                or "Recovery attempt marked failed"
            )

        log_audit_event(
            event_type="recovery_attempt_completed",
            payment_id=outcome_payment_id,
            intervention=outcome_intervention,
            status=request.status,
            reason=outcome_reason,
            metadata={
                "attempt_id": attempt_id,
                "attempt_number": updated_attempt.get(
                    "attempt_number"
                ),
                "failure_reason": request.failure_reason,
                "completed_at": updated_attempt.get(
                    "completed_at"
                ),
            },
        )

        print("===============================================")

        return {
            "success": True,
            "attempt": updated_attempt,
            "message": "Recovery attempt completed successfully",
        }

    except ValueError as exc:
        print("INVALID ATTEMPT STATUS:", repr(exc))

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print("========== COMPLETE ATTEMPT ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("============================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =========================================================
# RECOVERY ATTEMPT HISTORY
# =========================================================

@app.get("/payments/{payment_id}/recovery-attempts")
def get_payment_recovery_attempts(payment_id: str):
    try:
        print("========== RECOVERY ATTEMPT HISTORY ==========")
        print("PAYMENT ID:", repr(payment_id))

        attempts = get_recovery_attempts(payment_id)

        print("ATTEMPT COUNT:", len(attempts))
        print("===============================================")

        return {
            "success": True,
            "payment_id": payment_id,
            "attempt_count": len(attempts),
            "attempts": attempts,
        }

    except Exception as exc:
        print(
            "========== RECOVERY ATTEMPT HISTORY ERROR =========="
        )
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("=====================================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =========================================================
# BATCH RECOVERY INTELLIGENCE
# =========================================================

@app.post("/recovery/batch")
def run_batch_recovery():
    """
    Analyze the complete failed-payment portfolio.

    The batch agent:
    - scans failed payments
    - predicts recovery probability
    - evaluates candidate interventions
    - calculates expected recovery value
    - applies financial guardrails
    - separates automatic recovery from human review
    """

    try:
        print("========== BATCH RECOVERY ==========")

        result = analyze_batch_recovery()

        print("PAYMENT COUNT:", result["payment_count"])
        print(
            "REVENUE AT RISK:",
            result["total_revenue_at_risk"],
        )
        print(
            "EXPECTED RECOVERY:",
            result["total_expected_recovery"],
        )
        print(
            "RECOVERY OPPORTUNITY:",
            result["recovery_opportunity_percent"],
        )
        print(
            "AUTO RECOVERY COUNT:",
            result["auto_recovery_count"],
        )
        print(
            "HUMAN REVIEW COUNT:",
            result["human_review_count"],
        )

        log_audit_event(
            event_type="batch_recovery_analysis",
            actor="AgentReady",
            status="completed",
            reason=(
                "Portfolio-wide recovery opportunity "
                "analysis completed"
            ),
            metadata={
                "payment_count": result.get("payment_count"),
                "total_revenue_at_risk": result.get(
                    "total_revenue_at_risk"
                ),
                "total_expected_recovery": result.get(
                    "total_expected_recovery"
                ),
                "recovery_opportunity_percent": result.get(
                    "recovery_opportunity_percent"
                ),
                "auto_recovery_count": result.get(
                    "auto_recovery_count"
                ),
                "human_review_count": result.get(
                    "human_review_count"
                ),
            },
        )

        print("====================================")

        return {
            "success": True,
            "data": result,
        }

    except Exception as exc:
        print("========== BATCH RECOVERY ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("==========================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =========================================================
# CONVERSATIONAL RECOVERY AGENT
# =========================================================

@app.post("/agent/query")
def query_recovery_agent(request: AgentQueryRequest):
    """
    Answer a merchant recovery question using AgentReady's
    live recovery intelligence pipeline.

    The agent is grounded in:
    - Supabase payment/customer data
    - trained recovery probability model
    - intervention optimizer
    - policy guardrails
    - recovery workflow logic
    """

    try:
        print("========== RECOVERY AGENT QUERY ==========")
        print("QUESTION:", request.question)

        result = answer_recovery_question(request.question)

        print("INTENT:", result.get("intent"))
        print("==========================================")

        return {
            "success": True,
            "question": request.question,
            "result": result,
        }

    except ValueError as exc:
        print("RECOVERY AGENT VALIDATION ERROR:", repr(exc))

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print("========== RECOVERY AGENT ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("==========================================")

        raise HTTPException(
            status_code=500,
            detail="Unable to process recovery agent query",
        ) from exc


# =========================================================
# ML EVALUATION EVIDENCE
# =========================================================

@app.get("/ml/evaluation")
def get_ml_evaluation():
    """
    Return evidence behind AgentReady's ML recovery decisions.

    Data is loaded from evaluation artifacts generated
    during model development rather than hardcoded into
    the frontend.
    """

    try:
        print("========== ML EVALUATION ==========")

        result = get_model_evaluation()

        print(
            "MODEL:",
            result["model"]["name"],
        )

        print(
            "TEST ROC-AUC:",
            result["final_test"]["roc_auc"],
        )

        print(
            "TEST PR-AUC:",
            result["final_test"]["pr_auc"],
        )

        print(
            "TEST RECALL:",
            result["final_test"]["recall"],
        )

        print("===================================")

        return result

    except FileNotFoundError as exc:
        print("ML EVALUATION FILE ERROR:", repr(exc))

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        print("========== ML EVALUATION ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("=========================================")

        raise HTTPException(
            status_code=500,
            detail="Unable to load ML evaluation evidence",
        ) from exc


# =========================================================
# RECOVERY ACTION HISTORY
# =========================================================

@app.get("/recovery-actions")
def get_recovery_actions():
    try:
        response = (
            supabase
            .table("recovery_actions")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        return {
            "success": True,
            "recovery_actions": response.data,
        }

    except Exception as exc:
        print("========== RECOVERY HISTORY ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("=============================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# =========================================================
# AUDIT TRAIL
# =========================================================

@app.get("/audit-events")
def get_all_audit_events():
    """
    Return the complete AgentReady audit trail.
    """

    try:
        print("========== AUDIT TRAIL ==========")

        events = get_audit_events()

        print("AUDIT EVENT COUNT:", len(events))
        print("=================================")

        return {
            "success": True,
            "event_count": len(events),
            "events": events,
        }

    except Exception as exc:
        print("========== AUDIT TRAIL ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("========================================")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve audit trail",
        ) from exc


# =========================================================
# PAYMENT-SPECIFIC AUDIT TRAIL
# =========================================================

@app.get("/payments/{payment_id}/audit-events")
def get_payment_audit_events(payment_id: str):
    """
    Return the complete decision and recovery history
    for one payment.
    """

    try:
        print("========== PAYMENT AUDIT TRAIL ==========")
        print("PAYMENT ID:", repr(payment_id))

        events = get_audit_events(payment_id=payment_id)

        print("AUDIT EVENT COUNT:", len(events))
        print("==========================================")

        return {
            "success": True,
            "payment_id": payment_id,
            "event_count": len(events),
            "events": events,
        }

    except Exception as exc:
        print("========== PAYMENT AUDIT ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("=========================================")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve payment audit trail",
        ) from exc