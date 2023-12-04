from django.test import TestCase

from utagmsapi.models import Category, Criterion, User, Project, CriterionCategory
from utagmsapi.utils.recursive_queries import RecursiveQueries


class RecursiveQueriesTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="test@test.com",
            password="test",
            name="test",
            surname="test"
        )
        self.project = Project.objects.create(
            name="Test Project",
            shareable=False,
            pairwise_mode=False,
            user=self.user
        )
        self.category_root = Category.objects.create(
            name='Root Category',
            color="teal.500",
            project=self.project
        )
        self.category_1 = Category.objects.create(
            name='Category 1',
            color="teal.500",
            parent=self.category_root,
            project=self.project
        )
        self.category_2 = Category.objects.create(
            name='Category 2',
            color="teal.500",
            parent=self.category_root,
            project=self.project
        )
        self.category_3 = Category.objects.create(
            name='Category 3',
            color="teal.500",
            parent=self.category_1,
            project=self.project
        )
        self.category_4 = Category.objects.create(
            name='Category 4',
            color="teal.500",
            parent=self.category_1,
            project=self.project
        )
        self.category_5 = Category.objects.create(
            name='Category 5',
            color="teal.500",
            parent=self.category_2,
            project=self.project
        )
        self.category_6 = Category.objects.create(
            name='Category 6',
            color="teal.500",
            parent=self.category_2,
            project=self.project
        )

        self.criterion_g1 = Criterion.objects.create(
            name='g1',
            gain=True,
            linear_segments=1,
            project=self.project
        )
        self.cc_g1 = CriterionCategory.objects.create(
            category=self.category_3,
            criterion=self.criterion_g1
        )

        self.criterion_g2 = Criterion.objects.create(
            name='g2',
            gain=True,
            linear_segments=2,
            project=self.project
        )
        self.cc_g2 = CriterionCategory.objects.create(
            category=self.category_3,
            criterion=self.criterion_g2
        )

        self.criterion_g3 = Criterion.objects.create(
            name='g3',
            gain=True,
            linear_segments=3,
            project=self.project
        )
        self.cc_g3 = CriterionCategory.objects.create(
            category=self.category_4,
            criterion=self.criterion_g3
        )

        self.criterion_g4 = Criterion.objects.create(
            name='g4',
            gain=True,
            linear_segments=4,
            project=self.project
        )
        self.cc_g4 = CriterionCategory.objects.create(
            category=self.category_4,
            criterion=self.criterion_g4
        )

        self.criterion_c1 = Criterion.objects.create(
            name='c1',
            gain=False,
            linear_segments=1,
            project=self.project
        )
        self.cc_c1_1 = CriterionCategory.objects.create(
            category=self.category_4,
            criterion=self.criterion_c1
        )
        self.cc_c1_2 = CriterionCategory.objects.create(
            category=self.category_5,
            criterion=self.criterion_c1
        )

        self.criterion_g5 = Criterion.objects.create(
            name='g5',
            gain=True,
            linear_segments=5,
            project=self.project
        )
        self.cc_g5 = CriterionCategory.objects.create(
            category=self.category_5,
            criterion=self.criterion_g5
        )

        self.criterion_g6 = Criterion.objects.create(
            name='g6',
            gain=True,
            linear_segments=6,
            project=self.project
        )
        self.cc_g6 = CriterionCategory.objects.create(
            category=self.category_root,
            criterion=self.criterion_g6
        )

        self.criterion_c2 = Criterion.objects.create(
            name='c2',
            gain=False,
            linear_segments=2,
            project=self.project
        )
        self.cc_c2 = CriterionCategory.objects.create(
            category=self.category_6,
            criterion=self.criterion_c2
        )

    def test_get_categories_subtree(self):
        # whole tree
        result = RecursiveQueries.get_categories_subtree(self.category_root.id)
        self.assertQuerySetEqual(result, [
            self.category_root,
            self.category_1,
            self.category_2,
            self.category_3,
            self.category_4,
            self.category_5,
            self.category_6
        ], ordered=False)

        # first subtree
        result = RecursiveQueries.get_categories_subtree(self.category_1.id)
        self.assertQuerySetEqual(result, [
            self.category_1,
            self.category_3,
            self.category_4
        ], ordered=False)

        # second subtree
        result = RecursiveQueries.get_categories_subtree(self.category_2.id)
        self.assertQuerySetEqual(result, [
            self.category_2,
            self.category_5,
            self.category_6
        ], ordered=False)

        # single node
        result = RecursiveQueries.get_categories_subtree(self.category_3.id)
        self.assertQuerySetEqual(result, [self.category_3], ordered=False)

        # invalid id
        result = RecursiveQueries.get_categories_subtree(-1)
        self.assertQuerySetEqual(result, [], ordered=False)

    def test_get_criteria_for_category(self):
        # whole tree
        result = RecursiveQueries.get_criteria_for_category(self.category_root.id)
        self.assertQuerySetEqual(result, [
            self.criterion_g1,
            self.criterion_g2,
            self.criterion_g3,
            self.criterion_g4,
            self.criterion_c1,
            self.criterion_g5,
            self.criterion_c2,
            self.criterion_g6
        ], ordered=False)

        # first subtree
        result = RecursiveQueries.get_criteria_for_category(self.category_1.id)
        self.assertQuerySetEqual(result, [
            self.criterion_g1,
            self.criterion_g2,
            self.criterion_g3,
            self.criterion_g4,
            self.criterion_c1
        ], ordered=False)

        # second subtree
        result = RecursiveQueries.get_criteria_for_category(self.category_2.id)
        self.assertQuerySetEqual(result, [
            self.criterion_c1,
            self.criterion_g5,
            self.criterion_c2
        ], ordered=False)

        # single node
        result = RecursiveQueries.get_criteria_for_category(self.category_4.id)
        self.assertQuerySetEqual(result, [
            self.criterion_g3,
            self.criterion_g4,
            self.criterion_c1
        ], ordered=False)

        # invalid id
        result = RecursiveQueries.get_categories_subtree(-1)
        self.assertQuerySetEqual(result, [], ordered=False)

    def tearDown(self):
        pass
