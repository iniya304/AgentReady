from app.supabase_client import supabase


payments = [
    {
        "customer_id": "cust_001",
        "amount": 2499.00,
        "currency": "INR",
        "payment_status": "failed",
        "failure_reason": "insufficient_funds",
    },
    {
        "customer_id": "cust_002",
        "amount": 8999.00,
        "currency": "INR",
        "payment_status": "failed",
        "failure_reason": "card_declined",
    },
    {
        "customer_id": "cust_003",
        "amount": 1499.00,
        "currency": "INR",
        "payment_status": "failed",
        "failure_reason": "network_error",
    },
    {
        "customer_id": "cust_004",
        "amount": 12999.00,
        "currency": "INR",
        "payment_status": "failed",
        "failure_reason": "insufficient_funds",
    },
    {
        "customer_id": "cust_005",
        "amount": 599.00,
        "currency": "INR",
        "payment_status": "failed",
        "failure_reason": "expired_card",
    },
]


response = supabase.table("payments").insert(payments).execute()

print("Inserted payments:")
print(response.data)

