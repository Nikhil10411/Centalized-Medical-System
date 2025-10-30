from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Plan, Subscription, User
from schemas import (
    PlanCreate, PlanOut,
    SubscriptionCreate, SubscriptionUpdate, SubscriptionOut
)
from utils.token_utils import get_current_user  # ✅ Import your JWT auth util
import uuid
from datetime import datetime

router = APIRouter(prefix="/subscription", tags=["Subscription"])


# --------------------------
# ✅ Helper Function
# --------------------------
def admin_only(current_user: User):
    """Ensure the current user is admin only"""
    if current_user.role not in ["admin"] and current_user.id != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )


# ------------------------------------------
# 1️⃣  Create a new plan (Admin Only)
# ------------------------------------------
@router.post("/create_plan", response_model=PlanOut)
def create_plan(
    plan: PlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    admin_only(current_user)  # ✅ Restrict access to admins only

    existing_plan = db.query(Plan).filter(Plan.name == plan.name).first()
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan with this name already exists."
        )

    new_plan = Plan(
        id=uuid.uuid4(),
        name=plan.name,
        description=plan.description,
        amount=plan.amount,
        interval=plan.interval,
        is_active=plan.is_active
    )

    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    return new_plan


# ------------------------------------------
# 2️⃣  Get all active plans (Admin Only)
# ------------------------------------------
@router.get("/plans", response_model=list[PlanOut])
def get_all_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    admin_only(current_user)
    plans = db.query(Plan).filter(Plan.is_active == True).all()
    return plans


# ------------------------------------------
# 3️⃣  Create Subscription (Admin Only)
# ------------------------------------------
@router.post("/create", response_model=SubscriptionOut)
def create_subscription(
    subscription: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    admin_only(current_user)

    user = db.query(User).filter(User.id == subscription.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = db.query(Plan).filter(Plan.id == subscription.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Prevent duplicate active subscriptions
    active_sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == subscription.user_id)
        .filter(Subscription.status == "active")
        .first()
    )
    if active_sub:
        raise HTTPException(status_code=400, detail="User already has an active subscription")

    new_sub = Subscription(
        id=uuid.uuid4(),
        user_id=subscription.user_id,
        plan_id=subscription.plan_id,
        razorpay_subscription_id=subscription.razorpay_subscription_id,
        razorpay_plan_id=subscription.razorpay_plan_id,
        status=subscription.status,
        start_date=subscription.start_date or datetime.utcnow(),
        next_billing_date=subscription.next_billing_date,
    )

    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub


# ------------------------------------------
# 4️⃣  Get User’s All Subscriptions (Admin Only)
# ------------------------------------------
@router.get("/user/{user_id}", response_model=list[SubscriptionOut])
def get_user_subscriptions(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    admin_only(current_user)
    subs = db.query(Subscription).filter(Subscription.user_id == user_id).all()
    if not subs:
        raise HTTPException(status_code=404, detail="No subscriptions found")
    return subs


# ------------------------------------------
# 5️⃣  Update Subscription (Admin Only)
# ------------------------------------------
@router.put("/update/{subscription_id}", response_model=SubscriptionOut)
def update_subscription(
    subscription_id: uuid.UUID,
    update_data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    admin_only(current_user)

    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if update_data.status:
        subscription.status = update_data.status

    if update_data.cancelled_at:
        subscription.cancelled_at = update_data.cancelled_at
        subscription.status = "cancelled"

    if update_data.end_date:
        subscription.end_date = update_data.end_date

    db.commit()
    db.refresh(subscription)
    return subscription


# ------------------------------------------
# 6️⃣  Delete Subscription (Admin Only)
# ------------------------------------------
@router.delete("/delete/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    subscription_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    admin_only(current_user)

    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    db.delete(subscription)
    db.commit()
    return None
