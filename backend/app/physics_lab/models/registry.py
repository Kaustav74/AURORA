"""
AURORA Physics Lab - Model Registry Manager
Loads equation provenance metadata and instantiates verified physics models.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Type
from app.physics_lab.models.newtonian import NewtonianModel
from app.physics_lab.models.ramanujan_pseries import RamanujanPSeriesOpeningModel
from app.physics_lab.models.schwarzschild import SchwarzschildRelativisticModel
from app.physics_lab.models.perturbations import GeneralizedKernelPerturbationModel
from app.physics_lab.models.regularized_compact import (
    HurwitzMassScaledModel,
    RegularizedUVCutoffModel,
    ScreenedNonlocalModel,
)

REGISTRY_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "physics_lab" / "EQUATION_REGISTRY.json"

MODEL_CLASS_MAP: Dict[str, Type[BasePhysicsModel]] = {
    "MODEL-A-NEWTONIAN": NewtonianModel,
    "MODEL-B-RAMANUJAN-PSERIES-OPENING": RamanujanPSeriesOpeningModel,
    "MODEL-C-KERNEL-PERTURBATION": GeneralizedKernelPerturbationModel,
    "MODEL-D1-HURWITZ-MASS-SCALED": HurwitzMassScaledModel,
    "MODEL-D2-REGULARIZED-UV-CUTOFF": RegularizedUVCutoffModel,
    "MODEL-D3-SCREENED-NONLOCAL": ScreenedNonlocalModel,
    "MODEL-E-RELATIVISTIC-SCHWARZSCHILD": SchwarzschildRelativisticModel,
}


class PhysicsModelRegistry:
    """
    Central registry for inspecting and instantiating gravitational models.
    """

    @classmethod
    def load_registry_metadata(cls) -> Dict[str, Any]:
        if not REGISTRY_PATH.exists():
            return {"models": []}
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        meta = cls.load_registry_metadata()
        return meta.get("models", [])

    @classmethod
    def get_model_metadata(cls, model_id: str) -> Optional[Dict[str, Any]]:
        for m in cls.list_models():
            if m.get("model_id") == model_id:
                return m
        return None

    @classmethod
    def create_model_instance(cls, model_id: str, parameters: Optional[Dict[str, Any]] = None) -> BasePhysicsModel:
        if model_id not in MODEL_CLASS_MAP:
            raise KeyError(
                f"Model '{model_id}' is not yet implemented or registered in factory. "
                f"Available implemented models: {list(MODEL_CLASS_MAP.keys())}"
            )
        model_cls = MODEL_CLASS_MAP[model_id]
        return model_cls(parameters=parameters)
