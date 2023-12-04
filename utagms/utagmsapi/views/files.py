import _io
from io import BytesIO
import csv
import re
from builtins import Exception
import zipfile
from lxml import etree

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

from ..utils.parser import Parser as BackendParser


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
                except Exception:
                    return Response({'message': 'Incorrect file: {}'.format(uploaded_file.name)},
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
                third_line = uploaded_file_text.readline()

                match_second = re.search(r"<([^>\s]+)", second_line)
                match_third = re.search(r"<([^>\s]+)", third_line)
                if match_second and "xmcda" not in second_line:
                    uploaded_file_text.seek(0)
                    ordered_files_dict[match_second.group(1)] = uploaded_file_text
                if match_third:
                    uploaded_file_text.seek(0)
                    ordered_files_dict[match_third.group(1)] = uploaded_file_text

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

        # criteria scales
        criteria_scales_dict = {}
        if "criteriaScales" in ordered_files_dict:
            xml_file = ordered_files_dict["criteriaScales"]
            try:
                criteria_scales_dict = BackendParser.get_criterion_scales_dict_xmcda(xml_file)
            except Exception:
                return Response({'message': 'Incorrect file: {}'.format(xml_file.name)},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # criteria segments
        criteria_segments_dict = {}
        if "criteriaValues" in ordered_files_dict:
            xml_file = ordered_files_dict["criteriaValues"]
            try:
                criteria_segments_dict = BackendParser.get_criterion_segments_dict_xmcda(xml_file)
            except Exception:
                return Response({'message': 'Incorrect file: {}'.format(xml_file.name)},
                                status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # criteria
        xml_file = ordered_files_dict["criteria"]
        try:
            parser = Parser()
            criterion_dict = parser.get_criterion_dict_xmcda(xml_file)
        except Exception:
            return Response({'message': 'Incorrect file: {}'.format(xml_file.name)},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        for criterion in criterion_dict.items():
            gain = criteria_scales_dict.get(criterion[0], 'max' if criterion[1].gain == 1 else 'min')
            criterion_data = {
                'name': criterion[1].criterion_id,
                'gain': 1 if gain == 'max' else 0,
                'linear_segments': criteria_segments_dict.get(criterion[0], 0)
            }

            criterion_serializer = CriterionSerializer(data=criterion_data)
            if criterion_serializer.is_valid():
                criterion_serializer.save(project=project)

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

        # criterion to category
        for criterion in Criterion.objects.filter(project=project):
            cc_serializer = CriterionCategorySerializer(data={
                'criterion': criterion.id
            })
            if cc_serializer.is_valid():
                cc_serializer.save(category=category)

        # alternatives
        if "alternatives" not in ordered_files_dict:
            return Response({'message': 'Files uploaded successfully'})

        xml_file = ordered_files_dict["alternatives"]
        try:
            parser = Parser()
            alternative_dict = parser.get_alternative_dict_xmcda(xml_file)
        except Exception:
            return Response({'message': 'Incorrect file: {}'.format(xml_file.name)},
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

        # rankings
        xml_file = ordered_files_dict["alternativesValues"]
        try:
            alternative_ranking_dict = BackendParser.get_alternative_ranking_dict_xmcda(xml_file)
        except Exception:
            return Response({'message': 'Incorrect file: {}'.format(xml_file.name)},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        alternatives = Alternative.objects.all().filter(project=project)
        for alternative in alternative_dict.items():
            ranking_serializer = RankingSerializer(data={
                'reference_ranking': alternative_ranking_dict.get(alternative[0], 0),
                'ranking': 0,
                'ranking_value': 0,
                'alternative': alternatives.get(name=alternative[1]).id
            })
            if ranking_serializer.is_valid():
                ranking_serializer.save(category=category)

        # performance table
        if "performanceTable" in ordered_files_dict:
            xml_file = ordered_files_dict["performanceTable"]
            try:
                parser = Parser()
                performance_table_dict = parser.get_performance_table_dict_xmcda(xml_file)
            except Exception:
                return Response({'message': 'Incorrect file: {}'.format(xml_file.name)},
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


class XmlExport(APIView):
    permission_classes = [IsOwnerOfProject]

    def get(self, request, *args, **kwargs):
        project_id = self.kwargs.get("project_pk")
        xml_files = ["criteria.xml", "criteria_scales.xml", "criteria_segments.xml",
                     "alternatives.xml", "performance_table.xml"]
        xml_trees = []

        # criteria.xml
        root = etree.Element("xmcda", xmlns="http://www.decision-deck.org/2021/XMCDA-4.0.0")
        criteria = Criterion.objects.filter(project=project_id)
        criteria_element = etree.SubElement(root, "criteria")
        for criterion in criteria:
            criterion_element = etree.SubElement(criteria_element, "criterion", id=str(criterion.id),
                                                 name=criterion.name)
            active = etree.SubElement(criterion_element, "active")
            active.text = "true"
        xml_trees.append(etree.ElementTree(root))

        # criteria_scales.xml
        root = etree.Element("xmcda", xmlns="http://www.decision-deck.org/2021/XMCDA-4.0.0")
        criteria_scales_element = etree.SubElement(root, "criteriaScales")
        for criterion in criteria:
            criterion_scales_element = etree.SubElement(criteria_scales_element, "criterionScales")
            criterion_id_element = etree.SubElement(criterion_scales_element, "criterionID")
            criterion_id_element.text = str(criterion.id)

            scales_element = etree.SubElement(criterion_scales_element, "scales")
            scale_element = etree.SubElement(scales_element, "scale")
            quantitative_element = etree.SubElement(scale_element, "quantitative")
            preference_direction_element = etree.SubElement(quantitative_element, "preferenceDirection")
            preference_direction_element.text = "max" if criterion.gain else "min"
        xml_trees.append(etree.ElementTree(root))

        # criteria_segments.xml
        root = etree.Element("xmcda", xmlns="http://www.decision-deck.org/2021/XMCDA-4.0.0")
        criteria_values_element = etree.SubElement(root, "criteriaValues")
        for criterion in criteria:
            criterion_values_element = etree.SubElement(criteria_values_element, "criterionValues")
            criterion_id_element = etree.SubElement(criterion_values_element, "criterionID")
            criterion_id_element.text = str(criterion.id)

            values_element = etree.SubElement(criterion_values_element, "values")
            value_element = etree.SubElement(values_element, "value")
            integer_element = etree.SubElement(value_element, "integer")
            integer_element.text = str(criterion.linear_segments)
        xml_trees.append(etree.ElementTree(root))

        # alternatives.xml
        root = etree.Element("xmcda", xmlns="http://www.decision-deck.org/2021/XMCDA-4.0.0")
        alternatives = Alternative.objects.filter(project=project_id)
        alternatives_element = etree.SubElement(root, "alternatives")
        for alternative in alternatives:
            alternative_element = etree.SubElement(alternatives_element, "alternative", id=str(alternative.id),
                                                   name=alternative.name)
            type_ = etree.SubElement(alternative_element, "type")
            type_.text = "real"
            active = etree.SubElement(alternative_element, "active")
            active.text = "true"
        xml_trees.append(etree.ElementTree(root))

        # performanceTable.xml
        root = etree.Element("xmcda", xmlns="http://www.decision-deck.org/2021/XMCDA-4.0.0")
        performances_element = etree.SubElement(root, "performanceTable", mcdaConcept="REAL")

        for alternative in alternatives:
            alternative_performances_element = etree.SubElement(performances_element, "alternativePerformances")
            alternative_id_element = etree.SubElement(alternative_performances_element, "alternativeID")
            alternative_id_element.text = str(alternative.id)
            for criterion in criteria:
                performance = Performance.objects.filter(alternative=alternative, criterion=criterion).first()
                performance_element = etree.SubElement(alternative_performances_element, "performance")
                criterion_id_element = etree.SubElement(performance_element, "criterionID")
                criterion_id_element.text = str(criterion.id)

                values_element = etree.SubElement(performance_element, "values")
                value_element = etree.SubElement(values_element, "value")
                real_element = etree.SubElement(value_element, "real")
                real_element.text = str(performance.value)
        xml_trees.append(etree.ElementTree(root))

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for name, tree in zip(xml_files, xml_trees):
                xml_content = etree.tostring(tree, pretty_print=True, xml_declaration=True, encoding="UTF-8")
                zip_file.writestr(name, xml_content)

        response = HttpResponse(zip_buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="data.zip"'

        return response
