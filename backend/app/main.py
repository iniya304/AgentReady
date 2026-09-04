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


app = FastAPI(title="AgentReady")


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Models
# ---------------------------------------------------------

class PaymentCreate(BaseModel):
    customer_id: str = Field(min_length=1)
    amount: float = Field(gt=0)
    currency: str = "INR"
    payment_status: str = "failed"
    failure_reason: str | None = None
    payment_method: str = "card"


class PredictionRequest(BaseModel):
    intervention: str = "retry_later"


class RecoveryAttemptUpdate(BaseModel):
    status: str
    failure_reason: str | None = None


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "AgentReady",
        "message": "AgentReady backend is running",
        "running": True,
    }


# ---------------------------------------------------------
# Get Payments
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Create Payment
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Analyze Payment
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# ML Recovery Prediction
# ---------------------------------------------------------

@app.post("/payments/{payment_id}/predict")
def predict_payment_recovery(
    payment_id: str,
    request: PredictionRequest,
):
    try:
        print("========== ML RECOVERY PREDICTION ==========")
        print("PAYMENT ID:", repr(payment_id))
        print("INTERVENTION:", request.intervention)

        # 1. Fetch payment + customer profile
        context = get_payment_context(
            payment_id=payment_id,
            intervention=request.intervention,
        )

        print("ML CONTEXT CREATED")
        print("CUSTOMER:", context.get("customer_id"))
        print("AMOUNT:", context.get("amount"))
        print("FAILURE:", context.get("failure_reason"))

        # 2. Run trained ML model
        prediction = predict_recovery(context)

        print("ML PREDICTION:", prediction)
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


# ---------------------------------------------------------
# Intervention Optimizer + Policy Engine
# ---------------------------------------------------------

@app.post("/payments/{payment_id}/optimize")
def optimize_payment_recovery(payment_id: str):
    try:
        print("========== OPTIMIZE RECOVERY ==========")
        print("PAYMENT ID:", repr(payment_id))

        # 1. Fetch payment + customer recovery profile
        #    and construct ML context.
        context = get_payment_context(
            payment_id=payment_id,
            intervention="retry_later",
        )

        print("PAYMENT CONTEXT CREATED")
        print("CUSTOMER:", context.get("customer_id"))
        print("AMOUNT:", context.get("amount"))
        print("FAILURE:", context.get("failure_reason"))

        # 2. Evaluate all supported interventions.
        optimization = optimize_intervention(context)

        print("OPTIMIZATION RESULT:", optimization)

        # 3. Apply safety/business guardrails.
        policy = evaluate_policy(
            payment_context=context,
            optimization=optimization,
        )

        print("POLICY RESULT:", policy)
        print("======================================")

        # 4. Return optimizer + policy decision.
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


# ---------------------------------------------------------
# Recover Payment
# ---------------------------------------------------------

@app.post("/payments/{payment_id}/recover")
def recover_payment(payment_id: str):
    try:
        print("========== RECOVER PAYMENT ==========")
        print("REQUEST ID:", repr(payment_id))

        # 1. Fetch payments
        response = (
            supabase
            .table("payments")
            .select("*")
            .execute()
        )

        payments = response.data

        print("PAYMENTS FOUND:", len(payments))

        # 2. Find requested payment
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

        # 3. Analyze payment
        analysis = analyze_payment(payment)

        print("ANALYSIS:", analysis)

        # -------------------------------------------------
        # 4. Idempotency / Duplicate Prevention
        # -------------------------------------------------
        #
        # Before creating a new recovery recommendation,
        # check whether an active "recommended" action
        # already exists for this payment.
        #
        # This prevents repeated Recover clicks from
        # creating duplicate recovery_actions rows.
        # -------------------------------------------------

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

        # -------------------------------------------------
        # 5. Create new recovery action
        # -------------------------------------------------

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
        print("====================================")

        # 6. Return newly created result
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


# ---------------------------------------------------------
# Recovery Workflow
# ---------------------------------------------------------

@app.post("/payments/{payment_id}/recovery-workflow")
def start_recovery_workflow(payment_id: str):
    try:
        print("========== RECOVERY WORKFLOW ==========")
        print("PAYMENT ID:", repr(payment_id))

        # 1. Fetch previous recovery attempts
        previous_attempts = get_recovery_attempts(payment_id)

        print("PREVIOUS ATTEMPTS:", previous_attempts)

        # 2. Apply stopping rules
        workflow = get_next_intervention(previous_attempts)

        print("WORKFLOW DECISION:", workflow)

        # 3. If workflow is not continuing,
        #    do not create a duplicate attempt.
        if workflow["decision"] != "CONTINUE":

            existing_attempt = None

            # If an attempt is already pending,
            # return that existing attempt.
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

        # 4. Create next recovery attempt
        attempt = create_recovery_attempt(
            payment_id=payment_id,
            attempt_number=workflow["attempt_number"],
            intervention=workflow["next_intervention"],
        )

        print("CREATED ATTEMPT:", attempt)
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


# ---------------------------------------------------------
# Complete Recovery Attempt
# ---------------------------------------------------------

@app.patch("/recovery-attempts/{attempt_id}")
def complete_recovery_attempt(
    attempt_id: str,
    request: RecoveryAttemptUpdate,
):
    try:
        print("========== COMPLETE RECOVERY ATTEMPT ==========")
        print("ATTEMPT ID:", repr(attempt_id))
        print("STATUS:", request.status)

        # Update the attempt in Supabase
        updated_attempt = update_recovery_attempt(
            attempt_id=attempt_id,
            status=request.status,
            failure_reason=request.failure_reason,
        )

        print("UPDATED ATTEMPT:", updated_attempt)
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


# ---------------------------------------------------------
# Recovery Attempt History
# ---------------------------------------------------------

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
        print("========== RECOVERY ATTEMPT HISTORY ERROR ==========")
        print("ERROR TYPE:", type(exc).__name__)
        print("ERROR:", repr(exc))
        print("=====================================================")

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------
# Batch Recovery Intelligence
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Recovery Action History
# ---------------------------------------------------------

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

        