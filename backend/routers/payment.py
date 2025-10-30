from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from database import get_db
from utils.token_utils import get_current_user
from models import Plan, Subscription, Payment
from schemas import (
    CreateOrderRequest,
    RazorpayOrderResponse,
    VerifyPaymentRequest,
    PaymentSuccessResponse,
    SubscriptionStatus,
)
import razorpay
import os
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta
  # your Enum file (active, cancelled, etc.)

load_dotenv()

router = APIRouter(prefix="/payment", tags=["Payment"])

# ----------------------------
# Initialize Razorpay client
# ----------------------------
razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)

# ================================================================
# ✅ 1. Create Razorpay Order (for one-time payments)
# ================================================================
@router.post("/create-order", response_model=RazorpayOrderResponse)
async def create_order(
    data: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        order = razorpay_client.order.create(
            {
                "amount": int(data.amount * 100),
                "currency": data.currency,
                "receipt": str(uuid.uuid4()),
                "notes": {"user_id": str(current_user.id)},
            }
        )

        new_payment = Payment(
            id=uuid.uuid4(),
            razorpay_order_id=order["id"],
            amount=data.amount,
            currency=data.currency,
            user_id=current_user.id,
            payment_status="created",
            description=data.description or "",
        )
        db.add(new_payment)
        db.commit()

        return RazorpayOrderResponse(
            id=order["id"],
            amount=order["amount"] / 100,
            currency=order["currency"],
            status=order["status"],
            key=os.getenv("RAZORPAY_KEY_ID"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")


# ================================================================
# ✅ 2. Verify Razorpay Payment (Frontend callback verification)
# ================================================================
@router.post("/verify-payment", response_model=PaymentSuccessResponse)
async def verify_payment(
    data: VerifyPaymentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        razorpay_client.utility.verify_payment_signature(
            {
                "razorpay_order_id": data.razorpay_order_id,
                "razorpay_payment_id": data.razorpay_payment_id,
                "razorpay_signature": data.razorpay_signature,
            }
        )

        payment = (
            db.query(Payment)
            .filter(Payment.razorpay_order_id == data.razorpay_order_id)
            .first()
        )

        if not payment:
            raise HTTPException(status_code=404, detail="Payment record not found")

        payment.razorpay_payment_id = data.razorpay_payment_id
        payment.razorpay_signature = data.razorpay_signature
        payment.payment_status = "success"
        payment.updated_at = datetime.utcnow()
        db.commit()

        return PaymentSuccessResponse(success=True, message="Payment verified successfully")
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


# ================================================================
# ✅ 3. Get or Create Plan
# ================================================================
def get_or_create_plan(db: Session, name="Niksain Premium Plan"):
    plan = db.query(Plan).filter(Plan.name == name).first()
    if plan:
        return plan

    razorpay_plan = razorpay_client.plan.create(
        {
            "period": "monthly",
            "interval": 1,
            "item": {
                "name": name,
                "amount": 49900,  # ₹499 in paise
                "currency": "INR",
                "description": "Premium monthly subscription plan",
            },
        }
    )

    new_plan = Plan(
        id=uuid.uuid4(),
        name=name,
        description="Premium monthly access for doctors, stores, and suppliers",
        amount=499.00,
        interval="month",
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan


# ================================================================
# ✅ 4. Create Subscription
# ================================================================
@router.post("/create-subscription", response_model=PaymentSuccessResponse)
async def create_subscription(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        plan = get_or_create_plan(db)

        razorpay_subscription = razorpay_client.subscription.create(
            {
                "plan_id": plan.id,
                "total_count": 12,
                "customer_notify": 1,
                "notes": {
                    "user_id": str(current_user.id),
                    "role": current_user.role,
                },
            }
        )

        new_subscription = Subscription(
            id=uuid.uuid4(),
            user_id=current_user.id,
            plan_id=plan.id,
            razorpay_subscription_id=razorpay_subscription["id"],
            razorpay_plan_id=plan.id,
            status=SubscriptionStatus.created,
            start_date=datetime.utcnow(),
            next_billing_date=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow(),
        )

        db.add(new_subscription)
        db.commit()

        return PaymentSuccessResponse(
            success=True,
            message=f"Subscription created successfully! ID: {razorpay_subscription['id']}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating subscription: {str(e)}")


# ================================================================
# ✅ 5. Cancel Subscription
# ================================================================
@router.post("/cancel-subscription/{subscription_id}", response_model=PaymentSuccessResponse)
async def cancel_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        subscription = (
            db.query(Subscription)
            .filter(Subscription.razorpay_subscription_id == subscription_id)
            .first()
        )
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        razorpay_client.subscription.cancel(subscription_id)
        subscription.status = SubscriptionStatus.cancelled
        subscription.cancelled_at = datetime.utcnow()
        db.commit()

        return PaymentSuccessResponse(
            success=True, message=f"Subscription {subscription_id} cancelled successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling subscription: {str(e)}")


# ================================================================
# ✅ 6. Refund Payment
# ================================================================
@router.post("/refund", response_model=PaymentSuccessResponse)
async def refund_payment(
    razorpay_payment_id: str,
    current_user=Depends(get_current_user),
):
    try:
        refund = razorpay_client.payment.refund(razorpay_payment_id)
        return PaymentSuccessResponse(
            success=True,
            message=f"Refund initiated successfully. Refund ID: {refund['id']}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refund failed: {str(e)}")


# ================================================================
# ✅ 7. Razorpay Webhook Endpoint (Automatic Verification)
# ================================================================
@router.post("/webhook")
async def razorpay_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.body()
        signature = request.headers.get("X-Razorpay-Signature")

        secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        generated_signature = hmac.new(
            bytes(secret, "utf-8"), body, hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(generated_signature, signature):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

        payload = await request.json()
        event = payload.get("event")
        entity = payload.get("payload", {})

        if event == "subscription.activated":
            sub_id = entity["subscription"]["entity"]["id"]
            subscription = (
                db.query(Subscription)
                .filter(Subscription.razorpay_subscription_id == sub_id)
                .first()
            )
            if subscription:
                subscription.status = SubscriptionStatus.active
                subscription.start_date = datetime.utcnow()
                db.commit()

        elif event == "subscription.charged":
            sub_id = entity["subscription"]["entity"]["id"]
            subscription = (
                db.query(Subscription)
                .filter(Subscription.razorpay_subscription_id == sub_id)
                .first()
            )
            if subscription:
                subscription.next_billing_date = datetime.utcnow() + timedelta(days=30)
                db.commit()

        elif event == "subscription.cancelled":
            sub_id = entity["subscription"]["entity"]["id"]
            subscription = (
                db.query(Subscription)
                .filter(Subscription.razorpay_subscription_id == sub_id)
                .first()
            )
            if subscription:
                subscription.status = SubscriptionStatus.cancelled
                subscription.cancelled_at = datetime.utcnow()
                db.commit()

        return {"status": "success", "event": event}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")
