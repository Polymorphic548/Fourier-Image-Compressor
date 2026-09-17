import numpy as np
from src.engine import cooley_tukey_fft, educational_fft2d, fft2d, compress_spectrum, reconstruct

def test_fft1_matches_numpy():
    rng=np.random.default_rng(1); x=rng.normal(size=64)
    assert np.allclose(cooley_tukey_fft(x),np.fft.fft(x),atol=1e-9)

def test_fft2_matches_numpy():
    rng=np.random.default_rng(2); x=rng.normal(size=(8,8))
    assert np.allclose(educational_fft2d(x),np.fft.fft2(x),atol=1e-9)

def test_zero_threshold_roundtrip():
    rng=np.random.default_rng(3); x=rng.integers(0,256,size=(32,32),dtype=np.uint8)
    f=fft2d(x); g,_,r=compress_spectrum(f,0)
    y=np.asarray(reconstruct(g))
    assert np.array_equal(x,y)
    assert r==1.0

def test_75_percentile_is_sparse():
    rng=np.random.default_rng(4); x=rng.normal(size=(64,64))
    f=fft2d(x); g,_,r=compress_spectrum(f,75)
    assert 0.20 <= r <= 0.30
