from sqlalchemy import text

from app.database import engine


def main() -> None:
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT
                        current_database() AS database_name,
                        current_user AS database_user,
                        (
                            SELECT COUNT(*)
                            FROM transactions
                        ) AS transaction_count
                    """
                )
            ).mappings().one()

        print("PostgreSQL connection successful.")
        print(f"Database: {result['database_name']}")
        print(f"User: {result['database_user']}")
        print(f"Transactions: {result['transaction_count']}")

    except Exception as exc:
        print("PostgreSQL connection failed.")
        print(f"{type(exc).__name__}: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()