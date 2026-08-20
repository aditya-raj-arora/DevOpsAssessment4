import threading

WAREHOUSES = ["A", "B", "C"]
DEFAULT_REORDER_THRESHOLD = 10


class InventoryManagement:
    def __init__(self):
        self.warehouses = {wh: {} for wh in WAREHOUSES}
        self.suppliers = {}
        self.reorder_thresholds = {}
        self.reorder_log = []
        self.lock = threading.Lock()

    def _validate_warehouse(self, warehouse):
        if warehouse not in self.warehouses:
            raise ValueError(f"Invalid warehouse: {warehouse}")

    def add_supplier(self, supplier_id, name, contact):
        if supplier_id in self.suppliers:
            raise ValueError("Supplier already exists")
        self.suppliers[supplier_id] = {"name": name, "contact": contact, "products": set()}
        return True

    def link_supplier(self, supplier_id, product_id):
        if supplier_id not in self.suppliers:
            raise ValueError("Supplier does not exist")
        self.suppliers[supplier_id]["products"].add(product_id)

    def add_product(self, warehouse, product_id, quantity, reorder_threshold=DEFAULT_REORDER_THRESHOLD):
        self._validate_warehouse(warehouse)
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        with self.lock:
            self.warehouses[warehouse][product_id] = self.warehouses[warehouse].get(product_id, 0) + quantity
            self.reorder_thresholds.setdefault(product_id, reorder_threshold)
            self._check_reorder(warehouse, product_id)
            return self.warehouses[warehouse][product_id]

    def remove_product(self, warehouse, product_id, quantity):
        self._validate_warehouse(warehouse)
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        with self.lock:
            current = self.warehouses[warehouse].get(product_id, 0)
            if product_id not in self.warehouses[warehouse]:
                raise ValueError("Invalid product")
            if quantity > current:
                raise ValueError("Insufficient inventory")
            self.warehouses[warehouse][product_id] = current - quantity
            self._check_reorder(warehouse, product_id)
            return self.warehouses[warehouse][product_id]

    def transfer_stock(self, from_warehouse, to_warehouse, product_id, quantity):
        self._validate_warehouse(from_warehouse)
        self._validate_warehouse(to_warehouse)
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        with self.lock:
            current = self.warehouses[from_warehouse].get(product_id, 0)
            if quantity > current:
                raise ValueError("Insufficient inventory for transfer")
            self.warehouses[from_warehouse][product_id] = current - quantity
            self.warehouses[to_warehouse][product_id] = self.warehouses[to_warehouse].get(product_id, 0) + quantity
            self._check_reorder(from_warehouse, product_id)
            return True

    def _check_reorder(self, warehouse, product_id):
        threshold = self.reorder_thresholds.get(product_id, DEFAULT_REORDER_THRESHOLD)
        qty = self.warehouses[warehouse].get(product_id, 0)
        if qty <= threshold:
            self.reorder_log.append({"warehouse": warehouse, "product_id": product_id, "quantity": qty})
            return True
        return False

    def is_low_stock(self, warehouse, product_id):
        self._validate_warehouse(warehouse)
        threshold = self.reorder_thresholds.get(product_id, DEFAULT_REORDER_THRESHOLD)
        return self.warehouses[warehouse].get(product_id, 0) <= threshold

    def get_stock(self, warehouse, product_id):
        self._validate_warehouse(warehouse)
        return self.warehouses[warehouse].get(product_id, 0)

    def total_stock(self, product_id):
        return sum(self.warehouses[wh].get(product_id, 0) for wh in self.warehouses)

    def select_warehouse(self, product_id, quantity):
        candidates = [
            (wh, self.warehouses[wh].get(product_id, 0))
            for wh in self.warehouses
            if self.warehouses[wh].get(product_id, 0) >= quantity
        ]
        if not candidates:
            raise ValueError("Insufficient inventory across all warehouses")
        candidates.sort(key=lambda pair: -pair[1])
        return candidates[0][0]

    def fulfill_order(self, product_id, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        with self.lock:
            candidates = [
                (wh, self.warehouses[wh].get(product_id, 0))
                for wh in self.warehouses
                if self.warehouses[wh].get(product_id, 0) >= quantity
            ]
            if not candidates:
                raise ValueError("Insufficient inventory across all warehouses")
            candidates.sort(key=lambda pair: -pair[1])
            warehouse = candidates[0][0]
            self.warehouses[warehouse][product_id] -= quantity
            self._check_reorder(warehouse, product_id)
            return warehouse
