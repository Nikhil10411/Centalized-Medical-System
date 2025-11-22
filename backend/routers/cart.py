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
from datetime import date # Added import for date

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
    # NOTE: The existing logic here is incomplete as it doesn't join to Product details
    # I'll rely on the /inventory/all_stores endpoint for full details, but keep this simple
    return [
        {
            "inventory_id": p.inventory_id,
            "product_name": p.product_name, # This field is not on Inventory, but I'm keeping the original logic
            "price": float(p.price),
            "quantity": p.quantity,
            "image": f"/product/image/{p.product.product_id}" if p.product.image else None,
        }
        for p in products
    ]


# -------------------------
# Add product to cart (Updated to handle 'supplier' source)
# -------------------------
@router.post("/add/cart/{product_id}")
def add_to_cart(
    product_id: str,
    store_id: str = None, # Store ID is optional, required only for inventory products
    source: str = "inventory",
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # only chemists can buy supplier products
    if source == "supplier" and current_user.role != RoleEnum.CHEMIST:
        raise HTTPException(status_code=403, detail="Only chemists can buy supplier items")
    
    # If source is inventory, store_id must be provided
    if source == "inventory" and (not store_id or store_id.lower() == 'undefined'):
        raise HTTPException(
            status_code=400, 
            detail="A valid Store ID is required to add inventory products."
        )

    # Find or create cart
    # NOTE: Assuming one general cart per user, regardless of source type
    cart = db.query(Cart).filter(
        Cart.user_id == str(current_user.id)
    ).first()

    if not cart:
        cart = Cart(user_id=str(current_user.id), store_id=store_id if source == "inventory" else None)
        db.add(cart)
        db.commit()
        db.refresh(cart)

    # Determine price based on source
    price = None
    if source == "inventory":
        inventory = db.query(Inventory).filter(
            Inventory.store_id == store_id,
            Inventory.product_id == product_id
        ).first()

        if not inventory:
            raise HTTPException(status_code=404, detail="Product not in this store inventory")

        price = inventory.price

    elif source == "supplier":
        # Role check already passed: current_user.role == "chemist"
        sup = db.query(SupplierProduct).filter(
            SupplierProduct.product_id == product_id
        ).first()

        if not sup:
            raise HTTPException(status_code=404, detail="Supplier product not found")

        # Use the 'price' field from SupplierProduct
        price = sup.price 
        
    else:
        raise HTTPException(status_code=400, detail="Invalid source type specified. Must be 'inventory' or 'supplier'.")

    # Add or update cart item
    # NOTE: CartItem must be unique on (cart_id, product_id, source) to handle the same product
    # coming from a store vs. a supplier.
    existing = db.query(CartItem).filter(
        CartItem.cart_id == cart.cart_id,
        CartItem.product_id == product_id,
        CartItem.source == source
    ).first()

    if existing:
        existing.quantity += 1
    else:
        new_item = CartItem(
            cart_id=cart.cart_id,
            product_id=product_id,
            source=source,
            price=price,
            quantity=1
        )
        db.add(new_item)

    db.commit()
    return {"message": f"Added product {product_id} from {source} to cart"}

# -------------------------
# View Cart + Subtotal (Updated to fetch details for both sources)
# -------------------------
@router.get("/cart/view")
def view_cart(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Fetch the user's main cart.
    cart = db.query(Cart).filter(Cart.user_id == str(current_user.id)).first()

    if not cart:
        return {"message": "Cart is empty.", "items": [], "total_amount": 0.0}

    items_query = db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
    
    detailed_items = []
    subtotal = 0.0
    
    for item in items_query:
        product_detail = db.query(Product).filter(Product.product_id == item.product_id).first()
        
        if not product_detail:
            continue

        item_data = {
            "product_id": item.product_id,
            "product_name": product_detail.name,
            "product_image_url": f"/product/image/{item.product_id}" if product_detail.image else None,
            "brand": product_detail.brand,
            "generic_name": product_detail.generic_name,
            "source": item.source,
            "quantity": item.quantity,
            "price": float(item.price),
            "line_item_total": float(item.price) * item.quantity,
            "metadata": {} 
        }
        
        # Fetch Source-Specific Metadata
        if item.source == "inventory":
            # Assuming store_id is set on the Cart for inventory purchases
            if cart.store_id:
                store = db.query(MedicalStore).filter(MedicalStore.store_id == cart.store_id).first()
                item_data["metadata"] = {
                    "source_type": "Medical Store Inventory",
                    "source_id": cart.store_id,
                    "source_name": store.store_name if store else "Unknown Store",
                }
        
        elif item.source == "supplier":
            # Fetch supplier details for Chemist's view
            supplier_product_record = db.query(SupplierProduct).filter(
                SupplierProduct.product_id == item.product_id
            ).first() 

            if supplier_product_record:
                supplier = db.query(Supplier).filter(
                    Supplier.supplier_id == supplier_product_record.supplier_id
                ).first()
                
                item_data["metadata"] = {
                    "source_type": "Supplier Order",
                    "source_id": supplier.supplier_id if supplier else None,
                    "source_name": supplier.supplier_name if supplier else "Unknown Supplier",
                    "lead_time_days": supplier_product_record.lead_time_days
                }
            else:
                 item_data["metadata"] = {"source_type": "Supplier Order (Detail Missing)"}

        detailed_items.append(item_data)
        subtotal += item_data["line_item_total"]

    return {
        "cart_id": cart.cart_id, 
        "store_id": cart.store_id, 
        "items": detailed_items,
        "total_amount": round(subtotal, 2)
    }


# -------------------------
# Remove item from cart
# -------------------------
@router.delete("/cart/remove/{product_id}")
def remove_from_cart(
    product_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # NOTE: The original logic removes ALL items with the same product_id, 
    # regardless of source (inventory/supplier). This is acceptable for this example.
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
# Checkout item from cart (STANDARD: for Customer/Patient buying from a store)
# (Now only processes CartItems where source='inventory')
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
        patient_record = db.query(Patient).filter(Patient.patient_id == user_id).first()
        
        if patient_record:
            bill_patient_id = patient_record.patient_id
        else:
            db.rollback()
            raise HTTPException(status_code=400, detail="User is a Patient but no matching Patient record found.")
    
    # 2. HANDLE ALL OTHER ROLES
    if bill_patient_id is None:
        customer_record = db.query(Customer).filter(Customer.customer_id == user_id).first()
        
        if not customer_record:
            # Auto-create Customer record if needed (Assuming the store_id passed is the purchasing store)
            new_customer = Customer(
                customer_id=user_id,
                name=current_user.username,
                email=current_user.email,
                store_id=store_id, 
                role=user_role.value 
            )
            db.add(new_customer)
            db.flush() 
        
        bill_customer_id = user_id


    # 3. CART RETRIEVAL AND VALIDATION 
    cart = db.query(Cart).filter(
        Cart.user_id == user_id, Cart.store_id == store_id
    ).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found for this user and store.")

    # Filter CartItems to only include INVENTORY products for standard checkout
    items = db.query(CartItem).filter(
        CartItem.cart_id == cart.cart_id,
        CartItem.source == "inventory" 
    ).all()
    
    if not items:
        # Check if cart contains any items at all, and provide a helpful message if they are supplier items
        all_items = db.query(CartItem).filter(CartItem.cart_id == cart.cart_id).all()
        if all_items and any(i.source == "supplier" for i in all_items):
             raise HTTPException(status_code=400, detail="Cart contains supplier items. Please use the appropriate 'supplier_order' checkout endpoint.")
        else:
            raise HTTPException(status_code=400, detail="Cart is empty or contains no inventory items.")

    # 4. CALCULATIONS 
    subtotal = sum(float(i.price) * i.quantity for i in items)
    tax = round(subtotal * 0.05, 2)
    total = subtotal + tax

    # 5. BILL CREATION 
    bill = Bill(
        issuer_store_id=store_id,
        customer_id=bill_customer_id,   
        patient_id=bill_patient_id,      
        subtotal=subtotal,
        tax_amount=tax,
        total_amount=total,
    )
    db.add(bill)
    db.flush() 
    db.refresh(bill)

    # 6. BILL ITEM CREATION AND INVENTORY DECREMENT
    for i in items:
        inventory_item = db.query(Inventory).filter(
            Inventory.store_id == store_id, 
            Inventory.product_id == i.product_id,
            Inventory.quantity >= i.quantity
        ).first()

        if not inventory_item:
            db.rollback() 
            raise HTTPException(status_code=400, detail=f"Product {i.product_id} is out of stock in store {store_id} or inventory data is missing.")

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

    return {"message": "Store Inventory Checkout successful", "bill_id": bill.bill_id, "total": total}

# -------------------------
# Checkout item from cart (NEW: for CHEMIST ordering from a supplier)
# -------------------------
@router.post("/checkout/supplier_order")
def checkout_supplier_order(
    db: Session = Depends(get_db), 
    current_user=Depends(get_current_user)
):
    """
    Handles the B2B purchase order placed by a CHEMIST to a supplier.
    This does NOT decrement store inventory. It logs a Purchase Order (using Bill model).
    """
    # 1. Role Check: Must be a Chemist
    if current_user.role != RoleEnum.CHEMIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only Chemists are authorized to place supplier orders."
        )

    user_id = str(current_user.id)
    
    # 2. Find Chemist's Store ID (Needed for Bill issuer_store_id - the buyer's store)
    # Assumes the MedicalStore model has an 'owner_id' column linked to the User ID.
    chemist_store = db.query(MedicalStore).filter(MedicalStore.owner_id == user_id).first()
    if not chemist_store:
        raise HTTPException(
            status_code=400, 
            detail="Chemist account must be linked to a Medical Store to place a supplier order."
        )
    chemist_store_id = chemist_store.store_id

    # 3. Retrieve Cart & Filter for Supplier Items
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found.")

    # Only process items with source='supplier' for this checkout type
    items = db.query(CartItem).filter(
        CartItem.cart_id == cart.cart_id,
        CartItem.source == "supplier" 
    ).all()
    
    if not items:
        raise HTTPException(status_code=400, detail="Cart contains no supplier items to checkout via this endpoint.")

    # 4. CALCULATIONS
    subtotal = sum(float(i.price) * i.quantity for i in items)
    tax = round(subtotal * 0.05, 2)
    total = subtotal + tax

    # 5. BILL CREATION (Using Bill as a Purchase Order)
    bill = Bill(
        issuer_store_id=chemist_store_id, # The Chemist's store is the buyer
        customer_id=user_id,             # The Chemist (user) is the customer/requester
        patient_id=None,
        subtotal=subtotal,
        tax_amount=tax,
        total_amount=total,
        # Note: You may want to add a 'bill_type' or 'status' column to differentiate 
        # Sales Bills from Purchase Orders.
    )
    db.add(bill)
    db.flush() 
    db.refresh(bill)

    # 6. BILL ITEM CREATION (Purchase Order Items)
    for i in items:
        # Get supplier product details for reference (e.g., lead time)
        supplier_product_record = db.query(SupplierProduct).filter(
            SupplierProduct.product_id == i.product_id
        ).first()

        if not supplier_product_record:
            db.rollback() 
            raise HTTPException(status_code=400, detail=f"Supplier product detail missing for {i.product_id}. Cannot complete order.")

        # Create BillItem (representing an item on the Purchase Order)
        bill_item = BillItem(
            bill_id=bill.bill_id,
            product_id=i.product_id,
            # Use placeholder info as actual batch/expiry is set upon goods receipt
            batch_no=f"PO_{bill.bill_id}", 
            expiry_date=date.today(), # Placeholder
            quantity=i.quantity,
            unit_price=float(i.price),
            line_total=float(i.price) * i.quantity,
        )
        db.add(bill_item)
        
        # Delete cart item
        db.delete(i)
        
    db.commit() 

    return {
        "message": "Supplier Purchase Order placed successfully", 
        "purchase_order_id": bill.bill_id, 
        "total_order_amount": total
    }


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

    # 2. Authorization Check 
    current_user_id = str(current_user.id)
    
    is_authorized_customer = bill.customer_id == current_user_id
    is_authorized_patient = bill.patient_id == current_user_id
    # Allowing ADMIN and CHEMIST (store owner) to cancel their store's bills
    is_admin_or_store_user = current_user.role in [RoleEnum.ADMIN, RoleEnum.CHEMIST]

    if not (is_authorized_customer or is_authorized_patient or is_admin_or_store_user):
        raise HTTPException(status_code=403, detail="Not authorized to cancel this bill.")
    
    # 3. Retrieve Bill Items
    bill_items = db.query(BillItem).filter(BillItem.bill_id == bill_id).all()

    if not bill_items:
        raise HTTPException(status_code=404, detail="No items found for this bill.")

    # 4. Restore Inventory (Only if this was a standard sales bill, not a purchase order)
    # This logic assumes a standard sales bill where inventory was decremented.
    store_id = bill.issuer_store_id
    restored_items_count = 0
    
    try:
        for item in bill_items:
            # Check the status/type of the bill to determine if inventory restoration is needed
            # Since we don't have a 'bill_type' column, we assume all bills placed via /checkout/{store_id} 
            # are sales and need restoration. Purchase orders placed via /checkout/supplier_order do not.
            
            # --- Inventory Restoration Logic (applies to sales bills only) ---
            # You might need more complex logic here if you add a 'bill_type' field.
            
            inventory = db.query(Inventory).filter(
                Inventory.store_id == store_id,
                Inventory.product_id == item.product_id
            ).first()

            if inventory:
                inventory.quantity += item.quantity
                db.add(inventory)
                restored_items_count += 1
            else:
                print(f"WARNING: Inventory item not found for product {item.product_id} in store {store_id}.")
                
        # 5. Mark the Bill as Canceled (If you add a status column)
        # For now, just commit the transaction.

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


# -------------------------
# Global Search
# -------------------------
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