# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy", "pillow"]
# ///
"""Generates the EVE cloud textures (equirectangular, seamless) and the detail texture.

Usage: uv run tools/gen_clouds.py
Output: GameData/GargantuaSystem/Textures/EVE/  (outside PluginData: EVE reads them through the GameDatabase)
RGB = cloud brightness, A = coverage. The final colour comes from each layer's _Color in the .cfg.
"""
from pathlib import Path

import numpy as np

from gen_planets import check_seamless, fbm, render, ridged, save_gray, save_rgb, smoothstep, warp

OUT = Path(__file__).resolve().parent.parent / "GameData" / "GargantuaSystem" / "Textures" / "EVE"
# Volumetric (raymarched) EVE reads coverage maps from disk like the stock pack does: PluginData, R channel.
OUT_VOL = OUT.parent.parent / "PluginData" / "EVE"


def miller(lat, lon, xyz):
    # Film: a heavy, almost unbroken grey overcast with a few darker, thicker bands and rare breaks.
    p = warp(xyz, 0.5, 2.0, 201)
    base = fbm(p, 3.0, 6, 202)
    cover = smoothstep(0.28, 0.48, base)
    thick = fbm(warp(xyz * np.float32([1, 3, 1]), 0.3, 3.0, 203), 6.0, 5, 204)
    return np.clip(0.82 + 0.18 * thick, 0, 1), np.clip(cover * (0.85 + 0.15 * thick), 0, 1)


def mann(lat, lon, xyz):
    # "Frozen clouds": long thin sheets stretched along the wind, about a third of the sky.
    streaks = ridged(warp(xyz * np.float32([1, 4, 1]), 0.25, 2.0, 211), 4.0, 5, 212)
    patches = smoothstep(0.45, 0.65, fbm(warp(xyz, 0.4, 1.5, 213), 2.0, 4, 214))
    cover = smoothstep(0.35, 0.75, streaks) * patches
    return np.full(lat.shape, 0.95, np.float32), np.clip(cover * 0.85, 0, 1)


def edmunds(lat, lon, xyz):
    # Sparse fair-weather cumulus, a quarter of the sky at most.
    n = fbm(warp(xyz, 0.3, 4.0, 221), 10.0, 6, 222)
    cover = smoothstep(0.60, 0.72, n)
    return np.full(lat.shape, 0.97, np.float32), cover


def mann_aurora(lat, lon, xyz):
    # Auroral ovals around both poles (pulsar wind on Mann's thin air): wavy curtains, green with a pink fringe.
    alat = np.degrees(np.abs(lat))
    wobble = 4 * (fbm(warp(xyz, 0.2, 1.5, 241), 2.0, 4, 242) - 0.5)
    band = np.exp(-((alat - 70 - wobble) / 3.5) ** 2)
    curtains = smoothstep(0.35, 0.8, ridged(warp(xyz * np.float32([3, 1, 3]), 0.3, 3.0, 243), 6.0, 5, 244))
    cover = np.clip(band * (0.25 + 0.75 * curtains), 0, 1)
    return np.clip(band, 0, 1), cover


LAYERS = {"Miller_clouds": (miller, 4096), "Mann_clouds": (mann, 2048), "Edmunds_clouds": (edmunds, 2048)}


def detail(n=512):
    """Tiling detail noise for close-up cloud texture (FFT noise wraps in both axes)."""
    rng = np.random.default_rng(230)
    f = np.fft.fftfreq(n)
    k = np.sqrt(f[None, :] ** 2 + f[:, None] ** 2)
    amp = np.where(k > 0, 1 / np.maximum(k, 1e-6) ** 1.3, 0)
    d = np.fft.ifft2(amp * np.exp(2j * np.pi * rng.random((n, n)))).real
    return (d - d.min()) / (d.max() - d.min())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    OUT_VOL.mkdir(parents=True, exist_ok=True)
    for name, (fn, w) in LAYERS.items():
        bright, cover = render(w, w // 2, fn)
        check_seamless(cover, name)
        rgb = np.repeat(bright[..., None], 3, axis=-1)
        save_rgb(OUT / f"{name}.png", rgb, cover)
        save_gray(OUT_VOL / f"{name}_coverage.png", cover)
        print(f"{name}: mean coverage {cover.mean():.0%}")
    # aurora: self-lit 2D layer, colour baked in (green core, pink upper fringe)
    hue, cover = render(2048, 1024, mann_aurora)
    check_seamless(cover, "Mann_aurora")
    green, pink = np.array([0.35, 1.0, 0.55]), np.array([0.95, 0.45, 0.85])
    rgb = green * hue[..., None] + pink * (1 - hue[..., None])
    save_rgb(OUT / "Mann_aurora.png", rgb, cover)
    print(f"Mann_aurora: mean coverage {cover.mean():.1%}")
    d = detail()
    check_seamless(d, "cloud detail")
    save_gray(OUT / "cloud_detail.png", d)
    print("cloud_detail ok")


if __name__ == "__main__":
    main()
