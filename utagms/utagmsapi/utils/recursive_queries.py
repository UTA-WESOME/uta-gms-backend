from django.db import connection
from django.db.models import QuerySet

from utagmsapi.models import Category, Criterion


class RecursiveQueries:
    __CATEGORIES_QUERY = """
        WITH RECURSIVE category_tree AS (
            SELECT id FROM utagmsapi_category WHERE id = %s
            UNION
            SELECT c.id
            FROM utagmsapi_category c
            INNER JOIN category_tree ct ON c.parent_id = ct.id
            WHERE c.active = TRUE
        )
        SELECT DISTINCT cat.id
        FROM utagmsapi_category cat
        WHERE cat.id IN (SELECT id FROM category_tree);
    """

    __CRITERIA_QUERY = """
        WITH RECURSIVE category_tree AS (
            SELECT id FROM utagmsapi_category WHERE id = %s
            UNIONó
            SELECT c.id
            FROM utagmsapi_category c
            INNER JOIN category_tree ct ON c.parent_id = ct.id
            WHERE c.active = TRUE
        )
        SELECT DISTINCT c.id, c.name
        FROM utagmsapi_criterion c
        INNER JOIN utagmsapi_criterioncategory cc ON c.id = cc.criterion_id
        INNER JOIN utagmsapi_category cat ON cat.id = cc.category_id
        WHERE cat.id IN (SELECT id FROM category_tree);
    """

    @classmethod
    def get_categories_subtree(cls, category_id: int) -> QuerySet[Category]:
        """Get subtree of categories with the root as category with provided id"""
        with connection.cursor() as cursor:
            cursor.execute(cls.__CATEGORIES_QUERY, [category_id])
            results = cursor.fetchall()
        return Category.objects.filter(id__in=[result[0] for result in results])

    @classmethod
    def get_criteria_for_category(cls, category_id: int) -> QuerySet[Criterion]:
        """Returns Criteria that are leaves of children of the category with provided id"""
        with connection.cursor() as cursor:
            cursor.execute(cls.__CRITERIA_QUERY, [category_id])
            results = cursor.fetchall()
        return Criterion.objects.filter(id__in=[result[0] for result in results])
