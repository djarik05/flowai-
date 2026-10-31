"""
Training Engine for GestureFlow AI Static Gesture Classifier.

Orchestrates:
- Dataset sample loading and validation
- Feature extraction via FeaturePreprocessor
- Session-aware train/val/test splitting to prevent data leakage
- Background model training execution with real-time epoch tracking
- Independent test set evaluation with confusion matrix & per-class metrics
- Versioned model artifact creation & registry indexing
"""

import json
import logging
import math
import os
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split

from app.schemas.classifier import (
    ClassEvaluationMetric,
    EvaluationMetrics,
    ModelMetadata,
    TrainingConfigRequest,
    TrainingJobStatus,
    TrainingMetricItem,
)
from app.services.dataset_service import DatasetService
from app.services.feature_engineering import FeaturePreprocessor
from app.services.gesture_service import GestureService
from app.services.mlp_classifier import MLPClassifierModel
from app.services.model_registry import ModelRegistryService

logger = logging.getLogger(__name__)


class TrainingEngine:
    """Manages dataset preparation, training jobs, and model evaluation."""

    def __init__(
        self,
        dataset_service: Optional[DatasetService] = None,
        gesture_service: Optional[GestureService] = None,
        registry_service: Optional[ModelRegistryService] = None,
    ):
        self._dataset_service = dataset_service or DatasetService()
        self._gesture_service = gesture_service or GestureService()
        self._registry_service = registry_service or ModelRegistryService()
        self._jobs: Dict[str, TrainingJobStatus] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._lock = threading.RLock()

    def get_job_status(self, job_id: str) -> Optional[TrainingJobStatus]:
        """Query live progress or final status of a training job."""
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> List[TrainingJobStatus]:
        """List all recent training jobs."""
        with self._lock:
            return list(self._jobs.values())

    def start_training_job(
        self,
        config: TrainingConfigRequest,
        background: bool = True,
    ) -> TrainingJobStatus:
        """
        Validate dataset, create job, and start training.
        Returns initial TrainingJobStatus.
        """
        job_id = f"job_train_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        status = TrainingJobStatus(
            job_id=job_id,
            status="pending",
            current_epoch=0,
            total_epochs=config.epochs,
            progress_percent=0.0,
            started_at=datetime.now().isoformat(),
            logs=[f"Training job {job_id} initialized."],
        )

        with self._lock:
            self._jobs[job_id] = status

        if background:
            thread = threading.Thread(
                target=self._run_training_job,
                args=(job_id, config),
                name=f"TrainWorker-{job_id[:12]}",
                daemon=True,
            )
            self._threads[job_id] = thread
            thread.start()
        else:
            self._run_training_job(job_id, config)

        return status

    def _run_training_job(self, job_id: str, config: TrainingConfigRequest) -> None:
        """Background execution worker for training pipeline."""
        with self._lock:
            status = self._jobs[job_id]
            status.status = "training"
            status.logs.append("Preparing dataset and extracting features...")

        try:
            # 1. Determine target gesture classes
            all_gestures = {g.id: g.name for g in self._gesture_service.get_all()}
            target_ids = config.gesture_ids

            if not target_ids:
                # Default to all gestures that have >= 5 samples
                target_ids = [
                    gid for gid, name in all_gestures.items()
                    if (self._dataset_service.samples_dir / gid).exists()
                    and len(list((self._dataset_service.samples_dir / gid).glob("*.json"))) >= 5
                ]

            if len(target_ids) < 2:
                raise ValueError(
                    f"At least 2 gesture classes with >= 5 samples required for training. "
                    f"Selected classes: {target_ids}"
                )

            class_mapping = {gid: idx for idx, gid in enumerate(sorted(target_ids))}
            classes_meta = [{"id": gid, "name": all_gestures.get(gid, gid)} for gid in sorted(target_ids)]

            with self._lock:
                status.logs.append(
                    f"Target classes ({len(target_ids)}): {', '.join(f'{g['name']} ({g['id']})' for g in classes_meta)}"
                )

            # 2. Load samples & extract 63-dim features
            preprocessor = FeaturePreprocessor(mode="3d", scale_normalized=True, wrist_relative=True)
            X_all: List[np.ndarray] = []
            y_all: List[int] = []
            sessions_all: List[str] = []

            for gid in target_ids:
                g_dir = self._dataset_service.samples_dir / gid
                if not g_dir.exists():
                    continue

                for f_path in g_dir.glob("*.json"):
                    try:
                        with open(f_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        lms = data.get("landmarks", [])
                        feat = preprocessor.transform(lms)
                        X_all.append(feat)
                        y_all.append(class_mapping[gid])
                        sessions_all.append(data.get("session_id", "default_session"))
                    except Exception:
                        continue

            if len(X_all) < 10:
                raise ValueError(f"Insufficient total valid samples ({len(X_all)}). Need at least 10 across classes.")

            X = np.array(X_all, dtype=np.float32)
            y = np.array(y_all, dtype=np.int64)

            with self._lock:
                status.logs.append(
                    f"Extracted {len(X)} valid samples. Feature dimension: {X.shape[1]}."
                )

            # 3. Train / Validation / Test Splitting
            X_train, y_train, X_val, y_val, X_test, y_test = self._split_dataset(
                X, y, sessions_all, config
            )

            with self._lock:
                status.logs.append(
                    f"Dataset split: Train={len(X_train)}, Val={len(X_val)}, Test={len(X_test)}."
                )

            # 4. Initialize MLP Architecture
            model = MLPClassifierModel(
                input_dim=preprocessor.feature_dim,
                hidden_layers=config.hidden_layers,
                dropout_rates=config.dropout_rates,
                num_classes=len(target_ids),
                class_mapping=class_mapping,
            )

            # 5. Training Loop
            metrics_history: List[TrainingMetricItem] = []

            for epoch in range(1, config.epochs + 1):
                train_loss, train_acc = model.train_epoch(
                    X_train,
                    y_train,
                    batch_size=config.batch_size,
                    lr=config.learning_rate,
                )

                val_loss, val_acc = model.compute_loss_and_acc(X_val, y_val)

                metric_item = TrainingMetricItem(
                    epoch=epoch,
                    train_loss=round(train_loss, 4),
                    val_loss=round(val_loss, 4),
                    train_accuracy=round(train_acc * 100.0, 2),
                    val_accuracy=round(val_acc * 100.0, 2),
                )
                metrics_history.append(metric_item)

                with self._lock:
                    status.current_epoch = epoch
                    status.progress_percent = round((epoch / config.epochs) * 100.0, 1)
                    status.latest_train_loss = metric_item.train_loss
                    status.latest_val_loss = metric_item.val_loss
                    status.latest_train_accuracy = metric_item.train_accuracy
                    status.latest_val_accuracy = metric_item.val_accuracy
                    status.metrics_history = metrics_history

                    if epoch % max(1, config.epochs // 10) == 0 or epoch == config.epochs:
                        status.logs.append(
                            f"Epoch {epoch:02d}/{config.epochs}: Train Loss={train_loss:.4f}, Val Acc={val_acc*100:.1f}%"
                        )

                # Cooperative sleep for thread responsiveness
                time.sleep(0.005)

            # 6. Independent Test Set Evaluation
            with self._lock:
                status.logs.append("Evaluating model on independent test dataset...")

            eval_metrics = self._evaluate_model(model, X_test, y_test, sorted(target_ids), all_gestures)

            with self._lock:
                status.logs.append(
                    f"Final Test Evaluation: Accuracy={eval_metrics.accuracy*100:.1f}%, F1={eval_metrics.f1_macro:.3f}"
                )

            # 7. Model Serialization & Registration
            model_id = f"model_mlp_{int(time.time())}_{uuid.uuid4().hex[:4]}"
            model_dir = self._registry_service.registry_dir / model_id
            model_dir.mkdir(parents=True, exist_ok=True)
            weights_file = model_dir / "weights.npz"
            model.save(weights_file)

            metadata = ModelMetadata(
                model_id=model_id,
                model_name=config.model_name,
                version="1.0.0",
                created_at=datetime.now().isoformat(),
                dataset_version=f"ds_{int(time.time())}",
                classes=classes_meta,
                feature_schema="landmarks_3d_wrist_relative_scale_normalized",
                feature_dim=63,
                preprocessing_config=preprocessor.get_config(),
                training_config=config.model_dump(),
                metrics=eval_metrics,
                model_file=str(weights_file.resolve()),
                is_active=True,
            )

            # Save model.json inside model directory
            with open(model_dir / "model.json", "w", encoding="utf-8") as f:
                json.dump(metadata.model_dump(), f, indent=2)

            self._registry_service.register_model(metadata, activate=True)

            with self._lock:
                status.status = "completed"
                status.created_model_id = model_id
                status.completed_at = datetime.now().isoformat()
                status.logs.append(f"Model successfully saved & activated: {model_id}")

        except Exception as e:
            logger.error("Error in training worker: %s", e, exc_info=True)
            with self._lock:
                status.status = "failed"
                status.error = str(e)
                status.logs.append(f"Training failed with error: {e}")

    def _split_dataset(
        self,
        X: np.ndarray,
        y: np.ndarray,
        sessions: List[str],
        config: TrainingConfigRequest,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Perform train/validation/test split with session-aware leakage prevention.
        """
        n_samples = len(X)
        test_ratio = config.test_split
        val_ratio = config.val_split / (1.0 - test_ratio)

        # Check if session-aware split is valid (each class must have >= 3 distinct sessions)
        can_session_split = False
        if config.session_aware_split:
            classes = np.unique(y)
            sessions_per_class = {c: set() for c in classes}
            for cls, s in zip(y, sessions):
                sessions_per_class[cls].add(s)
            if all(len(s_set) >= 3 for s_set in sessions_per_class.values()):
                can_session_split = True

        if can_session_split:
            # Partition sessions within each class to preserve all classes in train/val/test
            train_mask = np.zeros(n_samples, dtype=bool)
            val_mask = np.zeros(n_samples, dtype=bool)
            test_mask = np.zeros(n_samples, dtype=bool)

            for c in np.unique(y):
                c_indices = np.where(y == c)[0]
                c_sessions = list({sessions[i] for i in c_indices})
                np.random.shuffle(c_sessions)
                n_s = len(c_sessions)
                n_test = max(1, int(round(n_s * test_ratio)))
                n_val = max(1, int(round(n_s * config.val_split)))
                
                t_sess = set(c_sessions[:n_test])
                v_sess = set(c_sessions[n_test : n_test + n_val])
                tr_sess = set(c_sessions[n_test + n_val:])
                if not tr_sess:
                    tr_sess = v_sess

                for idx in c_indices:
                    s = sessions[idx]
                    if s in t_sess:
                        test_mask[idx] = True
                    elif s in v_sess:
                        val_mask[idx] = True
                    else:
                        train_mask[idx] = True

            if train_mask.sum() > 0 and val_mask.sum() > 0 and test_mask.sum() > 0:
                return X[train_mask], y[train_mask], X[val_mask], y[val_mask], X[test_mask], y[test_mask]

        if not can_session_split:
            # Stratified splitting by class label
            strat = y if min(np.bincount(y)) >= 2 else None
            X_temp, X_test, y_temp, y_test = train_test_split(
                X, y, test_size=test_ratio, stratify=strat, random_state=42
            )
            strat_temp = y_temp if min(np.bincount(y_temp)) >= 2 else None
            X_train, X_val, y_train, y_val = train_test_split(
                X_temp, y_temp, test_size=val_ratio, stratify=strat_temp, random_state=42
            )
            return X_train, y_train, X_val, y_val, X_test, y_test

        return X[train_mask], y[train_mask], X[val_mask], y[val_mask], X[test_mask], y[test_mask]

    def _evaluate_model(
        self,
        model: MLPClassifierModel,
        X_test: np.ndarray,
        y_test: np.ndarray,
        target_ids: List[str],
        all_gestures: Dict[str, str],
    ) -> EvaluationMetrics:
        """Compute standard metrics on independent test split."""
        y_pred = model.predict(X_test)
        acc = float(accuracy_score(y_test, y_pred))

        prec, rec, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average="macro", zero_division=0
        )

        p_class, r_class, f1_class, s_class = precision_recall_fscore_support(
            y_test, y_pred, average=None, labels=range(len(target_ids)), zero_division=0
        )

        cm = confusion_matrix(y_test, y_pred, labels=range(len(target_ids)))

        per_class_metrics: Dict[str, ClassEvaluationMetric] = {}
        for idx, gid in enumerate(target_ids):
            gname = all_gestures.get(gid, gid)
            per_class_metrics[gname] = ClassEvaluationMetric(
                precision=round(float(p_class[idx]), 3),
                recall=round(float(r_class[idx]), 3),
                f1_score=round(float(f1_class[idx]), 3),
                support=int(s_class[idx]),
            )

        class_names = [all_gestures.get(gid, gid) for gid in target_ids]

        return EvaluationMetrics(
            accuracy=round(acc, 4),
            precision_macro=round(float(prec), 4),
            recall_macro=round(float(rec), 4),
            f1_macro=round(float(f1), 4),
            confusion_matrix=cm.tolist(),
            class_labels=class_names,
            per_class=per_class_metrics,
            test_samples_count=len(y_test),
        )
