"""Three disjoint DEMO demand components; regular demand cannot see discipline extras."""
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.dummy import DummyRegressor

REGULAR_FEATURES = ['semester_index', 'period', 'lag_regular']


class AcademicComponents(RegressorMixin, BaseEstimator):
    def __init__(self, algorithm='ridge', alpha=1.):
        self.algorithm = algorithm
        self.alpha = alpha

    def fit(self, X, y):
        self.models_ = []
        for target in ('regular', 'dependency', 'elective'):
            columns = REGULAR_FEATURES if target == 'regular' else list(X.columns)
            data = X[columns].copy()
            data['_target'] = y[target].to_numpy()
            # Regular examples are cohort-level, not duplicated for every discipline.
            if target == 'regular':
                data = data.drop_duplicates()
            regressor = DummyRegressor(strategy='mean') if self.algorithm == 'dummy' else Ridge(alpha=self.alpha)
            model = make_pipeline(StandardScaler(), regressor)
            model.fit(data[columns], data['_target'])
            self.models_.append((columns, model))
        self.n_features_in_ = X.shape[1]
        self.feature_names_in_ = np.asarray(X.columns, dtype=object)
        return self

    def predict(self, X):
        return np.column_stack([model.predict(X[columns]) for columns, model in self.models_])
