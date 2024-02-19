from typing import Any, Dict, List, Union

from ..models import (
    Alternative,
    Category,
    Criterion,
    CriterionCategory,
    PairwiseComparison,
    Performance,
    PreferenceIntensity,
    Project,
    Ranking
)
from ..serializers import (
    AlternativeSerializer,
    CategorySerializer,
    CriterionCategorySerializer,
    CriterionSerializer,
    PairwiseComparisonSerializer,
    PerformanceSerializer,
    PerformanceSerializerUpdate,
    PreferenceIntensitySerializer,
    RankingSerializer
)


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
