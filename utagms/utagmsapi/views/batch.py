from django.db import transaction
from django.db.models import Max, Min
from django_celery_results.models import TaskResult
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import (
    Category,
    Inconsistency,
    Project
)
from ..permissions import IsOwnerOfProject
from ..serializers import (
    JobSerializer, ProjectSerializerWhole
)
from ..tasks import run_engine
from ..utils.batch_operations import BatchOperations


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


class ProjectResults(APIView):
    """
    API view class for processing and updating results for a project.

    Permissions
    -----------
    - Users must be authenticated.
    - Users must be the owner of the project to access this view.

    Methods
    -------
    - GET:
        Retrieve the status of project results.
        Returns a response indicating whether the results are ready or still processing.

    - POST:
        Queue tasks for running the engine on project categories.
        Returns a response confirming the tasks queued for processing.
    """

    permission_classes = [IsOwnerOfProject]

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        """
        Retrieve the status of project results.

        This method checks if the results for the project are ready or still processing. It returns a response
        indicating whether the results are ready or still being processed.

        Parameters:
        -----------
        request : rest_framework.request.Request
            The HTTP request object.
        project_pk : str
            The unique identifier of the project.

        Returns:
        --------
        Response
            A JSON response indicating whether the results are ready (200) or still processing (202).
        """
        project_id = kwargs.get('project_pk')
        project = Project.objects.filter(id=project_id).first()
        for job in project.jobs.filter(group=project.jobs.aggregate(max_group=Max('group'))['max_group']):
            if not TaskResult.objects.filter(task_id=job.task).exists():
                return Response({"message": "Results not ready yet"}, status=status.HTTP_202_ACCEPTED)
        return Response({"message": "Results ready"})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Queue tasks for running the engine on project categories.

        This method queues tasks for running the engine on each category of the project. It returns a response
        confirming the tasks have been queued for processing.

        Parameters:
        -----------
        request : rest_framework.request.Request
            The HTTP request object.
        project_pk : str
            The unique identifier of the project.

        Returns:
        --------
        Response
            A JSON response confirming the tasks queued for processing.
        """
        project_id = kwargs.get('project_pk')
        project = Project.objects.filter(id=project_id).first()
        group_number = project.jobs.aggregate(min_group=Min('group'))['min_group']
        for category in project.categories.all():
            task = run_engine.delay(category.id)
            job_serializer = JobSerializer(data={
                'project': project.id,
                'category': category.id,
                'group': group_number + 1 if group_number is not None else 1,
                'task': task.id
            })
            if job_serializer.is_valid():
                job_serializer.save()

        return Response({"message": f"Tasks to run for project {project.name} queued for processing"})
