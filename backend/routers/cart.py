from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from fastapi.responses import Response
import os
from typing import List
from database import get_db
from models import *
from schemas import *
from utils.token_utils import get_current_user
import uuid

router = APIRouter()

# -------------------------------------------------------
# Get All Inventory Products (All Stores + Supplier for Chemists)
# -------------------------------------------------------
@router.get("/inventory/all_stores")
def get_all_inventory_and_supplier_products(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    ✅ Returns:
       - All medical store inventory products for PATIENT, CUSTOMER, DOCTOR, ADMIN.
       - Additionally returns supplier products when a CHEMIST is logged in.
    """

    # 1️⃣ Define authorized roles
    AUTHORIZED_ROLES = [
        RoleEnum.PATIENT,
        RoleEnum.CUSTOMER,
        RoleEnum.DOCTOR,
        RoleEnum.ADMIN,
        RoleEnum.CHEMIST
    ]

    if current_user.role not in AUTHORIZED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view all store inventories."
        )

    # 2️⃣ Fetch all medical store inventory products
    inventory_products = (
        db.query(
            Inventory,
            Product.name.label("product_name_full"),
            Product.product_id,
            Product.image_mime.label("product_image_data"),
            Product.brand,
            Product.generic_name,
            Product.dosage,
            Product.form,
            Product.category,
            MedicalStore.store_name,
            MedicalStore.address.label("store_address"),
            MedicalStore.open_hours.label("store_open_hour"),
            MedicalStore.phone.label("store_phone_no"),
            MedicalStore.email.label("store_email"),
            MedicalStore.delivery_radius_km.label("store_delivery_radius")
        )
        .join(Product, Inventory.product_id == Product.product_id)
        .join(MedicalStore, Inventory.store_id == MedicalStore.store_id)
        .all()
    )

    inventory_data = [
        {
            "type": "inventory_product",
            "inventory_id": item.Inventory.inventory_id,
            "product_id": item.product_id,
            "product_name": item.product_name_full,
            "product_image_url": f"/product/image/{item.product_id}" if item.product_image_data else None,
            "brand": item.brand,
            "generic_name": item.generic_name,
            "dosage": item.dosage,
            "form": item.form,
            "category": item.category,
            "store_id": item.Inventory.store_id,
            "store_name": item.store_name,
            "store_address": item.store_address,
            "store_open_hour": item.store_open_hour,
            "store_phone_no": item.store_phone_no,
            "store_email": item.store_email,
            "delivery_radius": item.store_delivery_radius,
            "batch_no": item.Inventory.batch_no,
            "expiry_date": item.Inventory.expiry_date.isoformat() if item.Inventory.expiry_date else None,
            "quantity": item.Inventory.quantity,
            "price": float(item.Inventory.price),
        }
        for item in inventory_products
    ]

    # 3️⃣ If user is a CHEMIST → fetch supplier products too
    supplier_data = []
    if current_user.role == RoleEnum.CHEMIST:
        supplier_products = (
            db.query(
                SupplierProduct,
                Supplier.supplier_name,
                Supplier.supplier_id,
                Supplier.contact_name,
                Supplier.phone,
                Supplier.email,
                Supplier.pin_code,
                Supplier.city,
                Supplier.address,
                Supplier.age,
                Supplier.gender,
                Product.name.label("product_name_full"),
                Product.product_id,
                Product.image_mime.label("product_image_data"),
                Product.brand,
                Product.generic_name,
                Product.dosage,
                Product.form,
                Product.category,
            )
            .join(Supplier, SupplierProduct.supplier_id == Supplier.supplier_id)
            .join(Product, SupplierProduct.product_id == Product.product_id)
            .all()
        )

        supplier_data = [
            {
                "type": "supplier_product",
                "supplier_product_id": item.SupplierProduct.supplier_product_id,
                "supplier_id": item.supplier_id,
                "supplier_name": item.supplier_name,
                "contact_name":item.contact_name,
                "phone":item.phone,
                "email":item.email,
                "city":item.city,
                "pin_code":item.pin_code,
                "address":item.address,
                "age":item.age,
                "gender":item.gender,
                "product_id": item.product_id,
                "product_name": item.product_name_full,
                "product_image_url": f"/product/image/{item.product_id}" if item.product_image_data else None,
                "brand": item.brand,
                "generic_name": item.generic_name,
                "dosage": item.dosage,
                "form": item.form,
                "category": item.category,
                "price": float(item.SupplierProduct.price or 0),
                "lead_time_days": item.SupplierProduct.lead_time_days,
            }
            for item in supplier_products
        ]

    # 4️⃣ Combine data
    all_data = inventory_data + supplier_data

    # 5️⃣ Return combined response
    if not all_data:
        return {"message": "No products available."}
    return all_data

# -------------------------
# Get all inventory products (for doctors/patients/customers)
# -------------------------
@router.get("/store/{store_id}/products")
def get_store_products(store_id: str, db: Session = Depends(get_db)):
    products = (
        db.query(Inventory)
        .filter(Inventory.store_id == store_id)
        .join(Product)
        .all()
    )
    return [
        {
            "inventory_id": p.inventory_id,
            "product_name": p.product_name,
            "price": float(p.price),
            "quantity": p.quantity,
            "image": f"/product/image/{p.product.product_id}" if p.product.image else None,
        }
        for p in products
    ]


# -------------------------
# Add product to cart
# -------------------------
@router.post("/add/cart/{product_id}")
def add_to_cart(
    product_id: str,
    store_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Find or create cart
    cart = db.query(Cart).filter(
        Cart.user_id == str(current_user.id), Cart.store_id == store_id
    ).first()
    if not cart:
        cart = Cart(user_id=str(current_user.id), store_id=store_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    # Get product price from inventory
    inventory = db.query(Inventory).filter(
        Inventory.store_id == store_id,
        Inventory.product_id == product_id
    ).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Product not available in this store")

    # Add item or update quantity
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.cart_id, CartItem.product_id == product_id
    ).first()

    if existing_item:
        existing_item.quantity += 1
    else:
        item = CartItem(
            cart_id=cart.cart_id,
            product_id=product_id,
            price=inventory.price,
            quantity=1
        )
        db.add(item)

    db.commit()
    return {"message": "Product added to cart successfully"}


# -------------------------
# View Cart + Subtotal
# -------------------------
@router.get("/cart/view")
def view_cart(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    carts = db.query(Cart).filter(Cart.user_id == str(current_user.id)).all()
    all_carts = []
    for cart in carts:
        items = db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
        subtotal = sum(float(item.price) * item.quantity for item in items)
        all_carts.append({
            "store_id": cart.store_id,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "subtotal": float(item.price) * item.quantity
                } for item in items
            ],
            "total": subtotal
        })
    return all_carts


# -------------------------
# Remove item from cart
# -------------------------
@router.delete("/cart/remove/{product_id}")
def remove_from_cart(
    product_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    cart_items = (
        db.query(CartItem)
        .join(Cart)
        .filter(Cart.user_id == str(current_user.id), CartItem.product_id == product_id)
        .all()
    )
    if not cart_items:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    for item in cart_items:
        db.delete(item)
    db.commit()
    return {"message": "Item removed successfully"}


# -------------------------
# Checkout item from cart
# -------------------------
from datetime import date
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
# Assuming you have an APIRouter named 'router' and the dependencies:
# from your_file import router, get_db, get_current_user, User, Customer, Cart, CartItem, Bill, BillItem, RoleEnum
# and User, Customer, Bill, BillItem, Patient, RoleEnum are all correctly imported/available

# -------------------------
# Checkout item from cart (Updated for Mutually Exclusive Bill Links)
# -------------------------
@router.post("/checkout/{store_id}")
def checkout(store_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user_id = str(current_user.id)
    user_role = current_user.role
    
    # Initialize bill recipients
    bill_customer_id = None
    bill_patient_id = None
    
    # 1. HANDLE PATIENT ROLE (PRIORITY FOR MEDICAL BILLING)
    if user_role == RoleEnum.PATIENT:
        # Check if Patient record exists. If your Patient.patient_id is always the User.id, 
        # this is the correct filter.
        patient_record = db.query(Patient).filter(Patient.patient_id == user_id).first()
        
        if patient_record:
            # If the user is a confirmed Patient, use patient_id and skip customer_id.
            bill_patient_id = patient_record.patient_id
            print(f"INFO: Billing as Patient ID: {bill_patient_id}")
        else:
            # FALLBACK: If user has PATIENT role but no Patient record, raise error or fall through to Customer logic.
            # Assuming every user with PATIENT role must have a Patient record.
            db.rollback()
            raise HTTPException(status_code=400, detail="User is a Patient but no matching Patient record found.")
    
    # 2. HANDLE ALL OTHER ROLES (DOCTOR, ADMIN, CHEMIST, etc.)
    if bill_patient_id is None:
        # If not a Patient (or Patient record not found), bill as a general Customer.
        
        # Ensure Customer record exists (Fix for FK_Bill_Customer error)
        customer_record = db.query(Customer).filter(Customer.customer_id == user_id).first()
        
        if not customer_record:
            new_customer = Customer(
                customer_id=user_id,
                name=current_user.username,
                email=current_user.email,
                store_id=store_id, 
                role=user_role.value 
            )
            db.add(new_customer)
            db.flush() # Ensure the Customer ID is available for the Bill insertion
            print(f"INFO: Auto-created Customer record for User ID: {user_id}")
        
        bill_customer_id = user_id
        print(f"INFO: Billing as Customer ID: {bill_customer_id}")


    # 3. CART RETRIEVAL AND VALIDATION (No change)
    cart = db.query(Cart).filter(
        Cart.user_id == user_id, Cart.store_id == store_id
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found for this user and store.")

    items = db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
    if not items:
        raise HTTPException(status_code=400, detail="Cart is empty.")

    # 4. CALCULATIONS (No change)
    subtotal = sum(float(i.price) * i.quantity for i in items)
    tax = round(subtotal * 0.05, 2)
    total = subtotal + tax

    # 5. BILL CREATION (Using the mutually exclusive IDs)
    bill = Bill(
        issuer_store_id=store_id,
        # Only one of these will be set, the other is None (NULL in DB)
        customer_id=bill_customer_id,   
        patient_id=bill_patient_id,      
        subtotal=subtotal,
        tax_amount=tax,
        total_amount=total,
    )
    db.add(bill)
    db.flush() 
    db.refresh(bill)

    # 6. BILL ITEM CREATION AND INVENTORY MANAGEMENT (Same Inventory logic as before)
    for i in items:
        inventory_item = db.query(Inventory).filter(
            Inventory.store_id == store_id, 
            Inventory.product_id == i.product_id,
            Inventory.quantity >= i.quantity
        ).first()

        if not inventory_item:
            db.rollback() 
            raise HTTPException(status_code=400, detail=f"Product {i.product_id} is out of stock or inventory data is missing.")

        bill_item = BillItem(
            bill_id=bill.bill_id,
            product_id=i.product_id,
            batch_no=inventory_item.batch_no or "N/A", 
            expiry_date=inventory_item.expiry_date or date.today(), 
            quantity=i.quantity,
            unit_price=float(i.price),
            line_total=float(i.price) * i.quantity
        )
        db.add(bill_item)
        
        # Decrement inventory
        inventory_item.quantity -= i.quantity
        
        # Delete cart item
        db.delete(i)
        
    db.commit() 

    return {"message": "Checkout successful", "bill_id": bill.bill_id, "total": total}

# -------------------------
# Cancel Order and Restore Inventory
# -------------------------
@router.post("/bill/cancel/{bill_id}", status_code=status.HTTP_200_OK)
def cancel_order(
    bill_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # 1. Find the Bill
    bill = db.query(Bill).filter(Bill.bill_id == bill_id).first()
    
    if not bill:
        raise HTTPException(status_code=404, detail=f"Bill with ID '{bill_id}' not found.")

    # 2. Authorization Check (Ensure only the customer who placed the order or an admin can cancel)
    # The current_user must match EITHER the customer_id OR the patient_id associated with the bill.
    current_user_id = str(current_user.id)
    
    is_authorized_customer = bill.customer_id == current_user_id
    is_authorized_patient = bill.patient_id == current_user_id
    is_admin_or_store_user = current_user.role in [RoleEnum.ADMIN,RoleEnum.CUSTOMER,RoleEnum.PATIENT,RoleEnum.DOCTOR] # Add roles as needed

    if not (is_authorized_customer or is_authorized_patient or is_admin_or_store_user):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this bill.")
    
    # Optional: Check if the bill is already processed/shipped and cannot be canceled
    # (You might need to add a 'status' column to the Bill model for this)
    # if bill.status in ["shipped", "delivered", "canceled"]:
    #     raise HTTPException(status_code=400, detail=f"Bill status is '{bill.status}' and cannot be canceled.")
    
    # 3. Retrieve Bill Items
    bill_items = db.query(BillItem).filter(BillItem.bill_id == bill_id).all()

    if not bill_items:
        # This should ideally not happen if a bill exists, but good for safety.
        raise HTTPException(status_code=404, detail="No items found for this bill.")

    # 4. Restore Inventory for each item
    store_id = bill.issuer_store_id
    restored_items_count = 0
    
    try:
        for item in bill_items:
            # Find the corresponding inventory item
            inventory = db.query(Inventory).filter(
                Inventory.store_id == store_id,
                Inventory.product_id == item.product_id
                # Note: We are ignoring batch_no/expiry_date here for simplicity, 
                # as inventory is typically tracked at the product level. 
                # If you track inventory by batch, the query must be more specific.
            ).first()

            if inventory:
                # Add the quantity back to the inventory
                inventory.quantity += item.quantity
                db.add(inventory)
                restored_items_count += 1
                print(f"INFO: Restored {item.quantity} of product {item.product_id} to inventory.")
            else:
                # Log or handle case where inventory record is missing (critical error)
                print(f"WARNING: Inventory item not found for product {item.product_id} in store {store_id}.")
                # Decide if you want to raise an exception or continue. Continuing for now.
                
        # 5. Mark the Bill as Canceled (Assuming you have a 'status' column on Bill)
        # If you don't have a status, you might delete the Bill and BillItems, but updating 
        # a status is safer for audit. Let's assume you add a status field:
        
        # --- (Requires Bill model update to include: status = Column(String(50), default="processed")) ---
        # bill.status = "canceled" 
        # db.add(bill)
        
        # If no status column, simply commit the inventory change and return success.

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"ERROR during order cancellation: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel order and restore inventory due to a database error.")

    return {
        "message": f"Bill {bill_id} canceled successfully.",
        "inventory_restored": True,
        "items_restored_count": restored_items_count
    }


# -------------------------
# Serve Product Image
# -------------------------

@router.get("/image/{product_id}")
def get_product_image(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    
    if not product or not product.image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    mime_type = product.image_mime or "image/jpeg"
    return Response(content=product.image, media_type=mime_type)



@router.get("/global/search")
async def global_search(
    query: str = Query(..., description="Search across multiple entities"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    role = current_user.role
    results = {}

    # ---- Helper: Safe UUID Conversion ----
    is_uuid = False
    try:
        uuid.UUID(query)
        is_uuid = True
    except ValueError:
        pass

    # ---- Search Doctors ----
    if role in ["doctor", "patient", "hospital_admin", "hospital_super_admin"]:
        doctors = db.query(Doctor).filter(
            (Doctor.name.ilike(f"%{query}%")) |
            (Doctor.specialization.ilike(f"%{query}%")) |
            (Doctor.clinic_name.ilike(f"%{query}%"))
        ).limit(10).all()
        results["doctors"] = doctors

    # ---- Search Patients ----
    if role in ["doctor", "hospital_admin", "hospital_super_admin"]:
        patients = db.query(Patient).filter(
            (Patient.name.ilike(f"%{query}%")) | 
            (Patient.email.ilike(f"%{query}%"))
        ).limit(10).all()
        results["patients"] = patients

    # ---- Search Customers ----
    if role in ["chemist", "hospital_admin", "hospital_super_admin"]:
        customers = db.query(Customer).filter(
            (Customer.name.ilike(f"%{query}%")) |
            (Customer.email.ilike(f"%{query}%"))
        ).limit(10).all()
        results["customers"] = customers

    # ---- Search Suppliers ----
    if role in ["chemist", "supplier", "hospital_admin", "hospital_super_admin"]:
        suppliers = db.query(Supplier).filter(
            (Supplier.company_name.ilike(f"%{query}%")) |
            (Supplier.contact_person.ilike(f"%{query}%"))
        ).limit(10).all()
        results["suppliers"] = suppliers

    # ---- Search Inventory ----
    if role in ["doctor", "patient", "customer", "hospital_admin", "hospital_super_admin"]:
        inventory = db.query(Inventory).filter(
            (Inventory.product_name.ilike(f"%{query}%")) |
            (Inventory.expiry_date.ilike(f"%{query}%")) |
            (Inventory.price.ilike(f"%{query}%"))
        ).limit(10).all()
        results["inventory"] = inventory

    # ---- Search Medical Stores ----
    if role in ["doctor", "customer", "patient", "hospital_admin", "hospital_super_admin"]:
        stores = db.query(MedicalStore).filter(
            (MedicalStore.store_name.ilike(f"%{query}%")) |
            (MedicalStore.owner_name.ilike(f"%{query}%"))
        ).limit(10).all()
        results["medical_stores"] = stores

    # ---- Search Patient History ----
    if role in ["doctor", "patient", "hospital_admin", "hospital_super_admin"]:
        history = db.query(MedicalHistory).filter(
            (MedicalHistory.diagnosis.ilike(f"%{query}%")) |
            (MedicalHistory.test_results.ilike(f"%{query}%")) |
            (MedicalHistory.visit_date.ilike(f"%{query}%"))
        ).limit(10).all()
        results["medical_history"] = history

    # ---- No Results ----
    if not any(results.values()):
        raise HTTPException(status_code=404, detail="No matching results found.")

    return results
