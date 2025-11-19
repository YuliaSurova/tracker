from __future__ import annotations

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func#для суммирования

# Configure and initialize Flask + SQLite
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    count = db.Column(db.Float, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

    def to_dict(self) -> dict[str, str | int | float]:
        return {"id": self.id, "name": self.name, "count": self.count, "day": self.day, "month": self.month, "year": self.year}


def create_tables() -> None:
    """Ensure tables exist before the first request hits the app."""
    with app.app_context():
        db.create_all()


@app.get("/items")
def list_items():
    items = Item.query.order_by(Item.id.asc()).all()
    return jsonify([item.to_dict() for item in items])


@app.post("/items")
def create_item():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    count = payload.get("count")
    day = payload.get("day")
    month = payload.get("month")
    year = payload.get("year")
    if not name:
        return jsonify({"error": "name is required"}), 400

    item = Item(name=name, count=count,day=day,month=month,year=year)
    db.session.add(item)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "failed to save item"}), 500

    return jsonify(item.to_dict()), 201


@app.get("/sum")
def sum_get():
    items = Item.query.order_by(Item.id.asc()).all()
    total_count = db.session.query(func.sum(Item.count)).scalar() or 0
    return jsonify({"total_count": total_count})

@app.post("/items-by-date")
def post_items_by_date():
    payload = request.get_json(silent=True) or {}#получаем данные или если их нет то пустой словарь
    day = payload.get("day")#получаем данные
    month = payload.get("month")
    year = payload.get("year")
    if day is None or month is None or year is None:#если нет дня,месяца или года, то ретерним ошибку
        return jsonify({"error": "day, month and year are required"}),400
    items = Item.query.filter_by(#фильтруем по дню,месяцу году
        day = day,
        month = month,
        year = year
    ).with_entities(Item.name, Item.count).all()#получаем только name и count
    result = [{"name": item.name, "count": item.count} for item in items]
    return jsonify(result)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Ensure tables are created before serving requests
    create_tables()
    app.run(host="0.0.0.0", port=9000, debug=True)