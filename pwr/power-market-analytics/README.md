# Indian Power Market Demand & Price Forecasting Platform

Project scaffold implementing ETL, ML models, and Django REST API for demand and day-ahead price forecasting.

See repository structure in project root and `requirements.txt` for dependencies.

Key components:
- Data ingestion and mock data generator
- ETL to load and validate into relational DB (SQLAlchemy)
- Model training: Gradient Boosting for demand, Random Forest for price
- Django REST API exposing forecasting endpoints and model metrics

Run notes:
- Create a virtualenv and install with `pip install -r requirements.txt`
- Use `python data_ingestion/generate_mock_data.py` to create sample CSVs
- Run `python etl/etl.py` to load data into `data.db` (SQLite by default)
- Train models with `python scripts/train_models.py`
- Start API: `python api/manage.py runserver` and call endpoints

See README sections in-code for data sources, feature logic, model rationale, failure modes, and scaling notes.
