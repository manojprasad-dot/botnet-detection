# KOVIRX AI Engine

Enterprise ML detection pipeline for botnet detection with explainability.

## Architecture

```
ai-engine/
├── models/                  # Model wrappers (uses existing ml/models/)
├── prediction/              # Inference pipeline
│   ├── behavior_scorer.py   # Behavior-aware scoring
│   └── (hybrid_detector.py) # → ml/hybrid_detector.py
│
├── training/                # Training pipeline (→ ml/train_*.py)
├── feature_store/           # Feature management
│   └── normalizer.py        # Feature normalization
│
├── explainability/          # Model interpretability
│   └── feature_importance.py # SHAP + magnitude analysis
│
└── saved_models/            # Trained artifacts (→ ml/saved_models/)
```

## Detection Pipeline

```
Features → Normalize → XGBoost → Isolation Forest → Behavior Scorer → Risk Score
```

## Multi-Source Risk Integration

| Source          | Weight | Module                    |
|-----------------|--------|---------------------------|
| ML Score        | 40%    | XGBoost + Isolation Forest |
| IOC Match       | 25%    | Threat Intel Service       |
| Behavior Score  | 25%    | BehaviorScorer             |
| History Score   | 10%    | Risk Engine (server-side)  |

## Note

The existing `ml/` directory is preserved for backward compatibility.
The `ai-engine/` directory extends it with new prediction, feature store,
and explainability capabilities. Migration from `ml/` to `ai-engine/`
happens incrementally as components are rewritten.
