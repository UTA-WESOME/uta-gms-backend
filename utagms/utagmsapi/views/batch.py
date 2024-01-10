from typing import Any, Dict, List, Tuple, Union

import utagmsengine.dataclasses as uged
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from utagmsengine.solver import Inconsistency as InconsistencyException, Solver

from ..models import (
    AcceptabilityIndex,
    Alternative,
    Category,
    Criterion,
    CriterionCategory,
    FunctionPoint,
    Inconsistency,
    PairwiseComparison,
    PairwiseWinning,
    Performance,
    PreferenceIntensity,
    Project,
    Ranking,
    Relation
)
from ..permissions import IsOwnerOfCategory, IsOwnerOfProject
from ..serializers import (
    AcceptabilityIndexSerializer,
    AlternativeSerializer,
    CategorySerializer,
    CriterionCategorySerializer,
    CriterionSerializer,
    FunctionPointSerializer,
    InconsistencySerializer,
    PairwiseComparisonSerializer,
    PairwiseWinningSerializer,
    PerformanceSerializer,
    PerformanceSerializerUpdate,
    PreferenceIntensitySerializer,
    ProjectSerializerWhole,
    RankingSerializer,
    RelationSerializer
)
from ..utils.recursive_queries import RecursiveQueries


class BatchOperations:
    """
    A utility class for batch operations on various entities in a project.

    This class provides static methods for performing batch operations, such as deletion and insertion/updation,
    on different entities within a project.

    Methods
    -------
    delete_criteria(project: Project, criteria_data: List[Dict[str, Union[str, int]]]) -> None:
        Delete criteria from the project based on the provided criteria data.

    insert_update_criterion(project: Project, criterion_data: Dict[str, Union[str, int]]) -> Union[Criterion, None]:
        Insert or update a criterion within a project based on the provided criterion data.

    delete_alternatives(project: Project, alternatives_data: List[Dict[str, Union[str, int, List[Dict[str, Union[str, int]]]]]]) -> None:
        Delete alternatives from the project based on the provided alternatives data.

    insert_update_alternative(project: Project, alternative_data: Dict[str, Union[str, int, List[Dict[str, Union[str, int]]]]]) -> None:
        Insert or update alternatives within a project based on the provided alternative data.

    delete_performances(alternative: Alternative, performances_data: List[Dict[str, Union[float, str]]]) -> None:
        Delete performances associated with an alternative based on the provided performances data.

    insert_update_performance(alternative: Alternative, performance_data: Dict[str, Union[float, str]]) -> Union[Performance, None]:
        Insert or update a performance associated with an alternative based on the provided performance data.

    delete_categories(project: Project, categories_data: List[Dict[str, Any]]) -> None:
        Delete categories from the project based on the provided categories data.

    insert_update_category(project: Project, category_data: Dict[str, Any]) -> Union[Category, None]:
        Insert or update a category within a project based on the provided category data.

    delete_criterion_categories(category: Category, ccs_data: List[Dict[str, int]]) -> None:
        Delete criterion categories associated with a category based on the provided criterion category data.

    insert_update_criterion_categories(category: Category, cc_data: Dict[str, int]) -> Union[CriterionCategory, None]:
        Insert or update a criterion category associated with a category based on the provided criterion category data.

    delete_pairwise_comparisons(category: Category, pairwise_comparisons_data: List[Dict[str, Union[str, int]]]) -> None:
        Delete pairwise comparisons associated with a category based on the provided pairwise comparisons data.

    insert_update_pairwise_comparison(category: Category, pairwise_comparison_data: Dict[str, Union[str, int]]) -> Union[PairwiseComparison, None]:
        Insert or update a pairwise comparison associated with a category based on the provided pairwise comparison data.

    delete_rankings(category: Category, rankings_data: List[Dict[str, Union[str, int, float]]]) -> None:
        Delete rankings associated with a category based on the provided rankings data.

    insert_update_ranking(category: Category, ranking_data: Dict[str, Union[str, int, float]]) -> Union[Ranking, None]:
        Insert or update a ranking associated with a category based on the provided ranking data.

    delete_preference_intensities(project: Project, preference_intensities_data: List[Dict[str, Union[str, int]]]) -> None:
        Delete preference intensities associated with a project based on the provided preference intensity data.

    insert_update_preference_intensity(project: Project, preference_intensity_data: Dict[str, Union[str, int]]) -> Union[PreferenceIntensity, None]:
        Insert or update a preference intensity associated with a project based on the provided preference intensity data.
    """

    @staticmethod
    def delete_criteria(project: Project, criteria_data: List[Dict[str, Union[str, int]]]) -> None:
        """
        Delete criteria from the project based on the provided criteria data.

        Parameters
        ----------
        project: Project
         The project instance from which criteria will be deleted.
        criteria_data: List[Dict[str, Union[str, int]]]
         A list of dictionaries representing criteria data.
         Each dictionary representing a single Criterion should have an 'id' key.

        Notes
        -----
        This method compares the 'id' values in the provided criteria_data with the 'id' values of the existing
        criteria in the project. Criteria with 'id' values in the project that are not present in criteria_data
        will be deleted.
        """
        criteria_ids_db = project.criteria.values_list('id', flat=True)
        criteria_ids_request = [criterion_data.get('id') for criterion_data in criteria_data]
        criteria_ids_to_delete = set(criteria_ids_db) - set(criteria_ids_request)
        project.criteria.filter(id__in=criteria_ids_to_delete).delete()

    @staticmethod
    def insert_update_criterion(project: Project, criterion_data: Dict[str, Union[str, int]]) -> Union[Criterion, None]:
        """
        Insert or update a criterion in the project based on the provided criterion data.

        Parameters
        ----------
        project : Project
            The project instance where the criterion will be inserted or updated.
        criterion_data : Dict[str, Union[str, int]]
            A dictionary representing the criterion data.
            It should contain information about the criterion including an 'id' key.

        Returns
        -------
        Criterion
            The inserted or updated criterion instance if the serialization is successful, otherwise returns None.

        Notes
        -----
        This method first attempts to retrieve an existing criterion based on the provided 'id'. If the criterion
        exists, it updates the criterion's data using the provided criterion_data. If the criterion does not exist,
        it creates a new criterion with the provided data.
        """
        criterion_id = criterion_data.get('id')

        try:
            criterion = project.criteria.get(id=criterion_id)
            criterion_serializer = CriterionSerializer(criterion, data=criterion_data)
        except Criterion.DoesNotExist:
            criterion_serializer = CriterionSerializer(data=criterion_data)

        if criterion_serializer.is_valid():
            return criterion_serializer.save(project=project)

    @staticmethod
    def delete_alternatives(
            project: Project,
            alternatives_data: List[Dict[str, Union[str, int, List[Dict[str, Union[str, float]]]]]]
    ) -> None:
        """
        Delete alternatives from the project based on the provided alternatives data.

        Parameters
        ----------
        project : Project
            The project instance from which alternatives will be deleted.
        alternatives_data : List[Dict[str, Union[str, int, List[Dict[str, Union[str, int]]]]]]
            A list of dictionaries representing alternatives data.
            Each dictionary representing a single alternative should have an 'id' key.

        Notes
        -----
        This method compares the 'id' values in the provided alternatives_data with the 'id' values of the existing
        alternatives in the project. Alternatives with 'id' values in the project that are not present in
        alternatives_data will be deleted.
        """
        alternatives_ids_db = project.alternatives.values_list('id', flat=True)
        alternatives_ids_request = [alternative_data.get('id') for alternative_data in alternatives_data]
        alternatives_ids_to_delete = set(alternatives_ids_db) - set(alternatives_ids_request)
        project.alternatives.filter(id__in=alternatives_ids_to_delete).delete()

    @staticmethod
    def insert_update_alternative(
            project: Project,
            alternative_data: Dict[str, Union[str, int, List[Dict[str, Union[str, float]]]]]
    ) -> Union[Criterion, None]:
        """
        Insert or update an alternative in the project based on the provided alternative data.

        Parameters
        ----------
        project : Project
            The project instance where the alternative will be inserted or updated.
        alternative_data : Dict[str, Union[str, int, List[Dict[str, Union[str, int]]]]]
            A dictionary representing the alternative data.
            It should contain information about the alternative, including an 'id' key.

        Returns
        -------
        Alternative
            The inserted or updated alternative instance if the serialization is successful, otherwise returns None.

        Notes
        -----
        This method first attempts to retrieve an existing alternative based on the provided 'id'. If the alternative
        exists, it updates the alternative's data using the provided alternative_data.
        If the alternative does not exist, it creates a new alternative with the provided data.
        """
        alternative_id = alternative_data.get('id')

        try:
            alternative = project.alternatives.get(id=alternative_id)
            alternative_serializer = AlternativeSerializer(alternative, data=alternative_data)
        except Alternative.DoesNotExist:
            alternative_serializer = AlternativeSerializer(data=alternative_data)

        if alternative_serializer.is_valid():
            return alternative_serializer.save(project=project)

    @staticmethod
    def delete_performances(alternative: Alternative, performances_data: List[Dict[str, Union[float, str]]]) -> None:
        """
        Delete performances associated with an alternative based on the provided performances data.

        Parameters
        ----------
        alternative : Alternative
            The alternative instance from which performances will be deleted.
        performances_data : List[Dict[str, Union[float, str]]]
            A list of dictionaries representing performances data.
            Each dictionary should contain information about a performance, including an 'id' key.

        Notes
        -----
        This method compares the 'id' values in the provided performances_data with the 'id' values of the existing
        performances associated with the alternative. Performances with 'id' values in the alternative that are not
        present in performances_data will be deleted.
        """
        performances_ids_db = alternative.performances.values_list('id', flat=True)
        performances_ids_request = [performance_data.get('id', -1) for performance_data in performances_data]
        performances_ids_to_delete = set(performances_ids_db) - set(performances_ids_request)
        alternative.performances.filter(id__in=performances_ids_to_delete).delete()

    @staticmethod
    def insert_update_performance(
            alternative: Alternative,
            performance_data: Dict[str, Union[float, str]]
    ) -> Union[Performance, None]:
        """
        Insert or update a performance associated with an alternative based on the provided performance data.

        Parameters
        ----------
        alternative : Alternative
            The alternative instance to which the performance will be associated.
        performance_data : Dict[str, Union[float, str]]
            A dictionary representing the performance data.
            It should contain information about the performance, including an 'id' key.

        Returns
        -------
        Union[Performance, None]
            Returns the inserted or updated performance instance if the serialization is successful, otherwise returns None.

        Notes
        -----
        This method first attempts to retrieve an existing performance based on the provided 'id' associated with the
        given alternative. If the performance exists, it updates the performance's data using the provided
        performance_data. If the performance does not exist, it creates a new performance with the provided data.
        """
        performance_id = performance_data.get('id')

        try:
            performance = alternative.performances.get(id=performance_id)
            performance_serializer = PerformanceSerializerUpdate(performance, data=performance_data)
        except Performance.DoesNotExist:
            performance_serializer = PerformanceSerializer(data=performance_data)

        if performance_serializer.is_valid():
            return performance_serializer.save(alternative=alternative)

    @staticmethod
    def delete_categories(project: Project, categories_data: List[Dict[str, Any]]) -> None:
        """
        Delete categories from the project based on the provided categories data.

        Parameters
        ----------
        project : Project
            The project instance from which categories will be deleted.
        categories_data : List[Dict[str, Any]]
            A list of dictionaries representing categories data. Each dictionary should have an 'id' key.

        Notes
        -----
        This method compares the 'id' values in the provided categories_data with the 'id' values of the existing
        categories in the project. Categories with 'id' values in the project that are not present in categories_data
        will be deleted.
        """
        categories_ids_db = project.categories.values_list('id', flat=True)
        categories_ids_request = [category_data.get('id') for category_data in categories_data]
        categories_ids_to_delete = set(categories_ids_db) - set(categories_ids_request)
        project.categories.filter(id__in=categories_ids_to_delete).delete()

    @staticmethod
    def insert_update_category(project, category_data: Dict[str, Any]) -> Union[Category, None]:
        """
        Insert or update a category in the project based on the provided category data.

        Parameters
        ----------
        project : Project
            The project instance where the category will be inserted or updated.
        category_data : Dict[str, Any]
            A dictionary representing the category data. It should contain information about the category,
            including an 'id' key.

        Returns
        -------
        Union[Category, None]
            Returns the inserted or updated category instance if the serialization is successful, otherwise returns None.

        Notes
        -----
        This method first attempts to retrieve an existing category based on the provided 'id'. If the category
        exists, it updates the category's data using the provided category_data. If the category does not exist,
        it creates a new category with the provided data.
        """
        category_id = category_data.get('id')

        try:
            category = project.categories.get(id=category_id)
            category_serializer = CategorySerializer(category, data=category_data)
        except Category.DoesNotExist:
            category_serializer = CategorySerializer(data=category_data)

        if category_serializer.is_valid():
            return category_serializer.save(project=project)

    @staticmethod
    def delete_criterion_categories(category: Category, ccs_data: List[Dict[str, int]]) -> None:
        """
        Delete criterion categories associated with a category based on the provided criterion category data.

        Parameters
        ----------
        category : Category
            The category instance from which criterion categories will be deleted.
        ccs_data : List[Dict[str, int]]
            A list of dictionaries representing criterion category data.
            Each dictionary should contain information about a criterion category, including an 'id' key.

        Notes
        -----
        This method compares the 'id' values in the provided ccs_data with the 'id' values of the existing criterion
        categories associated with the category. Criterion categories with 'id' values in the category that are not
        present in ccs_data will be deleted.
        """
        ccs_ids_db = category.criterion_categories.values_list('id', flat=True)
        ccs_ids_request = [cc_data.get('id') for cc_data in ccs_data]
        ccs_ids_to_delete = set(ccs_ids_db) - set(ccs_ids_request)
        category.criterion_categories.filter(id__in=ccs_ids_to_delete).delete()

    @staticmethod
    def insert_update_criterion_categories(
            category: Category,
            cc_data: Dict[str, int]
    ) -> Union[CriterionCategory, None]:
        """
        Insert or update a criterion category associated with a category based on the provided criterion category data.

        Parameters
        ----------
        category : Category
            The category instance to which the criterion category will be associated.
        cc_data : Dict[str, int]
            A dictionary representing the criterion category data. It should contain information about the criterion category,
            including an 'id' key.

        Returns
        -------
        Union[CriterionCategory, None]
            Returns the inserted or updated criterion category instance if the serialization is successful, otherwise returns None.

        Notes
        -----
        This method first attempts to retrieve an existing criterion category based on the provided 'id' associated with the
        given category. If the criterion category exists, it updates the criterion category's data using the provided
        cc_data. If the criterion category does not exist, it creates a new criterion category with the provided data.

        """
        cc_id = cc_data.get('id')
        try:
            criterion_category = category.criterion_categories.get(id=cc_id)
            cc_serializer = CriterionCategorySerializer(criterion_category, data=cc_data)
        except CriterionCategory.DoesNotExist:
            cc_serializer = CriterionCategorySerializer(data=cc_data)
        if cc_serializer.is_valid():
            return cc_serializer.save(category=category)

    @staticmethod
    def delete_pairwise_comparisons(
            category: Category,
            pairwise_comparisons_data: List[Dict[str, Union[str, int]]]
    ) -> None:
        """
        Delete pairwise comparisons associated with a category based on the provided pairwise comparisons data.

        Parameters
        ----------
        category : Category
            The category instance from which pairwise comparisons will be deleted.
        pairwise_comparisons_data : List[Dict[str, Union[str, int]]]
            A list of dictionaries representing pairwise comparisons data.
            Each dictionary should contain information about a pairwise comparison, including an 'id' key.

        Notes
        -----
        This method compares the 'id' values in the provided pairwise comparisons data with the 'id' values of the existing
        pairwise comparisons associated with the category. Pairwise comparisons with 'id' values in the category that are not
        present in pairwise comparisons data will be deleted.
        """
        pairwise_comparisons_ids_db = category.pairwise_comparisons.values_list('id', flat=True)
        pairwise_comparisons_ids_request = [pc_data.get('id') for pc_data in pairwise_comparisons_data]
        pairwise_comparisons_ids_to_delete = (set(pairwise_comparisons_ids_db) - set(pairwise_comparisons_ids_request))
        category.pairwise_comparisons.filter(id__in=pairwise_comparisons_ids_to_delete).delete()

    @staticmethod
    def insert_update_pairwise_comparison(
            category,
            pairwise_comparison_data: Dict[str, Union[str, int]]
    ) -> Union[PairwiseComparison, None]:
        """
        Insert or update a pairwise comparison associated with a category based on the provided pairwise comparison data.

        Parameters
        ----------
        category : Category
            The category instance to which the pairwise comparison will be associated.
        pairwise_comparison_data : Dict[str, Union[str, int]]
            A dictionary representing the pairwise comparison data.
            It should contain information about the pairwise comparison, including an 'id' key.

        Returns
        -------
        Union[PairwiseComparison, None]
            Returns the inserted or updated pairwise comparison instance if the serialization is successful,
            otherwise returns None.

        Notes
        -----
        This method first attempts to retrieve an existing pairwise comparison based on the provided 'id' associated with the
        given category. If the pairwise comparison exists, it updates the pairwise comparison's data using the provided
        pairwise_comparison_data. If the pairwise comparison does not exist, it creates a new pairwise comparison with
        the provided data.
        """
        pairwise_comparison_id = pairwise_comparison_data.get('id')
        try:
            pairwise_comparison = category.pairwise_comparisons.get(id=pairwise_comparison_id)
            pairwise_comparison_serializer = PairwiseComparisonSerializer(
                pairwise_comparison,
                data=pairwise_comparison_data
            )
        except PairwiseComparison.DoesNotExist:
            pairwise_comparison_serializer = PairwiseComparisonSerializer(data=pairwise_comparison_data)
        if pairwise_comparison_serializer.is_valid():
            return pairwise_comparison_serializer.save(category=category)

    @staticmethod
    def delete_rankings(category: Category, rankings_data: List[Dict[str, Union[str, int, float]]]) -> None:
        """
        Delete rankings associated with a category based on the provided rankings data.

        Parameters
        ----------
        category : Category
            The category instance from which rankings will be deleted.
        rankings_data : List[Dict[str, Union[str, int, float]]]
            A list of dictionaries representing rankings data. Each dictionary should contain information about
            a ranking, including an 'id' key.

        Notes
        -----
        This method compares the 'id' values in the provided rankings data with the 'id' values of the existing
        rankings associated with the category. Rankings with 'id' values in the category that are not present in
        rankings data will be deleted.
        """
        rankings_ids_db = category.rankings.values_list('id', flat=True)
        rankings_ids_request = [ranking_data.get('id') for ranking_data in rankings_data]
        rankings_ids_to_delete = set(rankings_ids_db) - set(rankings_ids_request)
        category.rankings.filter(id__in=rankings_ids_to_delete).delete()

    @staticmethod
    def insert_update_ranking(
            category: Category,
            ranking_data: Dict[str, Union[str, int, float]]
    ) -> Union[Ranking, None]:
        """
        Insert or update a ranking associated with a category based on the provided ranking data.

        Parameters
        ----------
        category : Category
            The category instance to which the ranking will be associated.
        ranking_data : Dict[str, Union[str, int, float]]
            A dictionary representing the ranking data. It should contain information about the ranking,
            including an 'id' key.

        Returns
        -------
        Union[Ranking, None]
            Returns the inserted or updated ranking instance if the serialization is successful, otherwise returns None.

        Notes
        -----
        This method first attempts to retrieve an existing ranking based on the provided 'id' associated with the
        given category. If the ranking exists, it updates the ranking's data using the provided ranking_data.
        If the ranking does not exist, it creates a new ranking with the provided data.
        """
        ranking_id = ranking_data.get('id')
        try:
            ranking = category.rankings.get(id=ranking_id)
            ranking_serializer = RankingSerializer(ranking, data=ranking_data)
        except Ranking.DoesNotExist:
            ranking_serializer = RankingSerializer(data=ranking_data)
        if ranking_serializer.is_valid():
            return ranking_serializer.save(category=category)

    @staticmethod
    def delete_preference_intensities(
            project: Project,
            preference_intensities_data: List[Dict[str, Union[str, int]]]
    ) -> None:
        """
        Delete preference intensities associated with a project based on the provided preference intensity data.

        Parameters
        ----------
        project : Project
            The project instance from which preference intensities will be deleted.
        preference_intensities_data : List[Dict[str, Union[str, int]]]
            A list of dictionaries representing preference intensity data. Each dictionary should contain information
            about a preference intensity, including an 'id' key.

        Notes
        -----
        This method compares the 'id' values in the provided preference intensities data with the 'id' values of the existing
        preference intensities associated with the project. Preference intensities with 'id' values in the project that are not
        present in preference intensities data will be deleted.
        """
        pref_intensities_ids_db = project.preference_intensities.values_list('id', flat=True)
        pref_intensities_ids_request = [
            pref_intensity_data.get('id') for pref_intensity_data in preference_intensities_data
        ]
        pref_intensities_ids_to_delete = set(pref_intensities_ids_db) - set(pref_intensities_ids_request)
        project.preference_intensities.filter(id__in=pref_intensities_ids_to_delete).delete()

    @staticmethod
    def insert_update_preference_intensity(
            project: Project,
            preference_intensity_data: Dict[str, Union[str, int]]
    ) -> Union[PreferenceIntensity, None]:
        """
        Insert or update a preference intensity associated with a project based on the provided preference intensity data.

        Parameters
        ----------
        project : Project
            The project instance to which the preference intensity will be associated.
        preference_intensity_data : Dict[str, Union[str, int]]
            A dictionary representing the preference intensity data.
            It should contain information about the preference intensity, including an 'id' key.

        Returns
        -------
        Union[PreferenceIntensity, None]
            Returns the inserted or updated preference intensity instance if the serialization is successful, otherwise returns None.

        Notes
        -----
        This method first attempts to retrieve an existing preference intensity based on the provided 'id' associated with the
        given project. If the preference intensity exists, it updates the preference intensity's data using the provided
        preference_intensity_data. If the preference intensity does not exist, it creates a new preference intensity with the provided data.
        """
        pref_intensity_id = preference_intensity_data.get('id')
        try:
            pref_intensity = project.preference_intensities.get(id=pref_intensity_id)
            pref_intensity_serializer = PreferenceIntensitySerializer(
                pref_intensity,
                data=preference_intensity_data
            )
        except PreferenceIntensity.DoesNotExist:
            pref_intensity_serializer = PreferenceIntensitySerializer(data=preference_intensity_data)
        if pref_intensity_serializer.is_valid():
            return pref_intensity_serializer.save(project=project)


class EngineConverter:
    """
    Utility class for converting and processing data between the UTA GMS Engine and the application's models.

    This class provides static methods for converting data from the application's models to the format expected by
    the UTA GMS Engine and vice versa. It also includes methods for inserting and updating various data types in the
    application's models based on data generated by the UTA GMS Engine.

    Static Methods:
    ---------------
    get_criteria(criteria: List[Criterion]) -> List[uged.Criterion]:
        Convert a list of application's Criteria instances to a list of uged.Criterion instances.

    get_performances(alternatives: List[Alternative], criteria: List[Criterion]) -> Dict[str, Dict[str, float]]:
        Convert performance data from the application's models to a dictionary format expected by the Uta GMS Engine.

    get_comparisons(project: Project, categories: List[Category]) -> List[uged.Comparison]:
        Convert pairwise comparison data from the application's models to a list of uged.Comparison instances.

    get_preference_intensities(
            project: Project, categories: List[Category], criteria: List[Criterion]
    ) -> List[uged.Intensity]:
        Convert preference intensity data from the application's models to a list of uged.Intensity instances.

    get_best_worst_positions(categories: List[Category]) -> List[uged.Position]:
        Convert best and worst position data from the application's models to a list of uged.Position instances.

    insert_inconsistencies_comparisons(
            category_root: Category, comparisons: List[uged.Comparison], group: int
    ) -> None:
        Insert inconsistency data for pairwise comparisons into the application's models.

    insert_inconsistencies_best_worst(
            category_root: Category, best_worsts: List[uged.Position], group: int
    ) -> None:
        Insert inconsistency data for best and worst positions into the application's models.

    insert_inconsistencies_preference_intensities(
            category_root: Category, intensities: List[uged.Intensity], group: int
    ) -> None:
        Insert inconsistency data for preference intensities into the application's models.

    insert_inconsistencies(
            category_root: Category,
            inconsistencies: Tuple[List[uged.Comparison], List[uged.Comparison], List[uged.Position], List[uged.Intensity]]
    ) -> None:
        Insert various inconsistency data into the application's models.

    insert_acceptability_indices(category_root: Category, indices: Dict[str, List[float]]) -> None:
        Insert acceptability indices into the application's models.

    insert_pairwise_winnings(category_root: Category, winnings: Dict[str, List[str]]) -> None:
        Insert pairwise winning data into the application's models.

    update_rankings(category_root: Category, ranking: Dict[str, float]) -> None:
        Update ranking data in the application's models.

    insert_criterion_functions(category_root: Category, functions: Dict[str, List[Tuple[float, float]]]) -> None:
        Insert criterion function data into the application's models.

    insert_relations(category_root: Category, relations: Dict[str, List[str]], relation_type: str) -> None:
        Insert relation data into the application's models.
    """

    @staticmethod
    def get_criteria(criteria: List[Criterion]) -> List[uged.Criterion]:
        """
        Convert a list of Django Criterion instances to a list of utagmsengine.Criterion instances.

        Parameters
        ----------
        criteria : List[Criterion]
            A list of Django Criterion instances.

        Returns
        -------
        List[uged.Criterion]
            A list of uged.Criterion instances.
        """
        return [
            uged.Criterion(criterion_id=str(c.id), number_of_linear_segments=c.linear_segments, gain=c.gain)
            for c in criteria
        ]

    @staticmethod
    def get_performances(alternatives: List[Alternative], criteria: List[Criterion]) -> Dict[str, Dict[str, float]]:
        """
        Retrieve performances for a list of alternatives and criteria.

        Parameters
        ----------
        alternatives : List[Alternative]
            A list of Django Alternative instances.
        criteria : List[Criterion]
            A list of Django Criterion instances.

        Returns
        -------
        Dict[str, Dict[str, float]]
            A dictionary representing performances for each alternative and criterion.
            The keys of the outer dictionary are alternative IDs, and the inner dictionaries
            have criterion IDs as keys and corresponding performances as values.
        """
        performances = {}
        for alternative in alternatives:
            performances[str(alternative.id)] = {
                str(criterion_id): value for criterion_id, value in
                Performance.objects
                .filter(alternative=alternative)
                .filter(criterion__in=criteria)
                .values_list('criterion', 'value')
            }
        return performances

    @staticmethod
    def get_comparisons(project: Project, categories: List[Category]) -> List[uged.Comparison]:
        """
        Retrieve comparisons for a project and a list of categories.

        Parameters
        ----------
        project : Project
            A Django Project instance.
        categories : List[Category]
            A list of Django Category instances.

        Returns
        -------
        List[uged.Comparison]
            A list of Comparison instances representing pairwise comparisons or rankings.

        Notes
        -----
        If the project is in pairwise mode, it retrieves pairwise comparisons.
        If not, it generates comparisons based on rankings within each category.
        """
        comparisons_list = []
        if project.pairwise_mode:
            for pairwise_comparison in PairwiseComparison.objects.filter(category__in=categories):
                # we have to find criteria that the pairwise comparison is related to
                criteria_for_comparison = Criterion.objects.filter(
                    id__in=RecursiveQueries.get_criteria_for_category(pairwise_comparison.category.id)
                )
                comparisons_list.append(
                    uged.Comparison(
                        alternative_1=str(pairwise_comparison.alternative_1.id),
                        alternative_2=str(pairwise_comparison.alternative_2.id),
                        criteria=[str(criterion.id) for criterion in criteria_for_comparison],
                        sign=pairwise_comparison.type
                    )
                )
        else:
            for category in categories:
                criteria_for_category = RecursiveQueries.get_criteria_for_category(category.id)
                rankings = Ranking.objects.filter(category=category)
                # we get unique ranking values and sort them
                reference_ranking_unique_values = list(set(rankings.values_list('reference_ranking', flat=True)))
                reference_ranking_unique_values.sort()
                # now we need to check every alternative and find other alternatives that are below this alternative in
                # reference_ranking
                for ranking_1 in rankings:
                    # 0 in reference_ranking means that it was not placed in the reference ranking
                    if ranking_1.reference_ranking == 0:
                        continue
                    # we have to get the index in the reference_ranking_unique_values of the current ranking's
                    # reference_ranking value
                    rr_index = reference_ranking_unique_values.index(ranking_1.reference_ranking)
                    for ranking_2 in rankings:
                        if ranking_1.id == ranking_2.id:
                            continue
                        if (
                                # we need to skip checking if the rr_index is the last one in the unique ranking,
                                # otherwise we will out of bounds for the reference_ranking_unique_values list
                                # when doing rr_index + 1
                                rr_index < len(reference_ranking_unique_values) - 1
                                and ranking_2.reference_ranking == reference_ranking_unique_values[rr_index + 1]
                        ):
                            comparisons_list.append(uged.Comparison(
                                alternative_1=str(ranking_1.alternative.id),
                                alternative_2=str(ranking_2.alternative.id),
                                criteria=[str(criterion.id) for criterion in criteria_for_category],
                                sign=PairwiseComparison.PREFERENCE
                            ))
                        if ranking_2.reference_ranking == reference_ranking_unique_values[rr_index]:
                            comparisons_list.append(uged.Comparison(
                                alternative_1=str(ranking_1.alternative.id),
                                alternative_2=str(ranking_2.alternative.id),
                                criteria=[str(criterion.id) for criterion in criteria_for_category],
                                sign=PairwiseComparison.INDIFFERENCE
                            ))
        return comparisons_list

    @staticmethod
    def get_preference_intensities(
            project: Project,
            categories: List[Category],
            criteria: List[Criterion]
    ) -> List[uged.Intensity]:
        """
        Retrieve preference intensities for a project, defined on categories and criteria.

        Parameters
        ----------
        project : Project
            A Django Project instance.
        categories : List[Category]
            A list of Django Category instances.
        criteria : List[Criterion]
            A list of Django Criterion instances.

        Returns
        -------
        List[uged.Intensity]
            A list of Intensity instances representing preference intensities.

        Notes
        -----
        Preference intensities can be defined on the whole category or on a specific criterion.
        """
        preference_intensities_list = []
        for preference_intensity in PreferenceIntensity.objects.filter(project=project):
            # intensity defined on the whole category
            if preference_intensity.category in categories:
                # get criteria for this category
                criteria_for_intensity = Criterion.objects.filter(
                    id__in=RecursiveQueries.get_criteria_for_category(preference_intensity.category.id)
                )
                preference_intensities_list.append(
                    uged.Intensity(
                        alternative_id_1=str(preference_intensity.alternative_1.id),
                        alternative_id_2=str(preference_intensity.alternative_2.id),
                        alternative_id_3=str(preference_intensity.alternative_3.id),
                        alternative_id_4=str(preference_intensity.alternative_4.id),
                        criteria=[str(criterion.id) for criterion in criteria_for_intensity],
                        sign=preference_intensity.type
                    )
                )
            # intensity defined on a criterion
            if preference_intensity.criterion in criteria:
                preference_intensities_list.append(
                    uged.Intensity(
                        alternative_id_1=str(preference_intensity.alternative_1.id),
                        alternative_id_2=str(preference_intensity.alternative_2.id),
                        alternative_id_3=str(preference_intensity.alternative_3.id),
                        alternative_id_4=str(preference_intensity.alternative_4.id),
                        criteria=[str(preference_intensity.criterion.id)],
                        sign=preference_intensity.type
                    )
                )
        return preference_intensities_list

    @staticmethod
    def get_best_worst_positions(categories: List[Category]) -> List[uged.Position]:
        """
        Retrieve best and worst positions for alternatives within specified categories.

        Parameters
        ----------
        categories : List[Category]
            A list of Django Category instances.

        Returns
        -------
        List[uged.Position]
            A list of Position instances representing best and worst positions for alternatives.

        Notes
        -----
        The best and worst positions are determined within the specified categories.
        """
        best_worst_positions_list = []
        for category in categories:
            rankings_count = Ranking.objects.filter(category=category).count()
            criteria_for_category = RecursiveQueries.get_criteria_for_category(category.id)
            for ranking in Ranking.objects.filter(category=category):
                if ranking.best_position is not None and ranking.worst_position is not None:
                    best_worst_positions_list.append(uged.Position(
                        alternative_id=str(ranking.alternative.id),
                        worst_position=ranking.worst_position,
                        best_position=ranking.best_position,
                        criteria=[str(criterion.id) for criterion in criteria_for_category]
                    ))
                elif ranking.best_position is not None:
                    best_worst_positions_list.append(uged.Position(
                        alternative_id=str(ranking.alternative.id),
                        worst_position=rankings_count,
                        best_position=ranking.best_position,
                        criteria=[str(criterion.id) for criterion in criteria_for_category]
                    ))
                elif ranking.worst_position is not None:
                    best_worst_positions_list.append(uged.Position(
                        alternative_id=str(ranking.alternative.id),
                        worst_position=ranking.worst_position,
                        best_position=1,
                        criteria=[str(criterion.id) for criterion in criteria_for_category]
                    ))
        return best_worst_positions_list

    @staticmethod
    def insert_inconsistencies_comparisons(
            category_root: Category,
            comparisons: List[uged.Comparison],
            group: int
    ) -> None:
        """
        Insert inconsistencies based on a list of comparisons within the specified category.

        Parameters
        ----------
        category_root : Category
            The root category for which inconsistencies will be inserted.
        comparisons : List[uged.Comparison]
            A list of Comparison instances containing information about pairwise comparisons.
        group : int
            The group identifier for the inconsistencies.

        Notes
        -----
        This method takes a list of uta-gms-engine Comparison instances and inserts inconsistencies into the specified
        category based on the provided comparisons.
        """
        for comparison in comparisons:
            # get names of the alternatives
            name_1 = Alternative.objects.get(id=int(comparison.alternative_1)).name
            name_2 = Alternative.objects.get(id=int(comparison.alternative_2)).name
            criteria_names = Criterion.objects \
                .filter(id__in=[int(_id) for _id in comparison.criteria]) \
                .values_list('name', flat=True)
            comparison_type = comparison.sign
            i_serializer = InconsistencySerializer(data={
                'group': group,
                'data': f"{name_1} {comparison_type} {name_2} on {', '.join(criteria_names)}",
                'type': comparison_type
            })
            if i_serializer.is_valid():
                i_serializer.save(category=category_root)

    @staticmethod
    def insert_inconsistencies_best_worst(
            category_root: Category,
            best_worsts: List[uged.Position],
            group: int
    ) -> None:
        """
        Insert inconsistencies based on a list of best-worst positions within the specified category.

        Parameters
        ----------
        category_root : Category
            The root category for which inconsistencies will be inserted.
        best_worsts : List[uged.Position]
            A list of Position instances containing information about best-worst positions.
        group : int
            The group identifier for the inconsistencies.

        Notes
        -----
        This method takes a list of uged.Position instances representing best-worst positions and inserts
        inconsistencies into the specified category based on the provided positions.
        """
        for best_worst in best_worsts:
            name = Alternative.objects.get(id=int(best_worst.alternative_id)).name
            criteria_names = Criterion.objects \
                .filter(id__in=[int(_id) for _id in best_worst.criteria]) \
                .values_list('name', flat=True)
            i_serializer = InconsistencySerializer(data={
                'group': group,
                'data': f"{name} - best position {best_worst.best_position}, worst position {best_worst.worst_position}"
                        f" on {', '.join(criteria_names)}",
                'type': Inconsistency.POSITION
            })
            if i_serializer.is_valid():
                i_serializer.save(category=category_root)

    @staticmethod
    def insert_inconsistencies_preference_intensities(
            category_root: Category,
            intensities: List[uged.Intensity],
            group: int
    ) -> None:
        """
        Insert inconsistencies based on a list of preference intensities within the specified category.

        Parameters
        ----------
        category_root : Category
            The root category for which inconsistencies will be inserted.
        intensities : List[uged.Intensity]
            A list of Intensity instances containing information about preference intensities.
        group : int
            The group identifier for the inconsistencies.

        Notes
        -----
        This method takes a list of uged.Intensity instances representing preference intensities and inserts
        inconsistencies into the specified category based on the provided intensities.
        """
        for intensity in intensities:
            name_1 = Alternative.objects.get(id=int(intensity.alternative_id_1)).name
            name_2 = Alternative.objects.get(id=int(intensity.alternative_id_2)).name
            name_3 = Alternative.objects.get(id=int(intensity.alternative_id_3)).name
            name_4 = Alternative.objects.get(id=int(intensity.alternative_id_4)).name
            criteria_names = Criterion.objects \
                .filter(id__in=[int(_id) for _id in intensity.criteria]) \
                .values_list('name', flat=True)
            intensity_sign = intensity.sign
            i_serializer = InconsistencySerializer(data={
                'group': group,
                'data': f"{name_1} - {name_2} {intensity_sign} {name_3} - {name_4} on {', '.join(criteria_names)}",
                'type': intensity_sign
            })
            if i_serializer.is_valid():
                i_serializer.save(category=category_root)

    @staticmethod
    def insert_inconsistencies(
            category_root: Category,
            inconsistencies: Tuple[
                List[uged.Comparison], List[uged.Comparison], List[uged.Position], List[uged.Intensity]
            ]
    ) -> None:
        """
        Insert inconsistencies into the specified category based on different groups of inconsistencies.

        Parameters
        ----------
        category_root : Category
            The root category for which inconsistencies will be inserted.
        inconsistencies : Tuple[List[uged.Comparison], List[uged.Comparison], List[uged.Position], List[uged.Intensity]]
            A tuple containing lists of different types of inconsistencies (comparisons, best-worst positions,
            preference intensities).

        Notes
        -----
        This method takes a tuple containing lists of different types of inconsistencies and inserts them into the specified
        category. The inconsistencies include comparisons, best-worst positions, and preference intensities. Each group of
        inconsistencies is associated with a unique group identifier.
        """
        for i, inconsistencies_group in enumerate(inconsistencies, start=1):
            i_comparisons, i_best_worst, i_intensities = inconsistencies_group

            EngineConverter.insert_inconsistencies_comparisons(category_root, i_comparisons, i)
            EngineConverter.insert_inconsistencies_best_worst(category_root, i_best_worst, i)
            EngineConverter.insert_inconsistencies_preference_intensities(category_root, i_intensities, i)

    @staticmethod
    def insert_acceptability_indices(category_root: Category, samples: Dict[str, List[float]]) -> None:
        """
        Insert acceptability indices values into the specified category for different alternatives.

        Parameters
        ----------
        category_root : Category
            The root category for which percentage values will be inserted.
        samples : Dict[str, List[float]]
            A dictionary where keys are alternative identifiers and values are lists of percentage values.

        Notes
        -----
        This method takes a dictionary of alternative identifiers and corresponding lists of percentage values and inserts
        them as AcceptabilityIndex instances into the specified category. Each alternative's indices are associated with
        distinct positions.
        """
        for key, percentages_data in samples.items():
            for i, value in enumerate(percentages_data):
                acceptability_index_serializer = AcceptabilityIndexSerializer(data={
                    'position': i + 1,
                    'percent': value,
                    'alternative': int(key)
                })
                if acceptability_index_serializer.is_valid():
                    acceptability_index_serializer.save(category=category_root)

    @staticmethod
    def insert_pairwise_winnings(category_root, pairwise_winnings: Dict[str, Dict[str, float]]) -> None:
        """
        Insert pairwise winning acceptability indices into the database for the specified category.

        This method takes a dictionary where keys are alternative IDs, and values are dictionaries representing the
        pairwise winning acceptability indices against other alternatives. It inserts these pairwise winning
        acceptability indices into the database and associates them with the specified category.

        Parameters:
        -----------
        category_root : Category
            The root category for which the pairwise winning percentages are to be inserted.
        pairwise_winnings : Dict[str, Dict[str, float]]
            A dictionary where keys are alternative IDs, and values are dictionaries representing pairwise winning
            acceptability indices against other alternatives.
        """
        for key_1, percentages in pairwise_winnings.items():
            for key_2, percentage in percentages.items():
                pairwise_winning_serializer = PairwiseWinningSerializer(data={
                    'percent': percentage,
                    'alternative_1': int(key_1),
                    'alternative_2': int(key_2)
                })
                if pairwise_winning_serializer.is_valid():
                    pairwise_winning_serializer.save(category=category_root)

    @staticmethod
    def update_rankings(category_root: Category, ranking: Dict[str, float]) -> None:
        """
        Update rankings for alternatives in the specified category based on the provided ranking dictionary.

        Parameters
        ----------
        category_root : Category
            The root category for which rankings will be updated.
        ranking : Dict[str, float]
            A dictionary where keys are alternative identifiers, and values are corresponding ranking values.

        Notes
        -----
        This method updates the rankings of alternatives within the specified category. The ranking dictionary should
        contain alternative identifiers as keys and their associated ranking values. The alternatives are ranked in descending
        order based on their ranking values, and the rankings are updated accordingly.
        """
        for i, (key, value) in enumerate(sorted(ranking.items(), key=lambda x: -x[1]), start=1):
            ranking = Ranking.objects.filter(alternative_id=int(key)).filter(category=category_root).first()
            ranking.ranking = i
            ranking.ranking_value = value
            ranking.save()

    @staticmethod
    def insert_criterion_functions(category_root: Category, functions: Dict[str, List[Tuple[float, float]]]) -> None:
        """
        Insert criterion functions into the specified category based on the provided functions dictionary.

        Parameters
        ----------
        category_root: Category
            The root category for which criterion functions will be inserted.
        functions: Dict[str, List[Tuple[float, float]]]
            A dictionary where keys are criterion identifiers, and values are lists of tuples representing
            (abscissa, ordinate) pairs for the criterion function.

        Notes
        -----
        This method inserts criterion functions into the specified category. The functions dictionary should contain
        criterion identifiers as keys, and the corresponding values should be lists of tuples representing (abscissa, ordinate)
        pairs for the criterion function. Multiple points define a function for a particular criterion.
        """
        for criterion_id, function in functions.items():
            for x, y in function:
                point = FunctionPointSerializer(data={
                    'ordinate': y,
                    'abscissa': x,
                    'criterion': int(criterion_id)
                })
                if point.is_valid():
                    point.save(category=category_root)

    @staticmethod
    def insert_relations(category_root: Category, relations: Dict[str, List[str]], relation_type: str) -> None:
        """
        Insert relations into the specified category based on the provided relations dictionary.

        Parameters
        ----------
        category_root : Category
            The root category for which relations will be inserted.
        relations : Dict[str, List[str]]
            A dictionary where keys are alternative identifiers, and values are lists of alternative identifiers
            representing relations.
        relation_type : str
            The type of relations - necessary or possible.

        Notes
        -----
        This method inserts relations into the specified category. The relations dictionary should contain alternative
        identifiers as keys, and the corresponding values should be lists of alternative identifiers representing
        relations. Each alternative can have multiple dependencies.
        """
        for alternative_id, dependent in relations.items():
            for d_alternative in dependent:
                relation = RelationSerializer(data={
                    'type': relation_type,
                    'alternative_1': int(alternative_id),
                    'alternative_2': int(d_alternative)
                })
                if relation.is_valid():
                    relation.save(category=category_root)

    @staticmethod
    def update_extreme_ranks(category_root: Category, extreme_ranks: Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]]) -> None:
        """
        Update extreme rank positions for the specified category.

        This method updates the extreme rank positions (pessimistic and optimistic) for each alternative in the provided
        dictionary. The dictionary keys are alternative IDs, and values are tuples representing extreme rank positions.

        Parameters:
        -----------
        category_root : Category
            The root category for which the extreme rank positions are to be updated.
        extreme_ranks : Dict[str, Tuple[Tuple[int, int], Tuple[int, int]]]
            A dictionary where keys are alternative IDs, and values are tuples representing extreme rank positions. The
            first tuple represents pessimistic ranks (worst and best), and the second tuple represents optimistic ranks.
        """
        for key, extreme_positions in extreme_ranks.items():
            ranking = Ranking.objects.filter(alternative_id=int(key)).filter(category=category_root).first()
            ranking.extreme_pessimistic_worst = extreme_positions[0][0]
            ranking.extreme_pessimistic_best = extreme_positions[0][1]
            ranking.extreme_optimistic_worst = extreme_positions[1][0]
            ranking.extreme_optimistic_best = extreme_positions[1][1]
            ranking.save()


class ProjectBatch(APIView):
    """
    API View for handling batch operations related to projects.

    This view provides:
     - endpoint to retrieve detailed information about a specific project.
     - endpoint to perform batch updates on various aspects of a project,
       such as criteria, alternatives, categories, preference intensities, and more.

    Permissions
    -----------
    - Users must be authenticated.
    - Users must be the owner of the project to access this view.

    Methods
    -------
    - GET: Retrieve detailed information about a specific project.
    - PATCH: Perform batch updates on a project based on the provided data.
    """

    permission_classes = [IsOwnerOfProject]

    def get(self, request, *args, **kwargs):
        """
        Retrieve detailed information about a specific project.

        Parameters
        ----------
        request : rest_framework.request.Request
            The HTTP request object.
        kwargs : dict
            A dictionary containing additional keyword arguments.
            - project_pk (str): The unique identifier of the project to retrieve details for.

        Returns
        -------
        Response
            A serialized representation of the project's detailed information.
        """
        project_id = kwargs.get('project_pk')
        project = Project.objects.filter(id=project_id).first()
        project_serializer = ProjectSerializerWhole(project)
        return Response(project_serializer.data)

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
        """
        Perform batch updates on a project based on the provided data.

        Parameters
        ----------
        request : rest_framework.request.Request
            The HTTP request object. It should include the following data:
            - pairwise_mode: bool, optional
                Indicates whether to set the project's pairwise mode.
            - criteria: list, optional
                A list of dictionaries representing criteria data.
            - alternatives: list, optional
                A list of dictionaries representing alternatives data.
            - categories: list, optional
                A list of dictionaries representing categories data.
            - preference_intensities: list, optional
                A list of dictionaries representing preference intensities data.
        kwargs : dict
            A dictionary containing additional keyword arguments.
            - project_pk (str): The unique identifier of the project to perform batch updates on.

        Returns
        -------
        Response
            A serialized representation of the updated project.
        """
        data = request.data
        project_id = kwargs.get("project_pk")
        project = Project.objects.filter(id=project_id).first()

        # set project's comparisons mode
        pairwise_mode_data = data.get("pairwise_mode", False)
        project.pairwise_mode = pairwise_mode_data
        project.save()

        # get data from request
        criteria_data = data.get("criteria", [])
        alternatives_data = data.get("alternatives", [])
        categories_data = data.get("categories", [])
        preference_intensities_data = data.get("preference_intensities", [])

        # ------------------------------------------------------------------------------------------------------------ #
        # Criteria
        # deleting criteria
        BatchOperations.delete_criteria(project, criteria_data)
        # insert or update criteria
        for criterion_data in criteria_data:
            criterion_id = criterion_data.get('id')
            criterion = BatchOperations.insert_update_criterion(project, criterion_data)

            if criterion is not None:
                # UPDATE DATA
                for alternative_data in alternatives_data:
                    # update criterion id in performances
                    performances_data = alternative_data.get('performances', [])
                    for performance_data in performances_data:
                        if performance_data.get('criterion', -1) == criterion_id:
                            performance_data['criterion'] = criterion.id

                # update criterion id in preference_intensities
                for pref_intensity_data in preference_intensities_data:
                    if pref_intensity_data.get('criterion', -1) == criterion_id:
                        pref_intensity_data['criterion'] = criterion.id

                for category_data in categories_data:
                    # update criterion id in criterion_categories
                    criterion_categories_data = category_data.get('criterion_categories', [])
                    for criterion_category_data in criterion_categories_data:
                        if criterion_category_data.get('criterion', -1) == criterion_id:
                            criterion_category_data['criterion'] = criterion.id

        # ------------------------------------------------------------------------------------------------------------ #
        # Alternatives
        # deleting alternatives
        BatchOperations.delete_alternatives(project, alternatives_data)
        # insert or update alternatives
        for alternative_data in alternatives_data:
            alternative_id = alternative_data.get('id')
            alternative = BatchOperations.insert_update_alternative(project, alternative_data)
            if alternative is not None:
                # Performances
                performances_data = alternative_data.get('performances', [])
                # it may happen that the user had an alternative with id=1, deleted it and added a new one with id=1
                # and the performances were not deleted in cascade, so we need to delete them manually because the new
                # ones do not have an id in the payload, and they would raise a ValidationError in the serializer
                BatchOperations.delete_performances(alternative, performances_data)
                # insert or update performances
                for performance_data in performances_data:
                    BatchOperations.insert_update_performance(alternative, performance_data)

                # UPDATE DATA
                # update alternatives id in preference intensities
                for pref_intensity_data in preference_intensities_data:
                    for alternative_number in range(1, 5):
                        if pref_intensity_data.get(f'alternative_{alternative_number}', -1) == alternative_id:
                            pref_intensity_data[f'alternative_{alternative_number}'] = alternative.id

                for category_data in categories_data:
                    # update alternative id in pairwise comparisons
                    pairwise_comparisons_data = category_data.get('pairwise_comparisons', [])
                    for pairwise_comparison_data in pairwise_comparisons_data:
                        if pairwise_comparison_data.get('alternative_1', -1) == alternative_id:
                            pairwise_comparison_data['alternative_1'] = alternative.id
                        if pairwise_comparison_data.get('alternative_2', -1) == alternative_id:
                            pairwise_comparison_data['alternative_2'] = alternative.id

                    # update alternative id in ranking
                    rankings_data = category_data.get('rankings', [])
                    for ranking_data in rankings_data:
                        if ranking_data.get('alternative', -1) == alternative_id:
                            ranking_data['alternative'] = alternative.id

        # ------------------------------------------------------------------------------------------------------------ #
        # Categories
        # deleting categories
        BatchOperations.delete_categories(project, categories_data)

        # insert or update categories
        for category_data in categories_data:
            category_id = category_data.get('id')
            category = BatchOperations.insert_update_category(project, category_data)
            if category is not None:

                # CriterionCategories
                ccs_data = category_data.get('criterion_categories', [])
                BatchOperations.delete_criterion_categories(category, ccs_data)
                for cc_data in ccs_data:
                    BatchOperations.insert_update_criterion_categories(category, cc_data)

                # Pairwise Comparisons
                pairwise_comparisons_data = category_data.get('pairwise_comparisons', [])
                BatchOperations.delete_pairwise_comparisons(category, pairwise_comparisons_data)
                for pairwise_comparison_data in pairwise_comparisons_data:
                    BatchOperations.insert_update_pairwise_comparison(category, pairwise_comparison_data)

                # Rankings
                rankings_data = category_data.get('rankings', [])
                BatchOperations.delete_rankings(category, rankings_data)
                for ranking_data in rankings_data:
                    BatchOperations.insert_update_ranking(category, ranking_data)

                # delete inconsistencies
                inconsistencies = Inconsistency.objects.filter(category=category)
                inconsistencies.delete()

                # UPDATE DATA
                # update criterion id in preference_intensities
                for pref_intensity_data in preference_intensities_data:
                    if pref_intensity_data.get('category', -1) == category_id:
                        pref_intensity_data['category'] = category.id

        # ------------------------------------------------------------------------------------------------------------ #
        # Preference Intensities
        # deleting
        BatchOperations.delete_preference_intensities(project, preference_intensities_data)

        for pref_intensity_data in preference_intensities_data:
            BatchOperations.insert_update_preference_intensity(project, pref_intensity_data)

        # ------------------------------------------------------------------------------------------------------------ #
        # reset the results
        for category in Category.objects.filter(project=project):
            category.has_results = False
            category.save()

        project_serializer = ProjectSerializerWhole(project)
        return Response(project_serializer.data)


class CategoryResults(APIView):
    """
    API view class for processing and updating results for a specific category.

    Permissions
    -----------
    - Users must be authenticated.
    - Users must be the owner of the category to access this view.

    Methods
    -------
    - POST: Perform calculations on a category.
    """

    permission_classes = [IsOwnerOfCategory]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Handles the HTTP POST request to compute and update results for the specified category.

        Parameters:
        -----------
        request : rest_framework.request.Request
            The HTTP request object.
        kwargs : dict
            A dictionary containing additional keyword arguments.
            - category_pk (str): The unique identifier of the category to perform calculations on.

        Returns:
        --------
        Response
            A response indicating the success or failure of the computation and update process.
        """
        category_id = kwargs.get('category_pk')
        category_root = Category.objects.get(id=category_id)
        project = category_root.project

        # Get children of the category
        categories = RecursiveQueries.get_categories_subtree(category_id)
        criteria = RecursiveQueries.get_criteria_for_category(category_id)

        # get uta-gms-engine criteria
        criteria_uged = EngineConverter.get_criteria(criteria)
        if len(criteria_uged) == 0:
            for category in Category.objects.filter(project=project):
                category.has_results = False
                category.save()
            return Response({"details": "There are no active criteria!"}, status=status.HTTP_400_BAD_REQUEST)

        # get performance_table_list
        alternatives = Alternative.objects.filter(project=project)
        performances = EngineConverter.get_performances(alternatives, criteria)

        # get comparisons
        comparisons_list = EngineConverter.get_comparisons(project, categories)

        # get preference intensities
        preference_intensities_list = EngineConverter.get_preference_intensities(project, categories, criteria)

        # get best-worst positions
        best_worst_positions_list = EngineConverter.get_best_worst_positions(categories)

        # delete previous inconsistencies if any
        inconsistencies = Inconsistency.objects.filter(category=category_root)
        inconsistencies.delete()

        # define if to use the sampler
        sampler_on = True if category_root.samples > 0 else False

        # RANKING
        solver = Solver()
        try:
            ranking, functions, acceptability_indices_uge, pairwise_winnings_uge, samples_used, extreme_ranks, necessary, possible, sampler_error = solver.get_representative_value_function_dict(
                performance_table_dict=performances,
                comparisons=comparisons_list,
                criteria=criteria_uged,
                positions=best_worst_positions_list,
                intensities=preference_intensities_list,
                sampler_path='/sampler/polyrun-1.1.0-jar-with-dependencies.jar',
                number_of_samples=str(category_root.samples),
                sampler_on=sampler_on
            )
        except InconsistencyException as e:
            inconsistencies = e.data
            EngineConverter.insert_inconsistencies(category_root, inconsistencies)
        else:
            # updating acceptability indices and pairwise winnings
            acceptability_indices = AcceptabilityIndex.objects.filter(category=category_root)
            acceptability_indices.delete()
            pairwise_winnings = PairwiseWinning.objects.filter(category=category_root)
            pairwise_winnings.delete()
            category_root.sampler_error = None
            # check if sampler worked
            if not sampler_error and sampler_on:
                EngineConverter.insert_acceptability_indices(category_root, acceptability_indices_uge)
                EngineConverter.insert_pairwise_winnings(category_root, pairwise_winnings_uge)
            elif sampler_error:
                category_root.sampler_error = sampler_error
            else:
                category_root.sampler_error = "Sampler turned off"

            # update rankings
            EngineConverter.update_rankings(category_root, ranking)

            # update extreme ranks
            EngineConverter.update_extreme_ranks(category_root, extreme_ranks)

            # insert criterion functions
            criterion_function_points = FunctionPoint.objects.filter(category=category_root)
            criterion_function_points.delete()
            EngineConverter.insert_criterion_functions(category_root, functions)

            # insert relations
            relations = Relation.objects.filter(category=category_root)
            relations.delete()
            EngineConverter.insert_relations(category_root, necessary, Relation.NECESSARY)
            EngineConverter.insert_relations(category_root, possible, Relation.POSSIBLE)

            # set successful save
            category_root.has_results = True
            category_root.save()

        return Response({"details": "success"})
