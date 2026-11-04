import json
import pytest
from src.common.lineage import canonical,sha256,reject_sensitive
from src.common.notebook_distribution import distribute


def test_canonical_hash():
    assert sha256({"b":1,"a":["é",None]})==sha256({"a":["é",None],"b":1})
    with pytest.raises(ValueError):
        canonical({"x":float("nan")})


@pytest.mark.parametrize("value",[{"nested":{"password":"x"}},{"uri":"postgresql://user:secret@host/db"},{"x":"Bearer abc"},{"AWS_ACCESS_KEY_ID":"hidden"}])
def test_sensitive_metadata(value):
    with pytest.raises(ValueError):
        reject_sensitive(value)


def test_distribution_preserves_edits(tmp_path):
    source=tmp_path/"source"; source.mkdir()
    workspace=tmp_path/"workspace"
    path=source/"01.ipynb"; path.write_text("original")
    distribute(source,workspace)
    (workspace/path.name).write_text("personal edit")
    path.write_text("new source")
    distribute(source,workspace)
    assert (workspace/path.name).read_text()=="personal edit"
    assert len(list(workspace.glob("*.update-*.ipynb")))==1
    distribute(source,workspace)
    assert len(list(workspace.glob("*.update-*.ipynb")))==1
