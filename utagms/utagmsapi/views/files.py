import _io
import csv
import re
from builtins import Exception

from django.db import transaction
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from utagmsengine.parser import Parser

from ..models import (
    Project,
    Criterion,
    Alternative,
    Performance,
    Category
)
from ..permissions import (
    IsOwnerOfProject
)
from ..serializers import (
    CriterionSerializer,
    AlternativeSerializer,
    PerformanceSerializer,
    CategorySerializer,
    CriterionCategorySerializer,
    RankingSerializer
)


# FileUpload
class FileUpload(APIView):
    permission_classes = [IsOwnerOfProject]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        uploaded_files = request.FILES.getlist('file')

        project_id = kwargs.get('project_pk')
        project = Project.objects.filter(id=project_id).first()
        if not uploaded_files:
            return Response({'message': 'No files selected or invalid request'}, status=status.HTTP_400_BAD_REQUEST)

        ordered_files_dict = {}
        for uploaded_file in uploaded_files:
            if len(uploaded_file.name) < 5:
                return Response({'message': 'Incorrect file name'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            if uploaded_file.name[-4:] == '.csv':
                uploaded_file_text = _io.TextIOWrapper(uploaded_file, encoding='utf-8')

                # deleting previous data
                curr_alternatives = Alternative.objects.filter(project=project)
                curr_criteria = Criterion.objects.filter(project=project)
                curr_categories = Category.objects.filter(project=project)
                curr_alternatives.delete()
                curr_criteria.delete()
                curr_categories.delete()

                try:
                    parser = Parser()
                    criterion_list = parser.get_criterion_list_csv(uploaded_file_text)
                    uploaded_file_text.seek(0)
                    performance_table_list = parser.get_performance_table_dict_csv(uploaded_file_text)
                except Exception as e:
                    return Response({'message': 'Incorrect file: {}'.format(str(e))},
                                    status=status.HTTP_422_UNPROCESSABLE_ENTITY)

                # criteria
                for criterion in criterion_list:
                    criterion_data = {
                        'name': criterion.criterion_id,
                        'gain': criterion.gain,
                        'linear_segments': 0,
                    }

                    criterion_serializer = CriterionSerializer(data=criterion_data)
                    if criterion_serializer.is_valid():
                        criterion_serializer.save(project=project)

                # alternatives
                for alternative in performance_table_list.keys():
                    alternative_data = {
                        'name': alternative,
                        'reference_ranking': 0,
                        'ranking': 0,
                        'ranking_value': 0,
                    }

                    alternative_serializer = AlternativeSerializer(data=alternative_data)
                    if alternative_serializer.is_valid():
                        alternative_serializer.save(project=project)

                # performances
                criteria = Criterion.objects.all().filter(project=project)
                alternatives = Alternative.objects.all().filter(project=project)
                for alternative_name, alternative_data in performance_table_list.items():
                    alternative = alternatives.get(name=alternative_name)
                    for criterion_name, value in alternative_data.items():
                        criterion = criteria.get(name=criterion_name)
                        performance_data = {
                            'criterion': criterion.pk,
                            'value': value,
                            'ranking': 0,
                        }
                        performance_serializer = PerformanceSerializer(data=performance_data)
                        if performance_serializer.is_valid():
                            performance_serializer.save(alternative=alternative)

                # categories
                category = None
                root_category_serializer = CategorySerializer(data={
                    'name': 'General',
                    'color': 'teal.500',
                    'active': True,
                    'hasse_diagram': {},
                    'parent': None
                })
                if root_category_serializer.is_valid():
                    category = root_category_serializer.save(project=project)

                # rankings
                for alternative in Alternative.objects.filter(project=project):
                    ranking_serializer = RankingSerializer(data={
                        'reference_ranking': 0,
                        'ranking': 0,
                        'ranking_value': 0,
                        'alternative': alternative.id
                    })
                    if ranking_serializer.is_valid():
                        ranking_serializer.save(category=category)

                # criterion to category
                for criterion in Criterion.objects.filter(project=project):
                    cc_serializer = CriterionCategorySerializer(data={
                        'criterion': criterion.id
                    })
                    if cc_serializer.is_valid():
                        cc_serializer.save(category=category)

                return Response({'message': 'File uploaded successfully'})
            elif uploaded_file.name[-4:] == '.xml':
                uploaded_file_text = _io.TextIOWrapper(uploaded_file, encoding='utf-8')

                _ = uploaded_file_text.readline()
                second_line = uploaded_file_text.readline()

                match = re.search(r"<([^>\s]+)", second_line)
                if match:
                    uploaded_file_text.seek(0)
                    ordered_files_dict[match.group(1)] = uploaded_file_text

        # make sure we don't import wrong combination of files
        if "criteria" not in ordered_files_dict or (
                "alternatives" not in ordered_files_dict and "performanceTable" in ordered_files_dict):
            return Response({'message': 'Wrong files configuration'}, status=status.HTTP_400_BAD_REQUEST)

        curr_alternatives = Alternative.objects.filter(project=project)
        curr_criteria = Criterion.objects.filter(project=project)
        curr_categories = Category.objects.filter(project=project)
        curr_alternatives.delete()
        curr_criteria.delete()
        curr_categories.delete()

        # criteria
        xml_file = ordered_files_dict["criteria"]
        try:
            parser = Parser()
            criterion_dict = parser.get_criterion_dict_xmcda(xml_file)
        except Exception as e:
            return Response({'message': 'Incorrect file: {}'.format(str(e))},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        for criterion in criterion_dict.values():
            criterion_data = {
                'name': criterion.criterion_id,
                'gain': criterion.gain,
                'linear_segments': 0,
            }

            criterion_serializer = CriterionSerializer(data=criterion_data)
            if criterion_serializer.is_valid():
                criterion_serializer.save(project=project)

        # alternatives
        if "alternatives" not in ordered_files_dict:
            return Response({'message': 'Files uploaded successfully'})

        xml_file = ordered_files_dict["alternatives"]
        try:
            parser = Parser()
            alternative_dict = parser.get_alternative_dict_xmcda(xml_file)
        except Exception as e:
            return Response({'message': 'Incorrect file: {}'.format(str(e))},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        for alternative in alternative_dict.values():
            alternative_data = {
                'name': alternative,
                'reference_ranking': 0,
                'ranking': 0,
                'ranking_value': 0,
            }

            alternative_serializer = AlternativeSerializer(data=alternative_data)
            if alternative_serializer.is_valid():
                alternative_serializer.save(project=project)

        # performance table
        if "performanceTable" in ordered_files_dict:
            xml_file = ordered_files_dict["performanceTable"]
            try:
                parser = Parser()
                performance_table_dict = parser.get_performance_table_dict_xmcda(xml_file)
            except Exception as e:
                return Response({'message': 'Incorrect file: {}'.format(str(e))},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            criteria = Criterion.objects.all().filter(project=project)
            alternatives = Alternative.objects.all().filter(project=project)
            for alternative_id, alternative_data in performance_table_dict.items():
                alternative = alternatives.get(name=alternative_dict.get(alternative_id))

                for criterion_id, value in alternative_data.items():
                    criterion = criteria.get(name=criterion_dict.get(criterion_id).criterion_id)
                    performance_data = {
                        'criterion': criterion.pk,
                        'value': value,
                    }
                    performance_serializer = PerformanceSerializer(data=performance_data)
                    if performance_serializer.is_valid():
                        performance_serializer.save(alternative=alternative)

        else:
            criteria = Criterion.objects.all().filter(project=project)
            alternatives = Alternative.objects.all().filter(project=project)
            for alternative_name in alternative_dict.values():
                alternative = alternatives.get(name=alternative_name)

                for criterion_element in criterion_dict.values():
                    criterion = criteria.get(name=criterion_element.criterion_id)
                    performance_data = {
                        'criterion': criterion.pk,
                        'value': 0,
                        'ranking': 0,
                    }
                    performance_serializer = PerformanceSerializer(data=performance_data)
                    if performance_serializer.is_valid():
                        performance_serializer.save(alternative=alternative)

        # categories
        category = None
        root_category_serializer = CategorySerializer(data={
            'name': 'General',
            'color': 'teal.500',
            'active': True,
            'hasse_diagram': {},
            'parent': None
        })
        if root_category_serializer.is_valid():
            category = root_category_serializer.save(project=project)

        # rankings
        for alternative in Alternative.objects.filter(project=project):
            ranking_serializer = RankingSerializer(data={
                'reference_ranking': 0,
                'ranking': 0,
                'ranking_value': 0,
                'alternative': alternative.id
            })
            if ranking_serializer.is_valid():
                ranking_serializer.save(category=category)

        # criterion to category
        for criterion in Criterion.objects.filter(project=project):
            cc_serializer = CriterionCategorySerializer(data={
                'criterion': criterion.id
            })
            if cc_serializer.is_valid():
                cc_serializer.save(category=category)

        return Response({'message': 'Files uploaded successfully'})


class CsvExport(APIView):
    permission_classes = [IsOwnerOfProject]

    def get(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_pk")
        response = HttpResponse(content_type='text/csv')

        writer = csv.writer(response, delimiter=';')

        alternatives = Alternative.objects.filter(project=project_id)
        criteria = Criterion.objects.filter(project=project_id)

        first_row = ['']
        second_row = ['']
        for criterion in criteria:
            first_row.append('gain' if criterion.gain else 'cost')
            second_row.append(criterion.name)

        if first_row != ['']:
            writer.writerow(first_row)
        if second_row != ['']:
            writer.writerow(second_row)

        for alternative in alternatives:
            row = [alternative.name]
            for criterion in criteria:
                performance = Performance.objects.filter(alternative=alternative, criterion=criterion).first()
                row.append(performance.value)
            writer.writerow(row)

        response['Content-Disposition'] = 'attachment; filename="data.csv"'
        return response
