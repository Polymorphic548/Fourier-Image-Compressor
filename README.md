# Fourier Image Compressor

A desktop image-compression system that demonstrates how the **Discrete Fourier Transform (DFT)** and **Fast Fourier Transform (FFT)** can be used to represent, selectively remove, store, and reconstruct image information in the spatial-frequency domain.

The project was developed as a **Signals, Networks & Systems** application of Fourier analysis. Instead of directly modifying pixels, the image is transformed into a collection of spatial-frequency components. Fourier coefficients with relatively small magnitudes are discarded, while the strongest coefficients are retained and stored as a sparse matrix.

> **Note:** This is an educational Fourier-domain compression system intended to demonstrate signal-processing concepts. It is not designed to outperform mature image codecs such as JPEG, WebP, or AVIF.

---

## Overview

A digital image can be interpreted as a two-dimensional discrete signal:

$$
f(x,y)
$$

where:

- $x$ represents the horizontal spatial coordinate,
- $y$ represents the vertical spatial coordinate,
- $f(x,y)$ represents the intensity of the pixel at that position.

Instead of storing and processing the image purely in the spatial domain, the system transforms the image into the **frequency domain** using a two-dimensional Discrete Fourier Transform.

The compression pipeline is:

```text
Input Image
     │
     ▼
Convert to Grayscale
     │
     ▼
2-D Fast Fourier Transform
     │
     ▼
Complex Fourier Spectrum
     │
     ▼
Calculate Coefficient Magnitudes
     │
     ▼
Magnitude Percentile Threshold
     │
     ▼
Remove Weak Fourier Coefficients
     │
     ▼
Sparse Fourier Matrix
     │
     ▼
CSR Sparse Representation
     │
     ▼
Compressed NPZ File
     │
     ▼
Load Sparse Spectrum
     │
     ▼
Inverse 2-D Fourier Transform
     │
     ▼
Reconstructed Image
```

---

## Example

The following screenshot shows the application compressing a sample image using a high Fourier compression percentile.

![Fourier Image Compressor Example](samples/sample%201.png)

The interface displays:

- the original grayscale image,
- the reconstructed image,
- the percentage of Fourier coefficients retained,
- original file size,
- compressed NPZ size,
- compression ratio,
- percentage size reduction,
- Mean Squared Error (MSE),
- Peak Signal-to-Noise Ratio (PSNR).

---

# 1. Image as a Two-Dimensional Signal

The first step is to interpret the image as a discrete two-dimensional signal.

For an image having width $N$ and height $M$,

$$
f(x,y), \qquad
0 \leq x < N,\quad
0 \leq y < M
$$

represents the intensity of each pixel.

The current implementation converts the input image to **grayscale**, meaning that each spatial position contains one intensity value approximately between 0 and 255.

This also follows the compression approach used by the reference Fourier implementation and avoids requiring three independent RGB Fourier spectra.

---

# 2. Two-Dimensional Discrete Fourier Transform

The image is transformed from the spatial domain into the spatial-frequency domain using the **2-D Discrete Fourier Transform (DFT)**.

For an image of dimensions $M \times N$, the 2-D DFT is

$$
F(u,v)
=
\sum_{x=0}^{M-1}
\sum_{y=0}^{N-1}
f(x,y)
e^{-j2\pi
\left(
\frac{ux}{M}
+
\frac{vy}{N}
\right)}
$$

where:

- $f(x,y)$ is the original image,
- $F(u,v)$ is the Fourier coefficient,
- $u$ is the vertical spatial-frequency index,
- $v$ is the horizontal spatial-frequency index,
- $j=\sqrt{-1}$.

Each Fourier coefficient is generally a complex number:

$$
F(u,v)=a+jb
$$

where $a$ is the real component and $b$ is the imaginary component.

The same coefficient may alternatively be represented in magnitude-phase form:

$$
F(u,v)
=
|F(u,v)|e^{j\phi(u,v)}
$$

with magnitude

$$
|F(u,v)|
=
\sqrt{
\operatorname{Re}(F(u,v))^2
+
\operatorname{Im}(F(u,v))^2
}
$$

and phase

$$
\phi(u,v)
=
\operatorname{atan2}
\left(
\operatorname{Im}(F(u,v)),
\operatorname{Re}(F(u,v))
\right).
$$

Therefore, the Fourier transform represents the image as a combination of many spatial-frequency components having different magnitudes and phases.

---

# 3. Why FFT Is Used

Calculating the DFT directly is computationally expensive.

For a one-dimensional signal containing $N$ samples, direct DFT evaluation has approximately

$$
O(N^2)
$$

computational complexity.

The **Fast Fourier Transform (FFT)** is an efficient algorithm for computing the same DFT.

A radix-2 Cooley-Tukey FFT recursively separates a sequence into its even and odd indexed samples:

$$
X[k]
=
E[k]
+
W_N^k O[k]
$$

and

$$
X[k+N/2]
=
E[k]
-
W_N^k O[k]
$$

where

$$
W_N^k
=
e^{-j2\pi k/N}
$$

is the twiddle factor.

This reduces the typical computational complexity to approximately

$$
O(N\log N).
$$

For a two-dimensional image, the transform is separable. A 2-D Fourier transform can therefore be computed by:

1. performing a 1-D FFT across every row,
2. performing a 1-D FFT across every column of the result.

The application uses NumPy's optimized FFT implementation for practical image processing. An educational Cooley-Tukey implementation is also included in the source code to demonstrate the underlying FFT algorithm.

---

# 4. Fourier Magnitude Spectrum

After transformation, every Fourier coefficient has a magnitude

$$
A(u,v)=|F(u,v)|.
$$

Large-magnitude coefficients represent Fourier components that make a relatively strong contribution to the image.

Small-magnitude coefficients make weaker individual contributions.

The application can display the Fourier magnitude spectrum using logarithmic scaling:

$$
S(u,v)
=
\log\left(1+|F(u,v)|\right).
$$

Logarithmic scaling is useful because Fourier magnitudes can span a very large numerical range.

---

# 5. Fourier Coefficient Selection

The central compression operation is **magnitude percentile thresholding**.

Suppose the user selects a compression percentile $P$.

The program collects the magnitudes of all Fourier coefficients:

$$
\{|F(u,v)|\}
$$

and determines the $P$-th percentile:

$$
T
=
\operatorname{Percentile}
\left(
|F(u,v)|,P
\right).
$$

The value $T$ becomes the compression threshold.

The filtered spectrum is then defined as

$$
\hat{F}(u,v)
=
\begin{cases}
F(u,v), & |F(u,v)| \geq T \\[6pt]
0, & |F(u,v)| < T
\end{cases}
$$

Thus, Fourier coefficients having magnitudes below the selected threshold are removed.

---

## Compression Percentile

The slider represents the approximate fraction of Fourier coefficients being discarded.

| Compression Percentile | Approx. Coefficients Retained |
|---:|---:|
| 0% | 100% |
| 50% | 50% |
| 75% | 25% |
| 90% | 10% |
| 95% | 5% |
| 99% | 1% |
| 99.4% | 0.6% |
| 99.9% | 0.1% |

For example, at

$$
P=99.4\%
$$

approximately

$$
100-99.4=0.6\%
$$

of the strongest Fourier coefficients remain.

The exact number can differ slightly when multiple coefficients have equal magnitudes.

---

# 6. Why Removing Coefficients Compresses the Image

Before thresholding, the Fourier matrix is dense:

$$
\begin{bmatrix}
F_{00} & F_{01} & F_{02} & \cdots \\
F_{10} & F_{11} & F_{12} & \cdots \\
F_{20} & F_{21} & F_{22} & \cdots \\
\vdots & \vdots & \vdots & \ddots
\end{bmatrix}
$$

After aggressive magnitude thresholding, the matrix may become

$$
\begin{bmatrix}
F_{00} & 0 & 0 & \cdots \\
0 & F_{11} & 0 & \cdots \\
0 & 0 & 0 & \cdots \\
\vdots & \vdots & \vdots & \ddots
\end{bmatrix}.
$$

Most elements are now zero.

Storing every zero explicitly would waste space, so the program converts the Fourier matrix into a **sparse representation**.

---

# 7. CSR Sparse Matrix Storage

The program uses SciPy's **Compressed Sparse Row (CSR)** representation.

Instead of storing the entire dense Fourier matrix, CSR primarily stores:

1. the non-zero Fourier coefficients,
2. their column indices,
3. information describing where each matrix row begins.

Conceptually:

```text
Dense Fourier Matrix

[ A  0  0  B ]
[ 0  0  C  0 ]
[ 0  D  0  0 ]

             │
             ▼

CSR Representation

Values:
[A, B, C, D]

Column indices:
[0, 3, 2, 1]

Row information:
[0, 2, 3, 4]
```

The greater the number of zero coefficients, the more useful sparse storage becomes.

The sparse matrix is then saved using SciPy's compressed **NPZ** format.

---

# 8. Why Very High Compression Percentiles May Be Required

The original input may already be stored using an efficient image codec such as JPEG.

JPEG itself uses sophisticated operations including:

- transform coding,
- quantization,
- coefficient ordering,
- run-length coding,
- entropy coding.

The Fourier compressor, in contrast, stores surviving Fourier coefficients as complex numerical values together with sparse-matrix indexing information.

Therefore, at moderate Fourier compression levels, the sparse Fourier representation can actually be **larger than the original JPEG**.

Only when enough Fourier coefficients become zero does sparse storage become sufficiently efficient to reduce the file size.

This is an important experimental result of the project rather than an error in the Fourier transform.

The project therefore demonstrates the relationship between

$$
\text{coefficient retention}
\quad\longleftrightarrow\quad
\text{file size}
\quad\longleftrightarrow\quad
\text{reconstruction quality}.
$$

---

# 9. Reconstruction Using the Inverse DFT

To reconstruct the image, the sparse NPZ matrix is loaded and converted back into its Fourier-spectrum representation.

The **Inverse Discrete Fourier Transform (IDFT)** is then calculated:

$$
f'(x,y)
=
\frac{1}{MN}
\sum_{u=0}^{M-1}
\sum_{v=0}^{N-1}
\hat{F}(u,v)
e^{j2\pi
\left(
\frac{ux}{M}
+
\frac{vy}{N}
\right)}.
$$

Here,

$$
\hat{F}(u,v)
$$

is the compressed Fourier spectrum.

If no coefficients were removed,

$$
\hat{F}(u,v)=F(u,v),
$$

and, apart from numerical rounding,

$$
f'(x,y)\approx f(x,y).
$$

When coefficients are removed,

$$
\hat{F}(u,v)\neq F(u,v),
$$

so the reconstructed image differs from the original.

The more aggressively coefficients are removed, the greater the potential distortion.

---

# 10. Lossy Compression

The compression technique is therefore **lossy**.

The discarded Fourier coefficients cannot be recovered from the compressed file.

Increasing the compression percentile generally causes

$$
\text{fewer coefficients}
\Rightarrow
\text{smaller sparse representation}
\Rightarrow
\text{greater reconstruction error}.
$$

Conversely,

$$
\text{more coefficients}
\Rightarrow
\text{better reconstruction}
\Rightarrow
\text{larger compressed representation}.
$$

This produces the fundamental compression-quality trade-off demonstrated by the application.

---

# 11. Mean Squared Error

Reconstruction error is measured using **Mean Squared Error (MSE)**.

For an image containing $MN$ pixels,

$$
\operatorname{MSE}
=
\frac{1}{MN}
\sum_{x=0}^{M-1}
\sum_{y=0}^{N-1}
\left[
f(x,y)-f'(x,y)
\right]^2.
$$

A smaller MSE indicates that the reconstructed image is numerically closer to the original.

For perfect reconstruction,

$$
\operatorname{MSE}=0.
$$

---

# 12. Peak Signal-to-Noise Ratio

The application also calculates **Peak Signal-to-Noise Ratio (PSNR)**.

For an 8-bit grayscale image,

$$
MAX_I=255.
$$

PSNR is calculated as

$$
\operatorname{PSNR}
=
10\log_{10}
\left(
\frac{MAX_I^2}{\operatorname{MSE}}
\right)
$$

or equivalently,

$$
\operatorname{PSNR}
=
20\log_{10}
\left(
\frac{255}{\sqrt{\operatorname{MSE}}}
\right).
$$

PSNR is measured in decibels (dB).

Higher PSNR generally indicates that the reconstructed image is closer to the original.

If

$$
\operatorname{MSE}=0,
$$

the theoretical PSNR becomes infinite.

---

# 13. Compression Ratio

The program compares the original file size $S_o$ with the compressed Fourier representation $S_c$.

The compression ratio is

$$
R=\frac{S_o}{S_c}.
$$

For example,

$$
R=1.65
$$

means the original file occupies approximately 1.65 times as much storage as the compressed representation.

This is displayed as:

```text
1.65 : 1
```

---

# 14. Percentage Size Reduction

The percentage reduction in file size is calculated as

$$
\text{Reduction}
=
\left(
1-\frac{S_c}{S_o}
\right)\times100\%.
$$

For example, if

$$
S_o=152.2\text{ KB}
$$

and

$$
S_c=92.2\text{ KB},
$$

then

$$
\text{Reduction}
=
\left(
1-\frac{92.2}{152.2}
\right)\times100
\approx39.4\%.
$$

A negative value means that the sparse Fourier representation is larger than the original file.

---

# 15. Optional Power-of-Two FFT Grid

The application contains an option to resize the FFT grid to dimensions that are powers of two.

For example,

```text
1200 × 500
```

may become

```text
2048 × 512
```

This reflects the natural dimensional requirement of a simple **radix-2 Cooley-Tukey FFT implementation**.

However, NumPy's optimized FFT routines can process arbitrary image dimensions, so power-of-two resizing is not required for the normal high-performance processing path.

Resizing to larger power-of-two dimensions can also increase the total number of Fourier coefficients and therefore increase storage requirements.

---

# 16. Repository Structure

```text
Fourier-Image-Compressor/
│
├── main.py
├── requirements.txt
├── README.md
├── run_windows.bat
│
├── src/
│   ├── __init__.py
│   ├── engine.py
│   ├── codec.py
│   ├── metrics.py
│   └── gui.py
│
├── tests/
│   └── test_engine.py
│
├── samples/
│   └── sample 1.png
│
└── output/
```

### `main.py`

Entry point for the desktop application.

### `src/engine.py`

Contains the signal-processing operations:

- image preparation,
- 2-D FFT,
- magnitude calculation,
- percentile thresholding,
- Fourier coefficient removal,
- inverse FFT,
- spectrum visualization,
- educational DFT/Cooley-Tukey routines.

### `src/codec.py`

Handles:

- conversion to CSR sparse matrices,
- compressed NPZ storage,
- loading compressed Fourier matrices,
- metadata handling.

### `src/metrics.py`

Calculates:

- MSE,
- PSNR,
- compression ratio,
- percentage file-size reduction.

### `src/gui.py`

Implements the Tkinter desktop interface.

### `tests/`

Contains numerical tests comparing the educational FFT implementation against NumPy's FFT and testing the compression pipeline.

---

# 17. Installation

Clone the repository and install the required Python packages:

```bash
pip install -r requirements.txt
```

The primary dependencies are:

- NumPy
- SciPy
- Pillow
- Tkinter
- Pytest

Tkinter is normally included with standard Windows Python installations.

---

# 18. Running the Application

Run:

```bash
python main.py
```

On Windows, the included batch file can also be used:

```text
run_windows.bat
```

---

# 19. Using the Compressor

1. Select **Add Image**.
2. Choose an image.
3. Select the desired **Compression Percentile**.
4. Press **Compress**.
5. Compare the original and reconstructed images.
6. Observe coefficient retention, MSE, PSNR, compression ratio, and file-size reduction.
7. Select **View Spectrum** to inspect the Fourier magnitude spectrum.
8. Select **Save .NPZ** to store the sparse Fourier representation.
9. Select **Open .NPZ** to reconstruct a previously compressed Fourier image.
10. Select **Export PNG** to export the reconstructed image.

---

# 20. Signals & Systems Interpretation

The project demonstrates several important concepts from Signals and Systems.

## Two-Dimensional Signals

A grayscale image is treated as a two-dimensional discrete signal:

$$
f(x,y).
$$

## Frequency-Domain Representation

The DFT decomposes the spatial signal into spatial-frequency components:

$$
f(x,y)
\longleftrightarrow
F(u,v).
$$

## Superposition

The image can be interpreted as the superposition of many spatial-frequency components.

## Magnitude and Phase

Each Fourier coefficient contains both magnitude and phase information:

$$
F(u,v)=|F(u,v)|e^{j\phi(u,v)}.
$$

## Information Reduction

Weak Fourier components are removed according to their magnitudes.

## Inverse Transformation

The remaining components are combined through the inverse transform to reconstruct an approximation of the original signal.

Therefore, the complete system can be summarized mathematically as

$$
f(x,y)
\xrightarrow{\mathrm{DFT}}
F(u,v)
\xrightarrow{\mathrm{Threshold}}
\hat{F}(u,v)
\xrightarrow{\mathrm{Sparse\ Encoding}}
\text{NPZ}
$$

followed during decoding by

$$
\text{NPZ}
\xrightarrow{\mathrm{Sparse\ Decoding}}
\hat{F}(u,v)
\xrightarrow{\mathrm{IDFT}}
f'(x,y).
$$

---

# 21. Limitations

This project intentionally prioritizes demonstrating Fourier-domain signal processing rather than implementing a production image codec.

Current limitations include:

- grayscale-only Fourier compression,
- complex Fourier coefficients require substantial storage,
- CSR matrices have indexing overhead,
- already-compressed JPEG images can be smaller than the Fourier representation,
- aggressive coefficient removal causes visible reconstruction degradation,
- magnitude thresholding does not model human visual perception as effectively as modern image codecs,
- power-of-two resizing can increase the amount of transform data.

These limitations provide useful directions for future development.

Possible improvements include coefficient quantization, reduced-precision storage, conjugate-symmetry exploitation, improved entropy coding, and perceptually weighted Fourier coefficient selection.

---

# 22. Reference and Attribution

The Fourier coefficient-selection and sparse-storage approach used in this project was developed with reference to the open-source project:

**PLangari — Fourier-Transform-Image-Decoder**

Repository:

https://github.com/PLangari/Fourier-Transform-Image-Decoder

The reference project demonstrates DFT/FFT implementation and image compression by applying magnitude-based Fourier coefficient thresholding and storing the resulting sparse Fourier matrix.

This repository builds an independently organized application around that concept, including a desktop GUI, compression metrics, Fourier-spectrum visualization, save/load workflow, testing infrastructure, and repository structure.

---

## License

This project is intended for educational and academic use.

When redistributing or extending code derived from external open-source projects, the corresponding upstream license and attribution requirements should be followed.