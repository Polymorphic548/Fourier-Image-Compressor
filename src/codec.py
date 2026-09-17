"""Sparse CSR/NPZ storage for Fourier coefficients."""
from pathlib import Path
import json, os
import numpy as np
from scipy import sparse


def save_npz_bundle(path, spectrum, metadata):
    path = Path(path)
    if path.suffix.lower() != ".npz":
        path = path.with_suffix(".npz")
    sparse.save_npz(path, sparse.csr_matrix(spectrum), compressed=True)
    sidecar = path.with_suffix(".json")
    sidecar.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return path, sidecar


def load_npz_bundle(path):
    path = Path(path)
    matrix = sparse.load_npz(path)
    metadata = {}
    sidecar = path.with_suffix(".json")
    if sidecar.exists():
        metadata = json.loads(sidecar.read_text(encoding="utf-8"))
    return matrix.toarray(), metadata


def bundle_size(path):
    path = Path(path)
    size = os.path.getsize(path)
    sidecar = path.with_suffix(".json")
    if sidecar.exists():
        size += os.path.getsize(sidecar)
    return size
