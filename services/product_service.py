from sqlalchemy.orm import Session

from db.models import Product


class ProductService:
    """
    Business logic related to products.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_product(self, product_id: int) -> Product | None:
        return self.db.query(Product).filter(Product.id == product_id).one_or_none()

    def get_user_product(self, product_id: int, user_id: int) -> Product | None:
        """
        Return a product belonging to a specific user.
        """
        return (
            self.db.query(Product)
            .filter(
                Product.id == product_id,
                Product.user_id == user_id,
            )
            .one_or_none()
        )
