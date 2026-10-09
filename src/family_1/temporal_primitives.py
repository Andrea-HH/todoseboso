"""Primitivas temporales para series irregulares, sin usar el target."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew

CORE = ["mean", "median", "std", "min", "max", "q25", "q75", "auc", "normalized_auc",
        "slope", "peak_value", "peak_day", "first", "last", "last_minus_first",
        "max_growth_rate", "max_decline_rate", "peak_drop", "max_drawdown", "max_runup"]
EXTENDED = ["q10", "q90", "iqr", "skewness", "kurtosis", "min_day", "peak_doy", "min_doy",
            "relative_change", "pre_peak_slope", "post_peak_slope", "mean_dx_dt", "std_dx_dt",
            "max_growth_day", "max_decline_day", "proportion_positive_changes",
            "proportion_negative_changes", "cumulative_positive_change", "cumulative_negative_change",
            "max_growth_jump", "max_decline_jump", "drawdown_start_day", "drawdown_end_day",
            "drawdown_duration", "runup_start_day", "runup_end_day", "runup_duration",
            "time_peak_to_end", "std_first_differences", "mean_absolute_change", "total_variation"]

def _slope(t: np.ndarray, x: np.ndarray) -> float:
    return float(np.polyfit(t, x, 1)[0]) if len(x) >= 2 and np.ptp(t) > 0 else np.nan

def extract_temporal_features(dates, values, window_start="2025-04-01") -> dict[str, float]:
    d = pd.to_datetime(pd.Series(dates), errors="coerce")
    x = pd.to_numeric(pd.Series(values), errors="coerce")
    z = pd.DataFrame({"d": d, "x": x}).dropna().groupby("d", as_index=False)["x"].mean().sort_values("d")
    out = {k: np.nan for k in CORE + EXTENDED}
    out["n_obs"] = float(len(z))
    if z.empty:
        return out
    x = z.x.to_numpy(float); dates = z.d.to_numpy(dtype="datetime64[ns]")
    origin = np.datetime64(pd.Timestamp(window_start), "ns")
    t = (dates - origin) / np.timedelta64(1, "D")
    imax, imin = int(np.nanargmax(x)), int(np.nanargmin(x))
    out.update(mean=np.mean(x), median=np.median(x), std=np.std(x, ddof=1) if len(x)>1 else np.nan,
               min=np.min(x), max=np.max(x), q10=np.quantile(x,.1), q25=np.quantile(x,.25),
               q75=np.quantile(x,.75), q90=np.quantile(x,.9), iqr=np.quantile(x,.75)-np.quantile(x,.25),
               skewness=float(skew(x, bias=False)) if len(x)>=3 and np.ptp(x)>0 else np.nan,
               kurtosis=float(kurtosis(x, bias=False)) if len(x)>=4 and np.ptp(x)>0 else np.nan,
               peak_value=x[imax], peak_day=t[imax], min_day=t[imin],
               peak_doy=pd.Timestamp(dates[imax]).dayofyear, min_doy=pd.Timestamp(dates[imin]).dayofyear,
               first=x[0], last=x[-1], last_minus_first=x[-1]-x[0], peak_drop=x[imax]-x[-1],
               time_peak_to_end=t[-1]-t[imax])
    out["relative_change"] = (x[-1]-x[0])/abs(x[0]) if abs(x[0]) >= 1e-6 else np.nan
    if len(x) >= 2:
        dt=np.diff(t); dx=np.diff(x); valid=dt>0; rate=dx[valid]/dt[valid]
        out["auc"] = float(np.trapezoid(x, t)); out["normalized_auc"] = out["auc"]/(t[-1]-t[0]) if t[-1]>t[0] else np.nan
        out["slope"]=_slope(t,x); out["pre_peak_slope"]=_slope(t[:imax+1],x[:imax+1]); out["post_peak_slope"]=_slope(t[imax:],x[imax:])
        if rate.size:
            irp=int(np.argmax(rate)); irn=int(np.argmin(rate))
            out.update(mean_dx_dt=np.mean(rate), std_dx_dt=np.std(rate,ddof=1) if rate.size>1 else np.nan,
                       max_growth_rate=rate[irp], max_decline_rate=rate[irn],
                       max_growth_day=t[np.flatnonzero(valid)[irp]+1], max_decline_day=t[np.flatnonzero(valid)[irn]+1])
        out.update(proportion_positive_changes=np.mean(dx>0), proportion_negative_changes=np.mean(dx<0),
                   cumulative_positive_change=np.sum(dx[dx>0]), cumulative_negative_change=np.sum(dx[dx<0]),
                   max_growth_jump=np.max(dx), max_decline_jump=np.min(dx),
                   std_first_differences=np.std(dx,ddof=1) if len(dx)>1 else np.nan,
                   mean_absolute_change=np.mean(abs(dx)), total_variation=np.sum(abs(dx)))
        running_max=np.maximum.accumulate(x); end=int(np.argmax(running_max-x)); start=int(np.argmax(x[:end+1]))
        running_min=np.minimum.accumulate(x); rend=int(np.argmax(x-running_min)); rstart=int(np.argmin(x[:rend+1]))
        out.update(max_drawdown=running_max[end]-x[end], drawdown_start_day=t[start], drawdown_end_day=t[end],
                   drawdown_duration=t[end]-t[start], max_runup=x[rend]-running_min[rend],
                   runup_start_day=t[rstart], runup_end_day=t[rend], runup_duration=t[rend]-t[rstart])
    return {k: float(v) if pd.notna(v) else np.nan for k,v in out.items()}

def select_features(result: dict, level: str) -> dict:
    names = ["n_obs"] + (CORE if level == "core" else EXTENDED)
    return {k: result.get(k, np.nan) for k in names}
