import numpy as np
import pandas as pd
import pytest
from src.academic.estimator import AcademicComponents
from src.operations.academic_generation import compose


def test_regular_predictions_independent_of_discipline_extras():
    frame=pd.DataFrame(dict(semester_index=[0.,1.,2.,3.],period=[2.]*4,
        lag_regular=[30.,35.,32.,40.],lag_dependency=[1.,7.,3.,9.],lag_elective=[0.,2.,4.,6.]))
    labels=pd.DataFrame(dict(regular=[31,34,33,38],dependency=[2,5,4,8],elective=[1,1,5,7]))
    model=AcademicComponents().fit(frame,labels)
    sample=pd.concat([frame.tail(1)]*2,ignore_index=True)
    sample.loc[1,'lag_dependency']=70
    sample.loc[1,'lag_elective']=50
    prediction=model.predict(sample)
    assert prediction[0,0]==prediction[1,0]
    assert prediction[0,1]!=prediction[1,1]
    assert np.isfinite(prediction).all()


def test_composition_rejects_cohort_regular_disagreement():
    import json
    from pathlib import Path
    manifest=json.loads(Path('artifacts/reports/v4/scenario-manifest.json').read_text(encoding='utf-8'))
    predictions={o['offer_id']:dict(values=[30+i,2.,1.],cohort_id='same',cohort_ingress='2023-1',usage={'inference_id':'id'})
                 for i,o in enumerate(manifest['offers'][:2])}
    with pytest.raises(ValueError,match='identical'):
        compose(manifest,predictions,'proposal','correlation',1)
