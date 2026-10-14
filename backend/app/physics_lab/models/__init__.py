"""
AURORA Physics Lab - Models Package
"""

from app.physics_lab.models.base import BasePhysicsModel
from app.physics_lab.models.newtonian import NewtonianModel
from app.physics_lab.models.ramanujan_pseries import RamanujanPSeriesOpeningModel
from app.physics_lab.models.schwarzschild import SchwarzschildRelativisticModel
from app.physics_lab.models.perturbations import GeneralizedKernelPerturbationModel
from app.physics_lab.models.regularized_compact import (
    HurwitzMassScaledModel,
    RegularizedUVCutoffModel,
    ScreenedNonlocalModel,
)
from app.physics_lab.models.registry import PhysicsModelRegistry

__all__ = [
    "BasePhysicsModel",
    "NewtonianModel",
    "RamanujanPSeriesOpeningModel",
    "SchwarzschildRelativisticModel",
    "GeneralizedKernelPerturbationModel",
    "HurwitzMassScaledModel",
    "RegularizedUVCutoffModel",
    "ScreenedNonlocalModel",
    "PhysicsModelRegistry",
]
