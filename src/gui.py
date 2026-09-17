import os, tempfile, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
import numpy as np
from PIL import Image, ImageTk

from .engine import prepare_image, fft2d, compress_spectrum, reconstruct, spectrum_preview
from .codec import save_npz_bundle, load_npz_bundle, bundle_size
from .metrics import mse, psnr, ratio, reduction

BG="#f7f7f8"; CARD="#ffffff"; TEXT="#18181b"; MUTED="#71717a"; BORDER="#dedee3"; ACCENT="#18181b"

class FourierCompressorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fourier Image Compressor")
        try: self.state("zoomed")
        except tk.TclError: self.geometry("1200x800")
        self.minsize(950,650); self.configure(bg=BG)
        self.percentile=tk.DoubleVar(value=75.0)
        self.pow2=tk.BooleanVar(value=True)
        self.source_path=None; self.source_image=None; self.gray=None
        self.original_size=None; self.spectrum=None; self.filtered=None
        self.reconstructed=None; self.temp_npz=None
        self._build()

    def card(self,p):
        return tk.Frame(p,bg=CARD,highlightbackground=BORDER,highlightthickness=1)

    def button(self,p,text,cmd,primary=False):
        return tk.Button(p,text=text,command=cmd,bg=ACCENT if primary else CARD,
            fg="white" if primary else TEXT,relief="flat",bd=0,padx=16,pady=8,
            font=("Segoe UI",10,"bold" if primary else "normal"),cursor="hand2")

    def _build(self):
        h=tk.Frame(self,bg=BG); h.pack(fill="x",padx=32,pady=(18,8))
        tk.Label(h,text="Fourier Image Compressor",bg=BG,fg=TEXT,font=("Segoe UI",20,"bold")).pack(side="left")
        tk.Label(h,text="2-D FFT • percentile threshold • sparse CSR/NPZ",bg=BG,fg=MUTED,font=("Segoe UI",10)).pack(side="left",padx=18,pady=(8,0))

        bar=self.card(self); bar.pack(fill="x",padx=32,pady=6)
        b=tk.Frame(bar,bg=CARD); b.pack(fill="x",padx=16,pady=10)
        self.button(b,"+ Add Image",self.load_image).pack(side="left",padx=(0,8))
        self.button(b,"Open .NPZ",self.open_npz).pack(side="left",padx=8)
        self.button(b,"View Spectrum",self.view_spectrum).pack(side="left",padx=8)
        tk.Checkbutton(b,text="Resize FFT grid to powers of two",variable=self.pow2,bg=CARD,fg=TEXT).pack(side="left",padx=20)
        self.button(b,"Compress",self.compress,True).pack(side="right")

        c=self.card(self); c.pack(fill="x",padx=32,pady=6)
        ci=tk.Frame(c,bg=CARD); ci.pack(fill="x",padx=16,pady=8)
        tk.Label(ci,text="Compression percentile",bg=CARD,fg=TEXT,font=("Segoe UI",10,"bold")).pack(side="left")
        tk.Scale(ci,from_=0,to=99.9,resolution=.1,orient="horizontal",variable=self.percentile,
                 bg=CARD,fg=TEXT,highlightthickness=0,bd=0,length=420,command=self.slider).pack(side="left",padx=18)
        self.p_label=tk.Label(ci,text="75.0% removed • ~25.0% retained",bg=CARD,fg=MUTED,font=("Segoe UI",10))
        self.p_label.pack(side="left")

        imgs=tk.Frame(self,bg=BG); imgs.pack(fill="both",expand=True,padx=32,pady=6)
        imgs.grid_columnconfigure(0,weight=1); imgs.grid_columnconfigure(1,weight=1); imgs.grid_rowconfigure(0,weight=1)
        self.left=self.panel(imgs,"Original (grayscale input)"); self.left["frame"].grid(row=0,column=0,sticky="nsew",padx=(0,8))
        self.right=self.panel(imgs,"Reconstructed"); self.right["frame"].grid(row=0,column=1,sticky="nsew",padx=(8,0))

        bot=self.card(self); bot.pack(fill="x",padx=32,pady=(6,18))
        bi=tk.Frame(bot,bg=CARD); bi.pack(fill="x",padx=16,pady=10)
        self.stats=tk.Label(bi,text="Add an image to begin.",bg=CARD,fg=MUTED,font=("Consolas",10),anchor="w")
        self.stats.pack(side="left",fill="x",expand=True)
        self.button(bi,"Save .NPZ",self.save_npz).pack(side="right",padx=5)
        self.button(bi,"Export PNG",self.export_png).pack(side="right",padx=5)

    def panel(self,p,title):
        f=self.card(p)
        tk.Label(f,text=title,bg=CARD,fg=TEXT,font=("Segoe UI",12,"bold")).pack(anchor="w",padx=16,pady=(12,3))
        im=tk.Label(f,text="No image",bg=CARD,fg=MUTED,font=("Segoe UI",11)); im.pack(fill="both",expand=True,padx=16,pady=8)
        info=tk.Label(f,text="",bg=CARD,fg=MUTED,font=("Segoe UI",9)); info.pack(anchor="w",padx=16,pady=(0,10))
        return {"frame":f,"image":im,"info":info}

    def show(self,image,panel):
        x=image.copy(); x.thumbnail((500,330),Image.Resampling.LANCZOS)
        ph=ImageTk.PhotoImage(x); panel["image"].config(image=ph,text=""); panel["image"].image=ph

    def slider(self,_=None):
        p=float(self.percentile.get()); self.p_label.config(text=f"{p:.1f}% removed • ~{100-p:.1f}% retained")

    def load_image(self):
        path=filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),("All files","*.*")])
        if not path:return
        try:
            img=Image.open(path).convert("RGB")
            gray,orig=prepare_image(img,self.pow2.get())
            self.source_path=path; self.source_image=img; self.gray=gray; self.original_size=orig
            self.spectrum=fft2d(gray); self.filtered=None; self.reconstructed=None
            self.show(Image.fromarray(np.clip(gray,0,255).astype(np.uint8),"L"),self.left)
            self.left["info"].config(text=f"Source {img.width}×{img.height} • FFT grid {gray.shape[1]}×{gray.shape[0]} • {self.fmt(os.path.getsize(path))}")
            self.right["image"].config(image="",text="Press Compress"); self.right["image"].image=None
            self.stats.config(text="Loaded. This reference-compatible engine intentionally compresses grayscale.")
        except Exception as e: messagebox.showerror("Load error",str(e))

    def compress(self):
        if self.spectrum is None:
            messagebox.showinfo("Add image","Please add an image first."); return
        try:
            p=float(self.percentile.get())
            self.filtered,cutoff,retained=compress_spectrum(self.spectrum,p)
            meta={"compression_percentile":p,"cutoff":cutoff,"retained_fraction":retained,
                  "original_width":self.original_size[0],"original_height":self.original_size[1],
                  "fft_width":self.filtered.shape[1],"fft_height":self.filtered.shape[0],
                  "power_of_two_resize":bool(self.pow2.get()),"color_mode":"grayscale"}
            temp=Path(tempfile.gettempdir())/"fourier_image_compressor_preview.npz"
            self.temp_npz,_=save_npz_bundle(temp,self.filtered,meta)
            decoded,meta2=load_npz_bundle(self.temp_npz)
            self.reconstructed=reconstruct(decoded,self.original_size)
            self.show(self.reconstructed,self.right)

            original_compare=Image.fromarray(np.clip(self.gray,0,255).astype(np.uint8),"L")
            if original_compare.size != self.original_size:
                original_compare=original_compare.resize(self.original_size,Image.Resampling.BILINEAR)
            a=np.asarray(original_compare); b=np.asarray(self.reconstructed)
            e=mse(a,b); q=psnr(a,b)
            ob=os.path.getsize(self.source_path); cb=bundle_size(self.temp_npz)
            self.right["info"].config(text=f"{retained*100:.2f}% Fourier coefficients retained")
            self.stats.config(text=f"Original {self.fmt(ob)} | NPZ {self.fmt(cb)} | Ratio {ratio(ob,cb):.2f}:1 | Reduction {reduction(ob,cb):.1f}% | MSE {e:.2f} | PSNR {'∞' if np.isinf(q) else f'{q:.2f} dB'}")
        except Exception as e: messagebox.showerror("Compression error",str(e))

    def save_npz(self):
        if self.filtered is None:
            messagebox.showinfo("Compress first","Compress an image first."); return
        path=filedialog.asksaveasfilename(defaultextension=".npz",filetypes=[("Sparse Fourier NPZ","*.npz")])
        if not path:return
        p=float(self.percentile.get()); retained=np.count_nonzero(self.filtered)/self.filtered.size
        meta={"compression_percentile":p,"retained_fraction":retained,"original_width":self.original_size[0],
              "original_height":self.original_size[1],"fft_width":self.filtered.shape[1],"fft_height":self.filtered.shape[0],
              "power_of_two_resize":bool(self.pow2.get()),"color_mode":"grayscale"}
        try:
            npz,js=save_npz_bundle(path,self.filtered,meta)
            messagebox.showinfo("Saved",f"Saved:\n{npz}\n\nMetadata:\n{js}")
        except Exception as e: messagebox.showerror("Save error",str(e))

    def open_npz(self):
        path=filedialog.askopenfilename(filetypes=[("Sparse Fourier NPZ","*.npz")])
        if not path:return
        try:
            spec,meta=load_npz_bundle(path)
            size=(int(meta.get("original_width",spec.shape[1])),int(meta.get("original_height",spec.shape[0])))
            self.filtered=spec; self.spectrum=spec; self.original_size=size; self.temp_npz=Path(path)
            self.reconstructed=reconstruct(spec,size); self.show(self.reconstructed,self.right)
            r=float(meta.get("retained_fraction",np.count_nonzero(spec)/spec.size))*100
            self.right["info"].config(text=f"{size[0]}×{size[1]} • {r:.2f}% coefficients retained")
            self.stats.config(text=f"Opened {os.path.basename(path)} • {self.fmt(os.path.getsize(path))}")
        except Exception as e: messagebox.showerror("Open error",str(e))

    def export_png(self):
        if self.reconstructed is None:
            messagebox.showinfo("Nothing to export","Compress or open an NPZ first."); return
        path=filedialog.asksaveasfilename(defaultextension=".png",filetypes=[("PNG","*.png")])
        if path:self.reconstructed.save(path)

    def view_spectrum(self):
        spec=self.filtered if self.filtered is not None else self.spectrum
        if spec is None:
            messagebox.showinfo("Add image","Please add an image first."); return
        im=Image.fromarray(spectrum_preview(spec),"L"); im.thumbnail((760,560),Image.Resampling.LANCZOS)
        w=tk.Toplevel(self); w.title("Fourier Magnitude Spectrum"); w.configure(bg=BG)
        ph=ImageTk.PhotoImage(im); lab=tk.Label(w,image=ph,bg=BG); lab.image=ph; lab.pack(padx=20,pady=20)

    @staticmethod
    def fmt(n):
        n=float(n)
        for u in ["B","KB","MB","GB"]:
            if n<1024 or u=="GB":return f"{n:.1f} {u}"
            n/=1024
