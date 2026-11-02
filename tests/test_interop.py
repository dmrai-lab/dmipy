"""Ecosystem integration: the dmipy packages, at the versions ``pip install dmipy`` resolves,
interoperate on one shared acquisition.

This is the umbrella's authoritative cross-package guarantee -- the only place dmipy-design,
dmipy-sim, dmipy-replay and dmipy-fit are assembled and version-resolved together. Guards against
interface drift as the packages release independently.

One design (dmipy-design) is one acquisition object (dmipy-replay's ``ScannerSequence``): its b is
``seq.b()``, dmipy-sim simulates it, and dmipy-fit wraps it as a scheme and fits the simulated signal.
"""
import numpy as np
import pytest

pytest.importorskip("dmipy_design")
pytest.importorskip("dmipy_replay")
pytest.importorskip("dmipy_sim")
pytest.importorskip("dmipy_fit")

import dmipy_sim as ds
from dmipy_design import ScannerLimits, design_waveform_now
from dmipy_fit.core.acquisition_scheme import AcquisitionScheme
from dmipy_fit.core.modeling_framework import MultiCompartmentModel
from dmipy_fit.signal_models.gaussian_models import G1Ball
from dmipy_replay.sequences import from_btensor_waveform


def _design():
    return design_waveform_now(1.0, limits=ScannerLimits.of("siemens_prisma"), TE=0.09,
                               n_t=100, n_restarts=3, seed=0)


def _multi_b_scheme(d, fracs):
    """One design -> a multi-b AcquisitionScheme by scaling amplitude (b ~ |G|^2): the designed physical
    gradient at every fraction, as one ScannerSequence with n_meas rows (dmipy-replay's builder), wrapped by
    dmipy-fit's scheme. dmipy-sim simulates this fit scheme directly."""
    G = np.stack([np.asarray(d.G) * np.sqrt(f) for f in fracs]).astype(np.float32)
    return AcquisitionScheme(from_btensor_waveform(G, d.dt, echo_idx=d.echo_idx, timing=d.timing))


def test_design_b_matches_sequence():
    """The b-value dmipy-design reports is the b of the sequence it returns (``seq.b()``), and the trace of the
    sequence's b-tensor (``seq.btensor()``): no drift between the designer and the acquisition object."""
    d = _design()
    seq = d.to_sequence()
    b_seq = float(np.asarray(seq.b()).ravel()[0])
    assert abs(b_seq - d.b_value) / d.b_value < 1e-3
    assert abs(float(np.trace(np.asarray(seq.btensor())[0])) - b_seq) / b_seq < 1e-6


def test_sim_reproduces_stejskal_tanner():
    """dmipy-sim eats the designed sequence and returns exp(-b D) for free diffusion."""
    d = _design()
    D = 1.7e-9
    S = float(np.asarray(ds.simulate(50_000, D, d.to_sequence(), ds.FreeDiffusion(),
                                     seed=0, require_gpu=False)).ravel()[0])
    assert abs(S - np.exp(-d.b_value * D)) < 0.02


def test_full_loop_recovers_diffusivity():
    """design -> one shared scheme -> dmipy-sim simulates -> dmipy-fit recovers D end-to-end."""
    d = _design()
    scheme = _multi_b_scheme(d, np.array([0.0, 0.3, 0.6, 1.0]))
    D_true = 1.7e-9
    sig = np.asarray(ds.simulate(60_000, D_true, scheme, ds.FreeDiffusion(),
                                 seed=0, require_gpu=False)).ravel()
    fit = MultiCompartmentModel([G1Ball()]).fit(scheme, sig[None, :], solver="brute2fine")
    D_fit = float(np.asarray(fit.fitted_parameters["G1Ball_1_lambda_iso"]).ravel()[0])
    assert abs(D_fit - D_true) / D_true < 0.05
