from pydantic import BaseModel


class InventoryEvent(BaseModel):
    event_id: str
    product_id: str
    store_id: str
    category: str
    current_stock: int
    shelf_capacity: int
    sales_last_10min: int
    replenishment_pending: int
    timestamp: str


class ScoreRequest(BaseModel):
    current_stock: int
    shelf_capacity: int
    sales_last_10min: int
    stock_ratio: float
    replenishment_pending: int
    category_encoded: int
    store_encoded: int


class ScoreResponse(BaseModel):
    stockout_risk: bool
    stockout_probability: float
    model: str


class ScoredInventoryEvent(BaseModel):
    event_id: str
    product_id: str
    store_id: str
    category: str
    current_stock: int
    shelf_capacity: int
    sales_last_10min: int
    replenishment_pending: int
    timestamp: str

    stock_ratio: float
    stockout_risk: bool
    stockout_probability: float
    model: str


class OnlineTrainingEvent(BaseModel):
    event_id: str
    product_id: str
    store_id: str
    category: str
    timestamp: str

    current_stock: int
    shelf_capacity: int
    sales_last_10min: int
    stock_ratio: float
    replenishment_pending: int
    category_encoded: int
    store_encoded: int

    stockout_label: int


class StockoutAlert(BaseModel):
    event_id: str
    product_id: str
    store_id: str
    category: str
    current_stock: int
    shelf_capacity: int
    sales_last_10min: int
    replenishment_pending: int
    timestamp: str

    stockout_probability: float
    alert_source: str
    alert_reason: str