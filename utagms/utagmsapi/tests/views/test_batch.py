from django.test import TestCase
from parameterized import parameterized

from utagmsapi.models import Criterion, Project, User
from utagmsapi.views.batch import BatchOperations


class BatchOperationsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@test.com", password="test", name="test", surname="test")
        self.project = Project.objects.create(name="Test Project", shareable=False, pairwise_mode=False, user=self.user)
        self.criterion_g1 = Criterion.objects.create(name='g1', gain=True, linear_segments=1, project=self.project)
        self.criterion_g2 = Criterion.objects.create(name='g2', gain=True, linear_segments=1, project=self.project)
        self.criterion_c1 = Criterion.objects.create(name='c1', gain=True, linear_segments=1, project=self.project)

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
            self.assertNotIn(result.id, [self.criterion_g1.id, self.criterion_g2.id, self.criterion_c1.id])
            self.assertEqual(result.name, criterion_data['name'])
            self.assertEqual(result.gain, criterion_data['gain'])
            self.assertEqual(result.linear_segments, criterion_data['linear_segments'])
        else:
            self.assertEqual(result.id, getattr(self, criterion_name).id)
            self.assertEqual(result.name, criterion_data['name'])
            self.assertEqual(result.gain, criterion_data['gain'])
            self.assertEqual(result.linear_segments, criterion_data['linear_segments'])
