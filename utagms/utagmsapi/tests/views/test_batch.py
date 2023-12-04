from django.test import TestCase
from parameterized import parameterized

from utagmsapi.models import Alternative, Criterion, Performance, Project, User
from utagmsapi.views.batch import BatchOperations


class BatchOperationsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com", password="test", name="test", surname="test")
        self.project = Project.objects.create(name="Test Project", shareable=False, pairwise_mode=False, user=self.user)

        self.criterion_g1 = Criterion.objects.create(name='g1', gain=True, linear_segments=1, project=self.project)
        self.criterion_g2 = Criterion.objects.create(name='g2', gain=True, linear_segments=1, project=self.project)
        self.criterion_c1 = Criterion.objects.create(name='c1', gain=True, linear_segments=1, project=self.project)
        self.criteria = [self.criterion_g1, self.criterion_g2, self.criterion_c1]

        self.alternative_A = Alternative.objects.create(name='A', project=self.project)
        self.alternative_B = Alternative.objects.create(name='B', project=self.project)
        self.alternative_C = Alternative.objects.create(name='C', project=self.project)
        self.alternative_D = Alternative.objects.create(name='D', project=self.project)
        self.alternatives = [self.alternative_A, self.alternative_B, self.alternative_C, self.alternative_D]

        self.performance_A_g1 = Performance.objects.create(value=1, alternative=self.alternative_A,
                                                           criterion=self.criterion_g1)
        self.performance_A_g2 = Performance.objects.create(value=1, alternative=self.alternative_A,
                                                           criterion=self.criterion_g2)
        self.performance_A_c1 = Performance.objects.create(value=1, alternative=self.alternative_A,
                                                           criterion=self.criterion_c1)
        self.performances = [self.performance_A_g1, self.performance_A_g2, self.performance_A_c1]

    @parameterized.expand([
        ("delete all", [], []),
        ("delete none",
         ['criterion_g1', 'criterion_g2', 'criterion_c1'],
         ['criterion_g1', 'criterion_g2', 'criterion_c1']),
        ("delete g1", ['criterion_g2', 'criterion_c1'], ['criterion_g2', 'criterion_c1'])
    ])
    def test_delete_criteria(self, name, criteria_names, expected_result):
        criteria_data = [{'id': getattr(self, name).id} for name in criteria_names]
        expected_result = [getattr(self, name) for name in expected_result]

        BatchOperations.delete_criteria(self.project, criteria_data)
        self.assertQuerySetEqual(self.project.criteria.all(), expected_result)

    @parameterized.expand([
        ("insert new criterion", {'name': 'new_g3', 'gain': True, 'linear_segments': 2}, '', True),
        ("update existing criterion", {'name': 'updated_criterion', 'gain': True, 'linear_segments': 2}, 'criterion_g1',
         False),
    ])
    def test_insert_update_criterion(self, name, criterion_data, criterion_name, expect_insert):
        if not expect_insert:
            criterion_data['id'] = getattr(self, criterion_name).id
        result = BatchOperations.insert_update_criterion(self.project, criterion_data)
        if expect_insert:
            self.assertNotIn(result.id, self.criteria)
        else:
            self.assertEqual(result.id, getattr(self, criterion_name).id)
        self.assertEqual(result.name, criterion_data['name'])
        self.assertEqual(result.gain, criterion_data['gain'])
        self.assertEqual(result.linear_segments, criterion_data['linear_segments'])

    @parameterized.expand([
        ("delete all", [], []),
        ("delete none",
         ['alternative_A', 'alternative_B', 'alternative_C', 'alternative_D'],
         ['alternative_A', 'alternative_B', 'alternative_C', 'alternative_D']),
        ("delete alternative_A",
         ['alternative_B', 'alternative_C', 'alternative_D'],
         ['alternative_B', 'alternative_C', 'alternative_D'])
    ])
    def test_delete_alternatives(self, name, alternatives_names, expected_result):
        alternatives_data = [{'id': getattr(self, name).id} for name in alternatives_names]
        expected_result = [getattr(self, name) for name in expected_result]

        BatchOperations.delete_alternatives(self.project, alternatives_data)
        self.assertQuerySetEqual(self.project.alternatives.all(), expected_result)

    @parameterized.expand([
        ("insert new alternative", {'name': 'new_E'}, '', True),
        ("update existing alternative", {'name': 'updated_A'}, 'alternative_A', False)
    ])
    def test_insert_update_alternative(self, name, alternative_data, alternative_name, expect_insert):
        if not expect_insert:
            alternative_data['id'] = getattr(self, alternative_name).id
        result = BatchOperations.insert_update_alternative(self.project, alternative_data)
        if expect_insert:
            self.assertNotIn(result.id, self.alternatives)
        else:
            self.assertEqual(result.id, getattr(self, alternative_name).id)
        self.assertEqual(result.name, alternative_data['name'])

    @parameterized.expand([
        ("delete all", [], []),
        ("delete none",
         ['performance_A_g1', 'performance_A_g2', 'performance_A_c1'],
         ['performance_A_g1', 'performance_A_g2', 'performance_A_c1']),
    ])
    def test_delete_performances(self, name, performances_names, expected_result):
        performances_data = [{'id': getattr(self, name).id} for name in performances_names]
        expected_result = [getattr(self, name) for name in expected_result]

        BatchOperations.delete_performances(self.alternative_A, performances_data)
        self.assertQuerySetEqual(self.alternative_A.performances.all(), expected_result)
