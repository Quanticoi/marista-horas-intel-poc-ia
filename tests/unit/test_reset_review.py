from src.common.lineage import reject_sensitive
from src.workbench.reset_review import inventory_view


def test_inventory_displays_mlflow_credential_table_names_without_values():
    inventory={"databases":{"mlflow_db":{"gateway_secrets":{"count":0,"digest":"empty"}}}}
    view=inventory_view(inventory)
    reject_sensitive(view)
    assert view["databases"]["mlflow_db"]==[{"table":"gateway_secrets","count":0,"digest":"empty"}]
    assert isinstance(inventory["databases"]["mlflow_db"],dict)
