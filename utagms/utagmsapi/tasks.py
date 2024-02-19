from celery import shared_task
from utagmsengine.solver import Inconsistency as InconsistencyException, Solver

from .models import (
    AcceptabilityIndex,
    Alternative,
    Category,
    FunctionPoint,
    Inconsistency,
    PairwiseWinning,
    Relation
)
from .utils.engine_converter import EngineConverter
from .utils.recursive_queries import RecursiveQueries


@shared_task
def run_engine(category_id: int):
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
        return

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
