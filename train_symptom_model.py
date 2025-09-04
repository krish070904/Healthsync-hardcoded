# train_symptom_model.py
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# create toy data: symptoms -> label (0: none,1:flu-like,2:food-intolerance)
rng = np.random.RandomState(0)
N = 1000
feats = []
labels = []
for _ in range(N):
    fever = rng.binomial(1,0.15)
    nausea = rng.binomial(1,0.10)
    bloating = rng.binomial(1,0.08)
    headache = rng.binomial(1,0.12)
    if fever and headache:
        lab = 1
    elif bloating or nausea:
        lab = 2
    else:
        lab = 0
    feats.append([fever, nausea, bloating, headache])
    labels.append(lab)

X = pd.DataFrame(feats, columns=['fever','nausea','bloating','headache'])
y = pd.Series(labels)
clf = RandomForestClassifier(n_estimators=50, random_state=0)
clf.fit(X,y)
joblib.dump(clf, "models/symptom_model.joblib")
print("trained model saved to models/symptom_model.joblib")
