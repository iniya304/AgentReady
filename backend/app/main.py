from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.supabase_client import supabase
from app.recovery_engine import analyze_payment


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

        # 4. Save recovery action
        recovery_data = {
            "payment_id": payment["id"],
            "strategy": analysis["strategy"],
            "priority": analysis["priority"],
            "priority_score": analysis["priority_score"],
            "status": "recommended",
        }

        print("RECOVERY DATA:", recovery_data)

        recovery_response = (
            supabase
            .table("recovery_actions")
            .insert(recovery_data)
            .execute()
        )

        print(
            "RECOVERY ACTION RESPONSE:",
            recovery_response.data
        )

        if not recovery_response.data:
            raise HTTPException(
                status_code=500,
                detail="Recovery action was not saved",
            )

        saved_action = recovery_response.data[0]

        print("SAVED ACTION:", saved_action)
        print("====================================")

        # 5. Return result
        return {
            "success": True,
            "payment_id": payment["id"],
            "action": analysis["strategy"],
            "priority": analysis["priority"],
            "priority_score": analysis["priority_score"],
            "recovery_action_id": saved_action["id"],
            "status": saved_action["status"],
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