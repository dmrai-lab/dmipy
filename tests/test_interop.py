"""Ecosystem integration: the three dmipy engines, at the versions ``pip install dmipy`` resolves,
interoperate on one shared acquisition.

This is the umbrella's authoritative cross-package guarantee — the only place dmipy-design,
dmipy-sim and dmipy-fit are assembled and version-resolved together. Guards against interface
drift as the engines release independently.
"""
import warnings

import numpy as np
import pytest

pytest.importorskip("dmipy_design")
pytest.importorskip("dmipy_sim")
pytest.importorskip("dmipy_fit")

import dmipy_sim as ds
from dmipy_design import design_waveform_now
from dmipy_fit.core.acquisition_scheme import AcquisitionScheme
from dmipy_fit.core.modeling_framework import MultiCompartmentModel
from dmipy_fit.signal_models.gaussian_models import G1Ball


def _design():
    return design_waveform_now(1.0, G_max=0.08, slew_rate_max=200.0, TE=0.09,
                               n_t=100, n_restarts=3, seed=0)


def _multi_b_scheme(d, fracs):
    """One design → a multi-b AcquisitionScheme by scaling amplitude (b ∝ |G|²). The effective
    (sign-folded) gradient with echo_idx at the end is the convention shared by both engines
    (matching NowDesign.to_sim_waveform); sim.simulate accepts this fit scheme directly."""
    Geff = np.asarray(d.effective_G())
    G = np.stack([Geff * np.sqrt(f) for f in fracs]).astype(np.float32)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return AcquisitionScheme.from_btensor_waveform(
            G, d.dt, echo_idx=Geff.shape[0] - 1, allow_offcenter_180=True)


def test_design_b_matches_sim():
    """dmipy-design's reported b == dmipy-sim's computed b for the same waveform (no drift)."""
    d = _design()
    b_sim = float(np.asarray(ds.calc_b(d.to_sim_waveform())).ravel()[0])
    assert abs(b_sim - d.b_value) / d.b_value < 1e-3


def test_sim_reproduces_stejskal_tanner():
    """dmipy-sim eats the designed pulse and returns exp(-b·D) for free diffusion."""
    d = _design()
    D = 1.7e-9
    S = float(np.asarray(ds.simulate(50_000, D, d.to_sim_waveform(), ds.FreeDiffusion(),
                                     seed=0, require_gpu=False)).ravel()[0])
    assert abs(S - np.exp(-d.b_value * D)) < 0.02


def test_full_loop_recovers_diffusivity():
    """design → one shared scheme → dmipy-sim simulates → dmipy-fit recovers D end-to-end."""
    d = _design()
    scheme = _multi_b_scheme(d, np.array([0.0, 0.3, 0.6, 1.0]))
    D_true = 1.7e-9
    sig = np.asarray(ds.simulate(60_000, D_true, scheme, ds.FreeDiffusion(),
                                 seed=0, require_gpu=False)).ravel()
    fit = MultiCompartmentModel([G1Ball()]).fit(scheme, sig[None, :], solver="brute2fine")
    D_fit = float(np.asarray(fit.fitted_parameters["G1Ball_1_lambda_iso"]).ravel()[0])
    assert abs(D_fit - D_true) / D_true < 0.05
