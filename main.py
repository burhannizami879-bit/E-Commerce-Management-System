#E-Commerce Management System

from pydantic import BaseModel, Field, field_validator, EmailStr, model_validator, computed_field, ValidationError
from typing import Annotated, Literal
from enum import Enum
from datetime import date
from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent

PRODUCT_FILE = BASE_DIR / "products.json"
CUSTOMER_FILE = BASE_DIR / "customers.json"
ORDER_FILE = BASE_DIR / "orders.json"


class ProductCategory(str, Enum):
    ELECTRONICS = "Electronics"
    CLOTHING = "Clothing"
    GROCERY = "Grocery"
    BOOKS = "Books"


class ProductStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class PaymentMethod(str, Enum):
    CASH = "Cash"
    CARD = "Card"
    BANK_TRANSFER = "Bank Transfer"


class OrderStatus(str, Enum):
    PENDING = "Pending"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"


class Product(BaseModel):
    product_id: Annotated[str, Field(pattern=r"^PR\d{3,}$")]
    product_name: Annotated[str, Field(min_length=3, max_length=60)]
    description: Annotated[str, Field(min_length=5, max_length=500)]
    price: Annotated[int, Field(gt=0)]
    category: ProductCategory
    stock_quantity: Annotated[int, Field(ge=0)]
    discount_percentage: Annotated[float, Field(ge=0, le=70)] = 0
    status: ProductStatus = ProductStatus.ACTIVE

    @field_validator("product_name")
    @classmethod
    def clean_product_name(cls, value):
        return value.strip().title()

    @computed_field
    @property
    def discount_amount(self) -> float:
        return self.price * self.discount_percentage / 100

    @computed_field
    @property
    def final_price(self) -> float:
        return self.price - self.discount_amount


class Customer(BaseModel):
    customer_id: Annotated[str, Field(pattern=r"^CUST\d{3,}$")]
    full_name: Annotated[str, Field(min_length=3, max_length=60)]
    email: EmailStr
    phone_number: Annotated[str, Field(pattern=r"^03\d{9}$")]
    age: Annotated[int, Field(ge=18, le=100)]
    address: Annotated[str, Field(min_length=5, max_length=200)]
    gender: Literal["Male", "Female", "Others"]

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value):
        return value.strip().title()


class Order(BaseModel):
    order_id: Annotated[str, Field(pattern=r"^ORD\d{3,}$")]
    customer: Customer
    product: Product
    quantity: Annotated[int, Field(gt=0)]
    order_date: date
    payment_method: PaymentMethod
    order_status: OrderStatus = OrderStatus.PENDING

    @model_validator(mode="after")
    def check_order(self):
        if self.quantity > self.product.stock_quantity:
            raise ValueError("Not enough product stock")
        return self

    @computed_field
    @property
    def total_price(self) -> float:
        return self.product.final_price * self.quantity


products = {}
customers = {}
orders = {}


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

            if not isinstance(data, dict):
                raise ValueError("Invalid JSON file structure")

            return data

    except FileNotFoundError:
        return {}

    except (json.JSONDecodeError, ValueError) as error:
        print("File error:", error)
        return {}


def load_products():
    data = load_json(PRODUCT_FILE)

    for product_id, product_data in data.items():
        try:
            products[product_id] = Product(**product_data)
        except (ValidationError, TypeError) as error:
            print("Product error:", error)


def save_products():
    data = {
        product_id: product.model_dump(mode="json")
        for product_id, product in products.items()
    }
    save_json(PRODUCT_FILE, data)


def load_customers():
    data = load_json(CUSTOMER_FILE)

    for customer_id, customer_data in data.items():
        try:
            customers[customer_id] = Customer(**customer_data)
        except (ValidationError, TypeError) as error:
            print("Customer error:", error)


def save_customers():
    data = {
        customer_id: customer.model_dump(mode="json")
        for customer_id, customer in customers.items()
    }
    save_json(CUSTOMER_FILE, data)


def load_orders():
    data = load_json(ORDER_FILE)

    for order_id, order_data in data.items():
        try:
            orders[order_id] = Order(**order_data)
        except (ValidationError, TypeError) as error:
            print("Order error:", error)


def save_orders():
    data = {
        order_id: order.model_dump(mode="json")
        for order_id, order in orders.items()
    }
    save_json(ORDER_FILE, data)


def add_product():
    try:
        product_id = input("Enter Product ID: ").strip().upper()

        if product_id in products:
            print("Product ID already exists")
            return

        product = Product(
            product_id=product_id,
            product_name=input("Enter Product Name: "),
            description=input("Enter Description: "),
            price=int(input("Enter Price: ")),
            category=input("Enter Category: ").strip().title(),
            stock_quantity=int(input("Enter Stock Quantity: ")),
            discount_percentage=float(input("Enter Discount Percentage (default 0): ") or 0),
            status=input("Enter Status (Active/Inactive, default Active): ").strip().title() or "Active"
        )

        products[product_id] = product
        save_products()

        print("Product added successfully")

    except (ValidationError, ValueError) as error:
        print(error)


def display_products():
    if not products:
        print("No products available")
        return

    for product in products.values():
        print(product.model_dump())


def search_product():
    keyword = input("Enter Product ID or Product Name: ").strip().lower()

    found = False

    for product in products.values():
        if keyword in product.product_name.lower() or keyword == product.product_id.lower():
            print(product.model_dump())
            found = True

    if not found:
        print("Product not found")


def search_by_category():
    category = input("Enter Category: ").strip().lower()

    found = False

    for product in products.values():
        if product.category.value.lower() == category:
            print(product.model_dump())
            found = True

    if not found:
        print("Category not found")


def update_product():
    product_id = input("Enter Product ID: ").strip().upper()

    if product_id not in products:
        print("Product not found")
        return

    try:
        product = products[product_id]

        updated_data = product.model_dump(
            exclude={"discount_amount", "final_price"}
        )

        new_name = input("Enter New Name (blank to skip): ")
        new_description = input("Enter New Description (blank to skip): ")
        new_price = input("Enter New Price (blank to skip): ")
        new_category = input("Enter New Category (blank to skip): ")
        new_stock = input("Enter New Stock (blank to skip): ")
        new_discount = input("Enter New Discount (blank to skip): ")
        new_status = input("Enter New Status (blank to skip): ")

        if new_name.strip():
            updated_data["product_name"] = new_name

        if new_description.strip():
            updated_data["description"] = new_description

        if new_price.strip():
            updated_data["price"] = int(new_price)

        if new_category.strip():
            updated_data["category"] = new_category.strip().title()

        if new_stock.strip():
            updated_data["stock_quantity"] = int(new_stock)

        if new_discount.strip():
            updated_data["discount_percentage"] = float(new_discount)

        if new_status.strip():
            updated_data["status"] = new_status.strip().title()

        updated_product = Product(**updated_data)

        products[product_id] = updated_product
        save_products()

        print("Product updated successfully")

    except (ValidationError, ValueError) as error:
        print(error)


def delete_product():
    product_id = input("Enter Product ID: ").strip().upper()

    if product_id not in products:
        print("Product not found")
        return

    for order in orders.values():
        if order.product.product_id == product_id and order.order_status != OrderStatus.CANCELLED:
            print("Cannot delete product with an active order")
            return

    del products[product_id]
    save_products()

    print("Product deleted successfully")


def add_customer():
    try:
        customer_id = input("Enter Customer ID: ").strip().upper()

        if customer_id in customers:
            print("Customer ID already exists")
            return

        customer = Customer(
            customer_id=customer_id,
            full_name=input("Enter Full Name: "),
            email=input("Enter Email: "),
            phone_number=input("Enter Phone Number: "),
            age=int(input("Enter Age: ")),
            address=input("Enter Address: "),
            gender=input("Enter Gender (Male/Female/Others): ").strip().title()
        )

        customers[customer_id] = customer
        save_customers()

        print("Customer added successfully")

    except (ValidationError, ValueError) as error:
        print(error)


def display_customers():
    if not customers:
        print("No customers available")
        return

    for customer in customers.values():
        print(customer.model_dump())


def search_customer():
    keyword = input("Enter Customer ID or Name: ").strip().lower()

    found = False

    for customer in customers.values():
        if keyword == customer.customer_id.lower() or keyword in customer.full_name.lower():
            print(customer.model_dump())
            found = True

    if not found:
        print("Customer not found")


def update_customer():
    customer_id = input("Enter Customer ID: ").strip().upper()

    if customer_id not in customers:
        print("Customer not found")
        return

    try:
        customer = customers[customer_id]
        updated_data = customer.model_dump()

        new_name = input("Enter New Name (blank to skip): ")
        new_email = input("Enter New Email (blank to skip): ")
        new_phone = input("Enter New Phone (blank to skip): ")
        new_age = input("Enter New Age (blank to skip): ")
        new_address = input("Enter New Address (blank to skip): ")
        new_gender = input("Enter New Gender (blank to skip): ")

        if new_name.strip():
            updated_data["full_name"] = new_name

        if new_email.strip():
            updated_data["email"] = new_email

        if new_phone.strip():
            updated_data["phone_number"] = new_phone

        if new_age.strip():
            updated_data["age"] = int(new_age)

        if new_address.strip():
            updated_data["address"] = new_address

        if new_gender.strip():
            updated_data["gender"] = new_gender.strip().title()

        updated_customer = Customer(**updated_data)

        customers[customer_id] = updated_customer
        save_customers()

        print("Customer updated successfully")

    except (ValidationError, ValueError) as error:
        print(error)


def delete_customer():
    customer_id = input("Enter Customer ID: ").strip().upper()

    if customer_id not in customers:
        print("Customer not found")
        return

    for order in orders.values():
        if order.customer.customer_id == customer_id:
            print("Cannot delete a customer with order history")
            return

    del customers[customer_id]
    save_customers()

    print("Customer deleted successfully")


def create_order():
    try:
        order_id = input("Enter Order ID: ").strip().upper()

        if order_id in orders:
            print("Order ID already exists")
            return

        customer_id = input("Enter Customer ID: ").strip().upper()
        product_id = input("Enter Product ID: ").strip().upper()

        if customer_id not in customers:
            print("Customer not found")
            return

        if product_id not in products:
            print("Product not found")
            return

        customer = customers[customer_id]
        product = products[product_id]

        if product.status == ProductStatus.INACTIVE:
            print("This product is inactive")
            return

        quantity = int(input("Enter Quantity: "))

        order = Order(
            order_id=order_id,
            customer=customer,
            product=product,
            quantity=quantity,
            order_date=date.fromisoformat(
                input("Enter Order Date (YYYY-MM-DD): ")
            ),
            payment_method=input(
                "Enter Payment Method (Cash/Card/Bank Transfer): "
            ).strip().title()
        )

        product.stock_quantity -= quantity

        orders[order_id] = order

        save_orders()
        save_products()

        print("Order created successfully")
        print("Total Price:", order.total_price)

    except (ValidationError, ValueError) as error:
        print(error)


def display_orders():
    if not orders:
        print("No orders available")
        return

    for order in orders.values():
        print(order.model_dump())


def search_order():
    order_id = input("Enter Order ID: ").strip().upper()

    if order_id in orders:
        print(orders[order_id].model_dump())
    else:
        print("Order not found")


def update_order_status():
    order_id = input("Enter Order ID: ").strip().upper()

    if order_id not in orders:
        print("Order not found")
        return

    order = orders[order_id]

    if order.order_status == OrderStatus.CANCELLED:
        print("Cancelled order cannot be updated")
        return

    try:
        print("Available Statuses:")

        for status in OrderStatus:
            if status != OrderStatus.CANCELLED:
                print(status.value)

        new_status = input("Enter New Status: ").strip().title()

        if new_status == OrderStatus.CANCELLED.value:
            print("Use Cancel Order option to cancel an order")
            return

        updated_data = order.model_dump(exclude={"total_price"})
        updated_data["order_status"] = new_status

        updated_order = Order(**updated_data)

        orders[order_id] = updated_order
        save_orders()

        print("Order status updated successfully")

    except (ValidationError, ValueError) as error:
        print(error)


def cancel_order():
    order_id = input("Enter Order ID: ").strip().upper()

    if order_id not in orders:
        print("Order not found")
        return

    order = orders[order_id]

    if order.order_status == OrderStatus.CANCELLED:
        print("Order is already cancelled")
        return

    product_id = order.product.product_id

    if product_id not in products:
        print("Original product no longer exists")
        return

    products[product_id].stock_quantity += order.quantity

    updated_data = order.model_dump(exclude={"total_price"})
    updated_data["order_status"] = OrderStatus.CANCELLED

    updated_order = Order(**updated_data)

    orders[order_id] = updated_order

    save_products()
    save_orders()

    print("Order cancelled successfully")
    print("Product stock restored successfully")


load_products()
load_customers()
load_orders()


while True:

    print("\n========== E-COMMERCE MANAGEMENT SYSTEM ==========")

    print("\n1. Add Product")
    print("2. Display Products")
    print("3. Search Product")
    print("4. Search Product by Category")
    print("5. Update Product")
    print("6. Delete Product")

    print("\n7. Add Customer")
    print("8. Display Customers")
    print("9. Search Customer")
    print("10. Update Customer")
    print("11. Delete Customer")

    print("\n12. Create Order")
    print("13. Display Orders")
    print("14. Search Order")
    print("15. Update Order Status")
    print("16. Cancel Order")

    print("\n17. Exit")

    choice = input("\nEnter Your Choice: ").strip()

    if choice == "1":
        add_product()

    elif choice == "2":
        display_products()

    elif choice == "3":
        search_product()

    elif choice == "4":
        search_by_category()

    elif choice == "5":
        update_product()

    elif choice == "6":
        delete_product()

    elif choice == "7":
        add_customer()

    elif choice == "8":
        display_customers()

    elif choice == "9":
        search_customer()

    elif choice == "10":
        update_customer()

    elif choice == "11":
        delete_customer()

    elif choice == "12":
        create_order()

    elif choice == "13":
        display_orders()

    elif choice == "14":
        search_order()

    elif choice == "15":
        update_order_status()

    elif choice == "16":
        cancel_order()

    elif choice == "17":
        print("Program closed successfully!")
        break

    else:
        print("Invalid choice! Please try again.")
