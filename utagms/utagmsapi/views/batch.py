import utagmsengine.dataclasses as uged
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from utagmsengine.solver import Solver, Inconsistency as InconsistencyException

from ..models import (
    Project,
    Criterion,
    Alternative,
    Performance,
    FunctionPoint,
    PreferenceIntensity,
    PairwiseComparison,
    Category,
    CriterionCategory,
    Ranking,
    Percentage,
    Inconsistency
)
from ..permissions import (
    IsOwnerOfProject,
    IsOwnerOfCategory
)
from ..serializers import (
    CriterionSerializer,
    AlternativeSerializer,
    PerformanceSerializer,
    PerformanceSerializerUpdate,
    PreferenceIntensitySerializer,
    ProjectSerializerWhole,
    PairwiseComparisonSerializer,
    FunctionPointSerializer,
    CategorySerializer,
    CriterionCategorySerializer,
    RankingSerializer,
    PercentageSerializer,
    InconsistencySerializer
)
from ..utils.recursive_queries import RecursiveQueries


class ProjectBatch(APIView):
    permission_classes = [IsOwnerOfProject]

    def get(self, request, *args, **kwargs):
        project_id = kwargs.get('project_pk')
        project = Project.objects.filter(id=project_id).first()
        project_serializer = ProjectSerializerWhole(project)
        return Response(project_serializer.data)

    @transaction.atomic
    def patch(self, request, *args, **kwargs):
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

        # Criteria
        # if there are criteria that were not in the payload, we delete them
        criteria_ids_db = project.criteria.values_list('id', flat=True)
        criteria_ids_request = [criterion_data.get('id') for criterion_data in criteria_data]
        criteria_ids_to_delete = set(criteria_ids_db) - set(criteria_ids_request)
        project.criteria.filter(id__in=criteria_ids_to_delete).delete()

        # if there exists a criterion with provided ID in the project, we update it
        # if there does not exist a criterion with provided ID in the project, we insert it (with a new id)
        for criterion_data in criteria_data:
            criterion_id = criterion_data.get('id')

            try:
                criterion = project.criteria.get(id=criterion_id)
                criterion_serializer = CriterionSerializer(criterion, data=criterion_data)
            except Criterion.DoesNotExist:
                criterion_serializer = CriterionSerializer(data=criterion_data)

            if criterion_serializer.is_valid():
                criterion = criterion_serializer.save(project=project)

                # update criterion id in performances
                for alternative_data in alternatives_data:
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

        # Alternatives
        # if there are alternatives that were not in the payload, we delete them
        alternatives_ids_db = project.alternatives.values_list('id', flat=True)
        alternatives_ids_request = [alternative_data.get('id') for alternative_data in alternatives_data]
        alternatives_ids_to_delete = set(alternatives_ids_db) - set(alternatives_ids_request)
        project.alternatives.filter(id__in=alternatives_ids_to_delete).delete()

        # if there exists an alternative with provided ID in the project, we update it
        # if there does not exist an alternative with provided ID in the project, we insert it (with a new id)
        for alternative_data in alternatives_data:
            alternative_id = alternative_data.get('id')

            try:
                alternative = project.alternatives.get(id=alternative_id)
                alternative_serializer = AlternativeSerializer(alternative, data=alternative_data)
            except Alternative.DoesNotExist:
                alternative_serializer = AlternativeSerializer(data=alternative_data)

            if alternative_serializer.is_valid():
                alternative = alternative_serializer.save(project=project)

                # Performances
                performances_data = alternative_data.get('performances', [])

                # it may happen that the user had an alternative with id=1, deleted it and added a new one with id=1
                # and the performances were not deleted in cascade, so we need to delete them manually because the new
                # ones do not have an id in the payload, and they would raise a ValidationError in the serializer
                performances_ids_db = alternative.performances.values_list('id', flat=True)
                performances_ids_request = [performance_data.get('id', -1) for performance_data in performances_data]
                performances_ids_to_delete = set(performances_ids_db) - set(performances_ids_request)
                alternative.performances.filter(id__in=performances_ids_to_delete).delete()

                for performance_data in performances_data:
                    performance_id = performance_data.get('id')

                    try:
                        performance = alternative.performances.get(id=performance_id)
                        performance_serializer = PerformanceSerializerUpdate(performance, data=performance_data)
                    except Performance.DoesNotExist:
                        performance_serializer = PerformanceSerializer(data=performance_data)

                    if performance_serializer.is_valid():
                        performance_serializer.save(alternative=alternative)

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

        # Categories
        # if there are categories that were not in the payload, we delete them
        categories_ids_db = project.categories.values_list('id', flat=True)
        categories_ids_request = [category_data.get('id') for category_data in categories_data]
        categories_ids_to_delete = set(categories_ids_db) - set(categories_ids_request)
        project.categories.filter(id__in=categories_ids_to_delete).delete()

        # if there exists a category with provided ID in the project, we update it
        # if there does not exist a category with provided ID in the project, we insert it (with a new id)
        for category_data in categories_data:
            category_id = category_data.get('id')

            try:
                category = project.categories.get(id=category_id)
                category_serializer = CategorySerializer(category, data=category_data)
            except Category.DoesNotExist:
                category_serializer = CategorySerializer(data=category_data)

            if category_serializer.is_valid():
                category = category_serializer.save(project=project)

                # CriterionCategories
                ccs_data = category_data.get('criterion_categories', [])

                ccs_ids_db = category.criterion_categories.values_list('id', flat=True)
                ccs_ids_request = [cc_data.get('id') for cc_data in ccs_data]
                ccs_ids_to_delete = set(ccs_ids_db) - set(ccs_ids_request)
                category.criterion_categories.filter(id__in=ccs_ids_to_delete).delete()

                for cc_data in ccs_data:
                    cc_id = cc_data.get('id')
                    try:
                        criterion_category = category.criterion_categories.get(id=cc_id)
                        cc_serializer = CriterionCategorySerializer(criterion_category, data=cc_data)
                    except CriterionCategory.DoesNotExist:
                        cc_serializer = CriterionCategorySerializer(data=cc_data)
                    if cc_serializer.is_valid():
                        cc_serializer.save(category=category)

                # Pairwise Comparisons
                pairwise_comparisons_data = category_data.get('pairwise_comparisons', [])
                pairwise_comparisons_ids_db = category.pairwise_comparisons.values_list('id', flat=True)
                pairwise_comparisons_ids_request = [pc_data.get('id') for pc_data in pairwise_comparisons_data]
                pairwise_comparisons_ids_to_delete = (
                        set(pairwise_comparisons_ids_db) - set(pairwise_comparisons_ids_request)
                )
                category.pairwise_comparisons.filter(id__in=pairwise_comparisons_ids_to_delete).delete()
                for pairwise_comparison_data in pairwise_comparisons_data:
                    pairwise_comparison_id = pairwise_comparison_data.get('id')
                    try:
                        pairwise_comparison = category.pairwise_comparisons.get(id=pairwise_comparison_id)
                        pairwise_comparison_serializer = PairwiseComparisonSerializer(pairwise_comparison,
                                                                                      data=pairwise_comparison_data)
                    except PairwiseComparison.DoesNotExist:
                        pairwise_comparison_serializer = PairwiseComparisonSerializer(data=pairwise_comparison_data)
                    if pairwise_comparison_serializer.is_valid():
                        pairwise_comparison_serializer.save(category=category)

                # Rankings
                rankings_data = category_data.get('rankings', [])
                rankings_ids_db = category.rankings.values_list('id', flat=True)
                rankings_ids_request = [ranking_data.get('id') for ranking_data in rankings_data]
                rankings_ids_to_delete = set(rankings_ids_db) - set(rankings_ids_request)
                category.rankings.filter(id__in=rankings_ids_to_delete).delete()
                for ranking_data in rankings_data:
                    ranking_id = ranking_data.get('id')
                    try:
                        ranking = category.rankings.get(id=ranking_id)
                        ranking_serializer = RankingSerializer(ranking, data=ranking_data)
                    except Ranking.DoesNotExist:
                        ranking_serializer = RankingSerializer(data=ranking_data)
                    if ranking_serializer.is_valid():
                        ranking_serializer.save(category=category)

                # delete inconsistencies
                inconsistencies = Inconsistency.objects.filter(category=category)
                inconsistencies.delete()

                # update criterion id in preference_intensities
                for pref_intensity_data in preference_intensities_data:
                    if pref_intensity_data.get('category', -1) == category_id:
                        pref_intensity_data['category'] = category.id

        # reset the hasse_graphs
        for category in Category.objects.filter(project=project):
            category.hasse_graph = {}
            category.save()

        # Preference Intensities
        pref_intensities_ids_db = project.preference_intensities.values_list('id', flat=True)
        pref_intensities_ids_request = [pref_intensity_data.get('id')
                                        for pref_intensity_data in preference_intensities_data]
        pref_intensities_ids_to_delete = set(pref_intensities_ids_db) - set(pref_intensities_ids_request)
        project.preference_intensities.filter(id__in=pref_intensities_ids_to_delete).delete()

        for pref_intensity_data in preference_intensities_data:
            pref_intensity_id = pref_intensity_data.get('id')
            try:
                pref_intensity = project.preference_intensities.get(id=pref_intensity_id)
                pref_intensity_serializer = PreferenceIntensitySerializer(pref_intensity,
                                                                          data=pref_intensity_data)
            except PreferenceIntensity.DoesNotExist:
                pref_intensity_serializer = PreferenceIntensitySerializer(data=pref_intensity_data)
            if pref_intensity_serializer.is_valid():
                pref_intensity_serializer.save(project=project)

        project_serializer = ProjectSerializerWhole(project)
        return Response(project_serializer.data)


class CategoryResults(APIView):
    permission_classes = [IsOwnerOfCategory]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        category_id = kwargs.get('category_pk')
        category_root = Category.objects.get(id=category_id)
        project = category_root.project

        # Get children of the category
        categories = RecursiveQueries.get_categories_subtree(category_id)
        criteria = RecursiveQueries.get_criteria_for_category(category_id)

        # get uta-gms-engine criteria
        criteria_uged = [
            uged.Criterion(criterion_id=str(c.id), number_of_linear_segments=c.linear_segments, gain=c.gain)
            for c in criteria
        ]
        if len(criteria_uged) == 0:
            for category in Category.objects.filter(project=project):
                category.hasse_graph = {}
                category.save()
            return Response({"details": "There are no active criteria!"}, status=status.HTTP_400_BAD_REQUEST)

        # get alternatives
        alternatives = Alternative.objects.filter(project=project)

        # get performance_table_list
        # we need performances only from criteria
        performances = {}
        for alternative in alternatives:
            performances[str(alternative.id)] = {
                str(criterion_id): value for criterion_id, value in
                Performance.objects
                .filter(alternative=alternative)
                .filter(criterion__in=criteria)
                .values_list('criterion', 'value')
            }

        # get preferences and indifferences
        preferences_list = []
        indifferences_list = []
        if project.pairwise_mode:
            for pairwise_comparison in PairwiseComparison.objects.filter(category__in=categories):
                # we have to find criteria that the pairwise comparison is related to
                criteria_for_comparison = Criterion.objects.filter(
                    id__in=RecursiveQueries.get_criteria_for_category(pairwise_comparison.category.id)
                )
                if pairwise_comparison.type == PairwiseComparison.PREFERENCE:
                    preferences_list.append(
                        uged.Preference(
                            superior=str(pairwise_comparison.alternative_1.id),
                            inferior=str(pairwise_comparison.alternative_2.id),
                            criteria=[str(criterion.id) for criterion in criteria_for_comparison]
                        )
                    )
                if pairwise_comparison.type == PairwiseComparison.INDIFFERENCE:
                    indifferences_list.append(
                        uged.Indifference(
                            equal1=str(pairwise_comparison.alternative_1.id),
                            equal2=str(pairwise_comparison.alternative_2.id),
                            criteria=[str(criterion.id) for criterion in criteria_for_comparison]
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
                            preferences_list.append(uged.Preference(
                                superior=str(ranking_1.alternative.id),
                                inferior=str(ranking_2.alternative.id),
                                criteria=[str(criterion.id) for criterion in criteria_for_category]
                            ))
                        if ranking_2.reference_ranking == reference_ranking_unique_values[rr_index]:
                            indifferences_list.append(uged.Indifference(
                                equal1=str(ranking_1.alternative.id),
                                equal2=str(ranking_2.alternative.id),
                                criteria=[str(criterion.id) for criterion in criteria_for_category]
                            ))

        preference_intensities_list = []
        # get preference intensities
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
                        sign='>'
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
                        sign='>'
                    )
                )

        # get best-worst positions
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

        # delete previous inconsistencies if any
        inconsistencies = Inconsistency.objects.filter(category=category_root)
        inconsistencies.delete()

        # RANKING
        solver = Solver()
        try:
            ranking, functions, samples = solver.get_representative_value_function_dict(
                performance_table_dict=performances,
                preferences=preferences_list,
                indifferences=indifferences_list,
                criteria=criteria_uged,
                positions=best_worst_positions_list,
                intensities=preference_intensities_list,
                sampler_path='/sampler/polyrun-1.1.0-jar-with-dependencies.jar',
                number_of_samples='100'
            )
        except InconsistencyException as e:
            inconsistencies = e.data
            for i, inconsistencies_group in enumerate(inconsistencies, start=1):
                i_preferences, i_indifferences, i_best_worst, i_intensities = inconsistencies_group

                for preference in i_preferences:
                    # get names of the alternatives
                    name_1 = Alternative.objects.get(id=int(preference.superior)).name
                    name_2 = Alternative.objects.get(id=int(preference.inferior)).name
                    criteria_names = Criterion.objects.filter(
                        id__in=[int(_id) for _id in preference.criteria]
                    ).values_list('name', flat=True)
                    i_serializer = InconsistencySerializer(data={
                        'group': i,
                        'data': f"{name_1} > {name_2} on {', '.join(criteria_names)}",
                        'type': Inconsistency.PREFERENCE
                    })
                    if i_serializer.is_valid():
                        i_serializer.save(category=category_root)

                for indifference in i_indifferences:
                    # get names of the alternatives
                    name_1 = Alternative.objects.get(id=int(indifference.equal1)).name
                    name_2 = Alternative.objects.get(id=int(indifference.equal2)).name
                    criteria_names = Criterion.objects.filter(
                        id__in=[int(_id) for _id in indifference.criteria]
                    ).values_list('name', flat=True)
                    i_serializer = InconsistencySerializer(data={
                        'group': i,
                        'data': f"{name_1} = {name_2} on {', '.join(criteria_names)}",
                        'type': Inconsistency.INDIFFERENCE
                    })
                    if i_serializer.is_valid():
                        i_serializer.save(category=category_root)

                for best_worst in i_best_worst:
                    name = Alternative.objects.get(id=int(best_worst.alternative_id)).name
                    criteria_names = Criterion.objects.filter(
                        id__in=[int(_id) for _id in best_worst.criteria]
                    ).values_list('name', flat=True)
                    i_serializer = InconsistencySerializer(data={
                        'group': i,
                        'data': f"{name} - best position {best_worst.best_position}, worst position {best_worst.worst_position} on {', '.join(criteria_names)}",
                        'type': Inconsistency.POSITION
                    })
                    if i_serializer.is_valid():
                        i_serializer.save(category=category_root)

                for intensity in i_intensities:
                    name_1 = Alternative.objects.get(id=int(intensity.alternative_id_1)).name
                    name_2 = Alternative.objects.get(id=int(intensity.alternative_id_2)).name
                    name_3 = Alternative.objects.get(id=int(intensity.alternative_id_3)).name
                    name_4 = Alternative.objects.get(id=int(intensity.alternative_id_4)).name
                    criteria_names = Criterion.objects.filter(
                        id__in=[int(_id) for _id in intensity.criteria]
                    ).values_list('name', flat=True)
                    i_serializer = InconsistencySerializer(data={
                        'group': i,
                        'data': f"{name_1} - {name_2} > {name_3} - {name_4} on {', '.join(criteria_names)}",
                        'type': Inconsistency.INTENSITY
                    })
                    if i_serializer.is_valid():
                        i_serializer.save(category=category_root)
        else:

            # updating percentages
            for key, percentages_data in samples.items():
                percentages = Percentage.objects.filter(alternative_id=int(key)).filter(category=category_root)
                percentages.delete()

                for i, value in enumerate(percentages_data):
                    percentage_serializer = PercentageSerializer(data={
                        'position': i + 1,
                        'percent': value,
                        'alternative': int(key)
                    })
                    if percentage_serializer.is_valid():
                        percentage_serializer.save(category=category_root)

            # updating rankings
            for i, (key, value) in enumerate(sorted(ranking.items(), key=lambda x: -x[1]), start=1):
                ranking = Ranking.objects.filter(alternative_id=int(key)).filter(category=category_root).first()
                ranking.ranking = i
                ranking.ranking_value = value
                ranking.save()

            criterion_function_points = FunctionPoint.objects.filter(category=category_root)
            criterion_function_points.delete()
            # updating criterion functions
            for criterion_id, function in functions.items():

                for x, y in function:
                    point = FunctionPointSerializer(data={
                        'ordinate': y,
                        'abscissa': x,
                        'criterion': int(criterion_id)
                    })
                    if point.is_valid():
                        point.save(category=category_root)

            # HASSE GRAPH
            hasse_graph = solver.get_hasse_diagram_dict(
                performances,
                preferences_list,
                indifferences_list,
                criteria_uged,
                best_worst_positions_list
            )
            hasse_graph = {int(key): [int(value) for value in values] for key, values in hasse_graph.items()}
            category_root.hasse_graph = hasse_graph
            category_root.save()

        return Response({"details": "success"})
