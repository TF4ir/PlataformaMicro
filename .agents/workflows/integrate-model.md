# Workflow: Integrate Model

## 1. Objective & Scope
Protocol for promoting, packaging, and wiring an offline-trained predictive retention model from `ml/` to online inference serving in `services/ml-api/`.

## 2. Promotion Steps

### Step 1: Metric Verification & Baseline Audit
- Confirm candidate model (DAS3H) meets minimum quality criteria:
  - $\text{AUC-ROC} \ge 0.75$
  - $\text{Brier Score} \le 0.18$
  - $\text{Expected Calibration Error (ECE)} \le 0.08$
- Verify statistical superiority over baselines (PFA and BKT) using Wilcoxon signed-rank test ($p < 0.05$).

### Step 2: Artifact Validation & Lineage
- Verify that `ml/artifacts/<model_name>_v<semver>/` contains:
  - `model.pkl` / `weights.json`: Frozen model parameters.
  - `feature_config.json`: Feature window definitions.
  - `metadata.json`: Complete metadata with SemVer, git commit hash, dependencies, and metrics.

### Step 3: Serving Wrapper Implementation
- Implement or update the inference engine under `services/ml-api/app/prediction/` adhering to the `BaseRetentionModel` abstract base class:
  ```python
  class BaseRetentionModel(ABC):
      @abstractmethod
      def predict_retention(self, student_features: Dict[str, Any], horizons: List[int]) -> PredictionOutput:
          pass
  ```

### Step 4: Fallback & Cold-Start Testing
- Validate that the inference endpoint returns `prediction_status: "insufficient_history"` when student history has $< 3$ attempts.
- Verify that adaptation layer automatically degrades to `rule_based_fallback`.
- Run warmup probe (`POST /api/v1/health/warmup`) and verify model pre-loading within acceptable memory footprint.

### Step 5: Latency & Performance Benchmarks
- Confirm inference latency on warmed container is $< 100\text{ms}$ at 95th percentile.

## 3. Definition of Done
- Model artifact versioned, signed with metadata, and loaded in FastAPI.
- Unit and integration tests verify both valid predictions and fallback paths.
