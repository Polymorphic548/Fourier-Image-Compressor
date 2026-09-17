"""Fourier compression engine.

The compression rule follows the reference project's method:
2-D FFT -> magnitude percentile threshold -> zero weak coefficients.
The implementation here is independently written.
"""
import numpy as np
from PIL import Image


def next_power_of_two(n):
    return 1 if n <= 1 else 1 << (int(n) - 1).bit_length()


def prepare_image(image, power_of_two=True):
    gray = image.convert("L")
    original_size = gray.size
    if power_of_two:
        target = (next_power_of_two(gray.width), next_power_of_two(gray.height))
        if target != gray.size:
            gray = gray.resize(target, Image.Resampling.BILINEAR)
    return np.asarray(gray, dtype=np.float64), original_size


def fft2d(image_array):
    # Fast, numerically reliable production path.
    return np.fft.fft2(np.asarray(image_array, dtype=np.float64))


def compress_spectrum(spectrum, percentile):
    p = float(np.clip(percentile, 0.0, 99.9))
    if p == 0:
        filtered = spectrum.copy()
        cutoff = 0.0
    else:
        cutoff = float(np.percentile(np.abs(spectrum), p))
        filtered = spectrum.copy()
        filtered[np.abs(filtered) < cutoff] = 0
    nnz = int(np.count_nonzero(filtered))
    return filtered, cutoff, nnz / filtered.size


def reconstruct(spectrum, original_size=None):
    spatial = np.real(np.fft.ifft2(spectrum))
    arr = np.clip(spatial, 0, 255).astype(np.uint8)
    image = Image.fromarray(arr, "L")
    if original_size and image.size != tuple(original_size):
        image = image.resize(tuple(original_size), Image.Resampling.BILINEAR)
    return image


def spectrum_preview(spectrum):
    mag = np.log1p(np.abs(np.fft.fftshift(spectrum)))
    mag -= mag.min()
    if mag.max() > 0:
        mag /= mag.max()
    return np.clip(mag * 255, 0, 255).astype(np.uint8)


# Educational routines: same mathematical family as the reference project.
def naive_dft(x):
    x = np.asarray(x, dtype=np.complex128)
    n = x.size
    k = np.arange(n).reshape(-1, 1)
    j = np.arange(n)
    return np.exp(-2j * np.pi * k * j / n) @ x


def cooley_tukey_fft(x):
    x = np.asarray(x, dtype=np.complex128)
    n = x.size
    if n <= 32:
        return naive_dft(x)
    if n & (n - 1):
        raise ValueError("Radix-2 FFT requires a power-of-two length.")
    even = cooley_tukey_fft(x[::2])
    odd = cooley_tukey_fft(x[1::2])
    twiddle = np.exp(-2j * np.pi * np.arange(n // 2) / n) * odd
    return np.concatenate((even + twiddle, even - twiddle))


def educational_fft2d(a):
    a = np.asarray(a, dtype=np.complex128)
    h, w = a.shape
    if (h & (h - 1)) or (w & (w - 1)):
        raise ValueError("Both dimensions must be powers of two.")
    rows = np.apply_along_axis(cooley_tukey_fft, 1, a)
    return np.apply_along_axis(cooley_tukey_fft, 0, rows)
