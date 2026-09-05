from razorpay_recovery_service import create_recovery_payment_link


result = create_recovery_payment_link(
    amount=599,
    customer_id="cust_test_agentready",
    description="AgentReady recovery test payment",
)

print("Razorpay Payment Link created!")
print("Payment Link ID:", result["payment_link_id"])
print("Short URL:", result["short_url"])
print("Status:", result["status"])
print("Amount:", result["amount"])
print("Currency:", result["currency"])