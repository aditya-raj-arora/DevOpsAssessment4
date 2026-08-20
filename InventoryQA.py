import unittest
import threading
from InventoryManagement import InventoryManagement


class TestStockAvailability(unittest.TestCase):
    def test_fulfill_order_from_warehouse_with_stock(self):
        inv = InventoryManagement()
        inv.add_product("A", "P1", 50)
        warehouse = inv.fulfill_order("P1", 20)
        self.assertEqual(warehouse, "A")
        self.assertEqual(inv.get_stock("A", "P1"), 30)


class TestInsufficientInventory(unittest.TestCase):
    def test_remove_more_than_available(self):
        inv = InventoryManagement()
        inv.add_product("A", "P1", 10)
        with self.assertRaises(ValueError):
            inv.remove_product("A", "P1", 20)

    def test_fulfill_order_no_warehouse_has_enough(self):
        inv = InventoryManagement()
        inv.add_product("A", "P1", 5)
        inv.add_product("B", "P1", 3)
        with self.assertRaises(ValueError):
            inv.fulfill_order("P1", 10)


class TestWarehouseTransfer(unittest.TestCase):
    def test_transfer_between_warehouses(self):
        inv = InventoryManagement()
        inv.add_product("A", "P1", 50)
        inv.transfer_stock("A", "B", "P1", 20)
        self.assertEqual(inv.get_stock("A", "P1"), 30)
        self.assertEqual(inv.get_stock("B", "P1"), 20)

    def test_transfer_more_than_available(self):
        inv = InventoryManagement()
        inv.add_product("A", "P1", 5)
        with self.assertRaises(ValueError):
            inv.transfer_stock("A", "B", "P1", 10)


class TestConcurrentOrders(unittest.TestCase):
    def test_concurrent_orders_do_not_oversell(self):
        inv = InventoryManagement()
        inv.add_product("A", "P1", 100)
        errors = []

        def place_order():
            try:
                inv.fulfill_order("P1", 10)
            except ValueError:
                errors.append("out_of_stock")

        threads = [threading.Thread(target=place_order) for _ in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(inv.get_stock("A", "P1"), 0)
        self.assertEqual(len(errors), 5)


class TestReorderThreshold(unittest.TestCase):
    def test_low_stock_triggers_reorder_log(self):
        inv = InventoryManagement()
        inv.add_product("A", "P1", 15, reorder_threshold=10)
        self.assertFalse(inv.is_low_stock("A", "P1"))
        inv.remove_product("A", "P1", 6)
        self.assertTrue(inv.is_low_stock("A", "P1"))
        self.assertEqual(len(inv.reorder_log), 1)


class TestInvalidProduct(unittest.TestCase):
    def test_remove_unknown_product(self):
        inv = InventoryManagement()
        with self.assertRaises(ValueError):
            inv.remove_product("A", "UNKNOWN", 1)

    def test_invalid_warehouse(self):
        inv = InventoryManagement()
        with self.assertRaises(ValueError):
            inv.add_product("Z", "P1", 10)


class TestNegativeInventory(unittest.TestCase):
    def test_negative_quantity_add_rejected(self):
        inv = InventoryManagement()
        with self.assertRaises(ValueError):
            inv.add_product("A", "P1", -5)

    def test_stock_never_goes_negative(self):
        inv = InventoryManagement()
        inv.add_product("A", "P1", 5)
        with self.assertRaises(ValueError):
            inv.remove_product("A", "P1", 6)
        self.assertEqual(inv.get_stock("A", "P1"), 5)


class TestMultipleWarehouses(unittest.TestCase):
    def test_selects_warehouse_with_most_stock(self):
        inv = InventoryManagement()
        inv.add_product("A", "P1", 20)
        inv.add_product("B", "P1", 80)
        inv.add_product("C", "P1", 40)
        warehouse = inv.select_warehouse("P1", 30)
        self.assertEqual(warehouse, "B")

    def test_total_stock_across_warehouses(self):
        inv = InventoryManagement()
        inv.add_product("A", "P1", 20)
        inv.add_product("B", "P1", 30)
        inv.add_product("C", "P1", 10)
        self.assertEqual(inv.total_stock("P1"), 60)


if __name__ == "__main__":
    unittest.main()
