import _io
from lxml import etree
from typing import Dict


class Parser:
    @staticmethod
    def get_criterion_scales_dict_xmcda(xmcda_file: _io.TextIOWrapper) -> Dict[str, str]:
        """
        Method responsible for getting dictionary of criteria scales

        :param xmcda_file: XMCDA file

        :return: Dictionary of ids and scales of criteria ex. ['id1': 'max','id2': 'min','id3': 'max']
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

        :return: Dictionary of ids and number of linear segments ex. ['id1': 2,'id2': 1,'id3': 1]
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
