from dagster import AssetSpec
from dagster._core.definitions.definitions_class import Definitions
from dagster_airlift.core import (
    AirflowBasicAuthBackend,
    AirflowInstance,
    assets_with_task_mappings,
    build_defs_from_airflow_instance,
)

from perf_harness.dagster_defs.constants import (
    AIRFLOW_BASE_URL,
    AIRFLOW_INSTANCE_NAME,
    PASSWORD,
    USERNAME,
)
from perf_harness.shared.constants import get_num_assets, get_num_dags, get_num_tasks

airflow_instance = AirflowInstance(
    auth_backend=AirflowBasicAuthBackend(
        webserver_url=AIRFLOW_BASE_URL, username=USERNAME, password=PASSWORD
    ),
    name=AIRFLOW_INSTANCE_NAME,
)


def build_asset_specs_for_task(
    task_name: str, prev_asset_specs: list[AssetSpec]
) -> list[AssetSpec]:
    return [
        # Create a bunch of dependencies for each asset.
        AssetSpec(f"{task_name}_asset_{i}", deps=[spec.key for spec in prev_asset_specs])
        for i in range(get_num_assets())
    ]


def get_dag_defs() -> Definitions:
    all_dag_defs = []
    prev_asset_specs = []
    for i in range(get_num_dags()):
        dag_id = f"dag_{i}"
        task_mappings = {}
        for j in range(get_num_tasks()):
            task_name = f"task_{i}_{j}"
            specs = build_asset_specs_for_task(task_name, prev_asset_specs)
            task_mappings[task_name] = specs
            prev_asset_specs = specs
        all_dag_defs.append(
            Definitions(
                assets=assets_with_task_mappings(
                    dag_id=dag_id,
                    task_mappings=task_mappings,
                )
            )
        )
    return Definitions.merge(*all_dag_defs)


defs = build_defs_from_airflow_instance(
    airflow_instance=airflow_instance,
    defs=get_dag_defs(),
)
