from razorpay_client import razorpay_client


response = razorpay_client.payment_link.all()

print("Razorpay connection successful!")
print("Payment links retrieved:", len(response.get("payment_links", [])))