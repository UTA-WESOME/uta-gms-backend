import _io
import csv
from lxml import etree
from typing import List, Dict
from xmcda.criteria import Criteria
from xmcda.XMCDA import XMCDA


class Parser:

    @staticmethod
    def get_criterion_dict_csv(csv_file: _io.TextIOWrapper) -> Dict[str, bool]:
        """
        Method responsible for getting dictionary of criteria

        :param csv_file: CSV file

        :return: Dictionary of criteria and their scales ex. {'g1': True, 'c2': False, 'g3': True}
        """
        csv_reader = csv.reader(csv_file, delimiter=';')

        gains: List[str] = next(csv_reader)[1:]
        criteria_ids: List[str] = next(csv_reader)[1:]

        criterion_dict = {}
        for i in range(len(criteria_ids)):
            criterion_dict[criteria_ids[i]] = True if gains[i].lower() == 'gain' else False

        return criterion_dict

    @staticmethod
    def get_performance_table_dict_csv(csv_file: _io.TextIOWrapper) -> Dict[str, Dict[str, float]]:
        """
        Method responsible for getting dict of performances from CSV file

        :param csv_file: CSV file

        :return: Dictionary of performances
        """
        csv_reader = csv.reader(csv_file, delimiter=';')
        gains: List[str] = next(csv_reader)[1:]  # skip gains row
        criteria_ids: List[str] = next(csv_reader)[1:]

        performance_table_list: List[List[float]] = []
        alternative_ids: List[str] = []
        for row in csv_reader:
            performance_list: List[float] = [float(value) for value in row[1:]]
            alternative_id: str = [value for value in row[:1]][0]

            performance_table_list.append(performance_list)
            alternative_ids.append(alternative_id)

        result = {}
        for i in range(len(alternative_ids)):
            result[alternative_ids[i]] = {criteria_ids[j]: performance_table_list[i][j] for j in
                                          range(len(criteria_ids))}

        return result

    @staticmethod
    def get_criterion_dict_xmcda(xmcda_file: _io.TextIOWrapper) -> Dict[str, List[str]]:
        """
        Method responsible for getting dictionary of criteria

        :param xmcda_file: XMCDA file

        :return: Dictionary of criteria, their names and scales ex. {'id1': ['g1', 'max'], 'id2': ['c2', 'min']}
        """
        xmcda: XMCDA = XMCDA()
        xmcda_data: XMCDA = xmcda.load(xmcda_file)
        criterion_dict = {}
        for criterion in xmcda_data.criteria:
            criterion_dict[criterion.id] = [criterion.name, 'max' if criterion.id[0] == 'g' else 'min']
        return criterion_dict

    @staticmethod
    def get_criterion_scales_dict_xmcda(xmcda_file: _io.TextIOWrapper) -> Dict[str, str]:
        """
        Method responsible for getting dictionary of criteria scales

        :param xmcda_file: XMCDA file

        :return: Dictionary of ids and scales of criteria ex. {'id1': 'max','id2': 'min','id3': 'max'}
        """
        xmcda_data = xmcda_file.read()
        root = etree.fromstring(xmcda_data)
        ns = {'xmcda': 'http://www.decision-deck.org/2021/XMCDA-4.0.0'}
        xpath = "//xmcda:criteriaScales/xmcda:criterionScales"

        criterion_scales_dict = {}
        for criterion_scales in root.xpath(xpath, namespaces=ns):
            criterion_id = criterion_scales.find("xmcda:criterionID", namespaces=ns).text
            preference_direction = criterion_scales.find(".//xmcda:preferenceDirection", namespaces=ns).text
            criterion_scales_dict[criterion_id] = preference_direction

        return criterion_scales_dict

    @staticmethod
    def get_criterion_segments_dict_xmcda(xmcda_file: _io.TextIOWrapper) -> Dict[str, int]:
        """
        Method responsible for getting dictionary of criteria linear segments

        :param xmcda_file: XMCDA file

        :return: Dictionary of ids and number of linear segments ex. {'id1': 2,'id2': 1,'id3': 1}
        """
        xmcda_data = xmcda_file.read()
        root = etree.fromstring(xmcda_data)
        ns = {'xmcda': 'http://www.decision-deck.org/2021/XMCDA-4.0.0'}
        xpath = "//xmcda:criteriaValues/xmcda:criterionValues"

        criterion_values_dict = {}
        for criterion_values in root.xpath(xpath, namespaces=ns):
            criterion_id = criterion_values.find("xmcda:criterionID", namespaces=ns).text
            linear_segments = criterion_values.find(".//xmcda:integer", namespaces=ns).text
            criterion_values_dict[criterion_id] = linear_segments

        return criterion_values_dict

    @staticmethod
    def get_alternative_dict_xmcda(xmcda_file: _io.TextIOWrapper) -> Dict[str, str]:
        """
        Method responsible for getting dictionary of alternatives

        :param xmcda_file: XMCDA file

        :return: Dictionary of alternatives ex. {'id1': 'Alternative1', 'id2': 'Alternative2', 'id3': 'Alternative3'}
        """
        xmcda: XMCDA = XMCDA()
        xmcda_data: XMCDA = xmcda.load(xmcda_file)
        alternatives = {}
        for alternative in xmcda_data.alternatives:
            alternatives[alternative.id] = alternative.name

        return alternatives

    @staticmethod
    def get_alternative_ranking_dict_xmcda(xmcda_file: _io.TextIOWrapper) -> Dict[str, int]:
        """
        Method responsible for getting dictionary of alternatives ranking

        :param xmcda_file: XMCDA file

        :return: Dictionary of ids and position in ranking of alternatives ex. ['id1': 1,'id2': 2,'id3': 1]
        """
        xmcda_data = xmcda_file.read()
        root = etree.fromstring(xmcda_data)
        ns = {'xmcda': 'http://www.decision-deck.org/2021/XMCDA-4.0.0'}
        xpath = "//xmcda:alternativesValues/xmcda:alternativeValues"

        alternative_ranking_dict = {}
        for alternative_values in root.xpath(xpath, namespaces=ns):
            alternative_id = alternative_values.find("xmcda:alternativeID", namespaces=ns).text
            rank = alternative_values.find(".//xmcda:integer", namespaces=ns).text
            alternative_ranking_dict[alternative_id] = int(rank)

        return alternative_ranking_dict

    @staticmethod
    def get_performance_table_dict_xmcda(xmcda_file: _io.TextIOWrapper) -> Dict[str, Dict[str, float]]:
        """
        Method responsible for getting dictionary representing performance table

        :param xmcda_file: XMCDA file

        :return: Dictionary representing performance table
            ex. {'id1': {'g1': 31.6, 'g2': 6.6, 'c3': 7.2}, 'id2': {'g1': 1.5, 'g2': 14.2, 'c3': 10.0}
        """
        xmcda: XMCDA = XMCDA()
        xmcda_data: XMCDA = xmcda.load(xmcda_file)
        performance_table_dict = {}
        for alternative in xmcda_data.alternatives:
            performance_list = {}
            for criterion in xmcda_data.criteria:
                performance_list[criterion.id] = xmcda_data.performance_tables[0][alternative][criterion]
            performance_table_dict[alternative.id] = performance_list

        return performance_table_dict
