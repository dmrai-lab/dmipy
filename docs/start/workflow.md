# The workflow, end to end

dmipy-sim walks a substrate once and stores the walk as a replay pack; dmipy-replay answers any acquisition on it,
from a file or by range from the Hub. The steps below run in seconds on a laptop CPU.

## 1. Produce a pack (dmipy-sim)

The substrate is written out as a spec, and the pack is certified for an envelope: here a Siemens Prisma's band and
gradient amplitude, at 3 T, with surface relaxivity up to 100 µm/s.

```python
import os, tempfile
import numpy as np
from dmipy_sim import Cylinder, build_replay_pack, walk
from dmipy_sim.replay.container import save_pack
from dmipy_replay import envelope_of

spec = Cylinder(radius=3e-6, orientation=(0, 0, 1)).spec              # the substrate, as a spec
env = envelope_of("siemens_prisma", B0_list=(3.0,), rho2_max=1e-4)    # what the pack is certified for
w = walk(spec, 2000, T_max=0.05, envelope=env, diffusivity=2e-9, seed=0, require_gpu=False)
pack = build_replay_pack(w, id="docs/cylinder-3um", license="CC-BY-4.0", citation="dmipy.org")
path = os.path.join(tempfile.mkdtemp(), "cylinder.rpk")
save_pack(pack, path)
print(f"{env.name}: {env.band_hz:.0f} Hz, G_max {env.G_max * 1e3:.0f} mT/m; {pack.K} bands, {pack.n_walkers} walkers")
```

## 2. Replay it (dmipy-replay)

Load the file and play a PGSE across and along the cylinder. The same walk turned so that its axis lies along x
swaps the two measurements: the pose is a replay knob, not a second walk.

```python
from dmipy_replay import ReplayPack, sequences

p = ReplayPack.load(path)
seq = sequences.pgse([[1, 0, 0], [0, 0, 1]], 0.01, 0.03, bvalues=[1e9, 1e9])    # across, along
print(np.round(p.replay(seq), 3))                                     # restricted across, free along
print(np.round(p.replay(seq, orientation=(1, 0, 0)), 3))              # the axis along x: the two swap
```

## 3. The pulses as played (vector Bloch)

`replay_bloch` carries every walker's magnetisation through the sequence's own pulses: a transmit field at 90 %
of nominal, or a CPMG train with the tissue's T2, whose echoes decay as `exp(-t / T2)`.

```python
from dmipy_replay import Tissue

print(np.round(np.abs(p.replay_bloch(seq, b1_scale=0.9)), 3))       # the flips at 90 % of nominal
train = sequences.cpmg(6, 0.006)                                       # six echoes, 6 ms apart
wm = Tissue(T2={"extra": 0.06, "intra": 0.06})                         # a T2 for every pool of the spec
print(np.round(np.abs(p.replay_bloch(train, tissue=wm)).ravel(), 3))
print(np.round(np.exp(-0.006 * np.arange(1, 7) / 0.06), 3))
```

The [vector-Bloch route](../replay/bloch.md) has the B1 law, the crushers of a train and the field offset.

## 4. The envelope is enforced

A pack answers what its band holds. A cosine OGSE at 1.5 kHz needs a band the Prisma pack does not store, and the
replay refuses it by name rather than returning a number:

```python
fast = sequences.ogse([[1, 0, 0]], 1500.0, 2e-3, shape="cosine", Delta=3e-3, bvalues=[1e9], TE=10e-3,
                      slew_rate=np.inf)
try:
    p.replay(fast)
except ValueError as e:
    print("refused:", str(e)[:100])
```

## 5. A published pack, by reference

A pack of [SubstrateCommons](https://huggingface.co/SubstrateCommons) opens on the Hub where it is, here a bundle of
CACTUS axons. The plan says which bands an acquisition needs and how many bytes that is; the replay reads those
ranges and no others. The bundle runs along its own x, and the pose turns it to the lab's z:

```python
r = ReplayPack.open("hf://SubstrateCommons/cactus-axons/packs/cactus_bundle00000_100ms.rpk")
print(r.id, r.n_walkers, "walkers")
print(r.plan(seq))                                                     # the bands and the bytes before any read
print(np.round(r.replay(seq, orientation=(0, 0, 1)), 3))               # the bundle's axis turned to z: across, along
```

## Then

- [The replay guide](../replay/index.md): every object (pack, sequence, tissue, scanner, orientation) and every knob.
- [Fit](../fit.md) a model to what a pack replays, on the same `ScannerSequence`.
- [Design](../design.md) the sequence under a scanner's limits, and replay the design.
