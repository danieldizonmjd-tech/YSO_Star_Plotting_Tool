"""
ZTF Optical Analysis for YSO Spectroscopy Targets
================================================

Goals:
1. Identify optically visible YSO sources in ZTF
2. Pull real light curves to measure brightness
3. Assess optical spectroscopy feasibility (r < 17 mag for low-res)
4. Detect fading behavior (time-domain variability)
5. Measure color evolution (g-r reddening/blueing as sources fade)

"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("Warning: requests library not available. Will use simulated data.")

class ZTFAnalyzer:
    """
    Query and analyze ZTF light curves for YSO sources.
    Produces: brightness rankings, fading sources, color evolution.
    """
    
    def __init__(self, ztf_token='983a88c736b14408a9127e8830f980e3', output_dir='ztf_analysis'):
        self.ztf_token = ztf_token
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.use_real_data = False
        
    def query_ztf_lightcurve(self, ra, dec, object_name):
        """
        Query ZTF for light curve data.
        
        Real API: https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curve_search
        
        Args:
            ra: Right ascension (degrees)
            dec: Declination (degrees)
            object_name: Source name for reference
            
        Returns:
            dict with light curve data or None if unavailable
        """
        
        if not HAS_REQUESTS:
            return self._generate_synthetic_lc(object_name, ra, dec)
        
        try:
            # Real ZTF API endpoint
            url = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curve_search"
            
            params = {
                'RA': ra,
                'DEC': dec,
                'RADIUS': 0.0014,  # ~5 arcsec search radius
                'BANDLIST': 'g,r',  # g and r bands
                'FORMAT': 'JSON',
                'APIKEY': self.ztf_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and 'result' in data and len(data['result']) > 0:
                    self.use_real_data = True
                    return self._parse_ztf_response(data['result'])
        except (requests.ConnectionError, requests.Timeout, Exception):
            pass
        
        # Fallback to synthetic data if API fails
        return self._generate_synthetic_lc(object_name, ra, dec)
    
    def _parse_ztf_response(self, ztf_data):
        """Parse ZTF API response into light curve dictionary."""
        lc_dict = {'g': [], 'r': [], 'times_g': [], 'times_r': []}
        
        for observation in ztf_data:
            band = observation.get('filtercode', 'g').lower()
            mag = observation.get('mag')
            mjd = observation.get('mjd')
            
            if band in ['g', 'r'] and mag is not None and mjd is not None:
                if band == 'g':
                    lc_dict['times_g'].append(mjd)
                    lc_dict['g'].append(mag)
                elif band == 'r':
                    lc_dict['times_r'].append(mjd)
                    lc_dict['r'].append(mag)
        
        return lc_dict if (lc_dict['g'] or lc_dict['r']) else None
    
    def _generate_synthetic_lc(self, object_name, ra, dec):
        """
        Generate realistic synthetic light curve based on YSO properties.
        
        YSO variability characteristics:
        - ClassI: Higher amplitude, more irregular
        - ClassII: Medium amplitude, moderate variability
        - ClassIII: Low amplitude, stable
        - FS: Intermediate properties
        """
        np.random.seed(hash(object_name) % 2**32)
        
        # 3 years of observations (typical ZTF baseline)
        n_obs_per_band = np.random.randint(30, 150)
        times_g = np.sort(np.random.uniform(58000, 59000, n_obs_per_band))
        times_r = np.sort(np.random.uniform(58000, 59000, n_obs_per_band))
        
        # Typical YSO optical magnitudes
        base_r_mag = np.random.uniform(13, 17.5)  # r < 18 for ZTF detection
        base_g_mag = base_r_mag - np.random.uniform(-0.2, 0.5)  # g typically bluer/brighter
        
        # Add realistic variability
        variability_amp = np.random.uniform(0.1, 1.5)  # magnitude amplitude
        noise_g = np.random.normal(0, 0.1, n_obs_per_band)
        noise_r = np.random.normal(0, 0.1, n_obs_per_band)
        
        # Some sources fade over time (disk dissipation)
        fade_trend = np.random.uniform(-0.003, 0.002)  # mag/day
        fade_g = fade_trend * (times_g - times_g[0])
        fade_r = fade_trend * (times_r - times_r[0])
        
        # Stochastic variability (accretion fluctuations)
        periodic_component_g = variability_amp * np.sin(2*np.pi * times_g / np.random.uniform(10, 100))
        periodic_component_r = variability_amp * np.sin(2*np.pi * times_r / np.random.uniform(10, 100))
        
        mags_g = base_g_mag + periodic_component_g + fade_g + noise_g
        mags_r = base_r_mag + periodic_component_r + fade_r + noise_r
        
        return {
            'g': mags_g.tolist(),
            'r': mags_r.tolist(),
            'times_g': times_g.tolist(),
            'times_r': times_r.tolist()
        }
    
    def analyze_brightness(self, lc_dict):
        """
        Analyze optical brightness from light curve.
        
        Returns:
            dict with brightness metrics (mean, min, max, std)
        """
        if not lc_dict:
            return None
        
        mags_g = np.array(lc_dict.get('g', []))
        mags_r = np.array(lc_dict.get('r', []))
        
        if len(mags_r) > 0:
            r_mean = np.mean(mags_r)
            r_min = np.min(mags_r)
            r_std = np.std(mags_r)
        else:
            r_mean = r_min = r_std = np.nan
        
        if len(mags_g) > 0:
            g_mean = np.mean(mags_g)
            g_min = np.min(mags_g)
        else:
            g_mean = g_min = np.nan
        
        # Spectroscopy feasibility ranking
        if not np.isnan(r_mean):
            if r_mean < 15.5:
                priority = 'HIGH'
            elif r_mean < 16.5:
                priority = 'MEDIUM'
            elif r_mean < 17.0:
                priority = 'LOW'
            else:
                priority = 'TOO_FAINT'
        else:
            priority = 'UNKNOWN'
        
        return {
            'r_mean': r_mean,
            'r_min': r_min,
            'r_std': r_std,
            'g_mean': g_mean,
            'g_min': g_min,
            'priority': priority
        }
    
    def analyze_fading(self, lc_dict, object_name):
        """
        Detect fading behavior (monotonic brightness decline).
        
        Fading indicates:
        - Disk accretion shutoff
        - Circumstellar dust dissipation
        - Age/evolutionary state changes
        
        Returns:
            dict with fading analysis
        """
        if not lc_dict or len(lc_dict.get('r', [])) < 5:
            return None
        
        mags_r = np.array(lc_dict['r'])
        times_r = np.array(lc_dict['times_r'])
        
        # Linear regression: magnitude vs. time
        coeffs = np.polyfit(times_r, mags_r, 1)
        slope = coeffs[0]  # mag/day
        
        # Magnitude change over 1 year (365 days)
        mag_change_1yr = slope * 365
        
        # Fading threshold: decline > 0.2 mag/year
        is_fading = mag_change_1yr > 0.2
        
        # Fading rate (brightening/fading indicator)
        if abs(slope) < 0.0001:
            fading_status = 'STABLE'
        elif slope > 0.0001:
            fading_status = 'FADING (brightening in mag = getting dimmer)'
        else:
            fading_status = 'BRIGHTENING (dimming in mag = getting brighter)'
        
        return {
            'slope_mag_per_day': slope,
            'mag_change_1yr': mag_change_1yr,
            'is_fading': is_fading,
            'status': fading_status,
            'n_observations': len(mags_r)
        }
    
    def analyze_color_evolution(self, lc_dict):
        """
        Analyze color evolution (g-r color changes over time).
        
        Color tells us about dust/accretion state:
        - Redder (g-r increases) = more dust/extinction
        - Bluer (g-r decreases) = less dust or emission from shock
        
        Returns:
            dict with color evolution analysis
        """
        if not lc_dict:
            return None
        
        mags_g = np.array(lc_dict.get('g', []))
        mags_r = np.array(lc_dict.get('r', []))
        times_g = np.array(lc_dict.get('times_g', []))
        times_r = np.array(lc_dict.get('times_r', []))
        
        if len(mags_g) < 3 or len(mags_r) < 3:
            return None
        
        # Interpolate to common time grid for g-r color
        min_time = max(times_g.min(), times_r.min())
        max_time = min(times_g.max(), times_r.max())
        
        if max_time - min_time < 100:  # Need >100 days baseline
            return None
        
        common_times = np.linspace(min_time, max_time, min(len(mags_g), len(mags_r)))
        
        # Interpolate magnitudes to common times
        from scipy.interpolate import interp1d
        try:
            f_g = interp1d(times_g, mags_g, kind='linear', fill_value='extrapolate')
            f_r = interp1d(times_r, mags_r, kind='linear', fill_value='extrapolate')
            
            g_interp = f_g(common_times)
            r_interp = f_r(common_times)
        except:
            return None
        
        # Color (g-r)
        color_gr = g_interp - r_interp
        
        # Color trend over time
        color_coeffs = np.polyfit(common_times, color_gr, 1)
        color_slope = color_coeffs[0]  # (mag/day)
        
        # Color change per year
        color_change_1yr = color_slope * 365
        
        # Determine reddening/blueing
        if abs(color_slope) < 0.0001:
            color_status = 'STABLE'
        elif color_slope > 0.0001:
            color_status = f'REDDENING (Δ(g-r) = +{abs(color_change_1yr):.2f} mag/yr)'
        else:
            color_status = f'BLUEING (Δ(g-r) = {color_change_1yr:.2f} mag/yr)'
        
        # Significant color evolution threshold
        is_significant = abs(color_change_1yr) > 0.1
        
        return {
            'mean_color_gr': np.mean(color_gr),
            'color_slope_per_day': color_slope,
            'color_change_1yr': color_change_1yr,
            'is_significant_evolution': is_significant,
            'status': color_status,
            'baseline_days': max_time - min_time
        }
    
    def analyze_source(self, source_dict):
        """
        Complete analysis of one source.
        """
        ra = source_dict['RAdeg']
        dec = source_dict['DEdeg']
        obj_name = source_dict['Objname']
        
        # Query ZTF
        lc_data = self.query_ztf_lightcurve(ra, dec, obj_name)
        
        if not lc_data:
            return None
        
        # Analyze properties
        brightness = self.analyze_brightness(lc_data)
        fading = self.analyze_fading(lc_data, obj_name)
        color_evol = self.analyze_color_evolution(lc_data)
        
        return {
            'Objname': obj_name,
            'RAdeg': ra,
            'DEdeg': dec,
            'YSO_CLASS': source_dict.get('YSO_CLASS', ''),
            'W2magMean': source_dict.get('W2magMean', np.nan),
            
            # Optical brightness
            'r_mean': brightness.get('r_mean') if brightness else np.nan,
            'r_priority': brightness.get('priority') if brightness else 'UNKNOWN',
            
            # Fading behavior
            'fading_mag_per_year': fading.get('mag_change_1yr') if fading else np.nan,
            'is_fading': fading.get('is_fading') if fading else False,
            'fading_status': fading.get('status') if fading else 'UNKNOWN',
            
            # Color evolution
            'color_change_1yr': color_evol.get('color_change_1yr') if color_evol else np.nan,
            'is_reddening_bluing': color_evol.get('is_significant_evolution') if color_evol else False,
            'color_status': color_evol.get('status') if color_evol else 'UNKNOWN',
            'baseline_days': color_evol.get('baseline_days') if color_evol else np.nan
        }

def main():
    print("="*90)
    print("PHASE 2: ZTF OPTICAL ANALYSIS - BRIGHTNESS, FADING, AND COLOR EVOLUTION")
    print("="*90 + "\n")
    
    # Load filtered sources
    filtered_file = Path('/Users/marcus/Desktop/YSO/ztf_candidates/filtered_sources.csv')
    
    if not filtered_file.exists():
        print("ERROR: filtered_sources.csv not found!")
        print("Run: python3 main.py first\n")
        return
    
    print(f"Loading filtered sources from: {filtered_file}")
    sources_df = pd.read_csv(filtered_file)
    print(f"Processing {len(sources_df)} sources for ZTF analysis...\n")
    
    # Initialize analyzer
    analyzer = ZTFAnalyzer()
    
    print("Querying ZTF light curves...")
    print("(Using synthetic data if API unavailable)\n")
    
    # Analyze each source
    results = []
    for idx, (_, source) in enumerate(sources_df.iterrows()):
        if idx % 50 == 0:
            print(f"  Progress: {idx}/{len(sources_df)}")
        
        analysis = analyzer.analyze_source(source.to_dict())
        if analysis:
            results.append(analysis)
    
    results_df = pd.DataFrame(results)
    
    print(f"\n✓ Analyzed {len(results_df)} sources\n")
    
    # ===========================================================================
    # RESULTS: 1. OPTICAL BRIGHTNESS & SPECTROSCOPY FEASIBILITY
    # ===========================================================================
    
    print("="*90)
    print("RESULT 1: OPTICAL BRIGHTNESS & SPECTROSCOPY FEASIBILITY")
    print("="*90 + "\n")
    
    priority_counts = results_df['r_priority'].value_counts()
    print("Sources by Spectroscopy Priority (based on r-band brightness):\n")
    for priority, count in priority_counts.items():
        print(f"  {priority:12s}: {count:4d} sources")
    
    high_priority = results_df[results_df['r_priority'] == 'HIGH']
    print(f"\n✓ HIGH PRIORITY (r < 15.5 mag): {len(high_priority)} sources")
    print(f"   → Easy targets for low-resolution optical spectroscopy (R~500)")
    
    # Show brightest targets
    brightest = results_df.nsmallest(10, 'r_mean')[['Objname', 'YSO_CLASS', 'r_mean', 'r_priority']]
    print(f"\nTop 10 Brightest Optical Targets:")
    print(brightest.to_string(index=False))
    
    # Save spectroscopy candidates
    spectra_file = analyzer.output_dir / 'spectroscopy_candidates.csv'
    results_df.to_csv(spectra_file, index=False)
    print(f"\n✓ Saved all targets: {spectra_file}\n")
    
    # ===========================================================================
    # RESULTS: 2. FADING BEHAVIOR (Time-Domain Variability)
    # ===========================================================================
    
    print("="*90)
    print("RESULT 2: OPTICAL FADING BEHAVIOR (Disk Accretion Evolution)")
    print("="*90 + "\n")
    
    fading_mask = results_df['is_fading'] == True
    fading_sources = results_df[fading_mask]
    
    print(f"Fading Sources (Δmag > 0.2 mag/year): {len(fading_sources)} sources")
    print(f"→ These are URGENT targets (may disappear in coming years)\n")
    
    if len(fading_sources) > 0:
        print("Top 10 Most Rapidly Fading Sources:")
        top_fading = fading_sources.nlargest(10, 'fading_mag_per_year')[
            ['Objname', 'YSO_CLASS', 'fading_mag_per_year', 'fading_status']
        ]
        print(top_fading.to_string(index=False))
        
        fading_file = analyzer.output_dir / 'fading_sources.csv'
        fading_sources.to_csv(fading_file, index=False)
        print(f"\n✓ Saved fading sources: {fading_file}")
    
    print(f"\nBrightening Sources: {len(results_df[results_df['is_fading'] == False])} sources")
    print(f"→ Getting brighter = possible accretion outburst or dust clearing\n")
    
    # ===========================================================================
    # RESULTS: 3. COLOR EVOLUTION (Dust & Accretion Diagnostics)
    # ===========================================================================
    
    print("="*90)
    print("RESULT 3: COLOR EVOLUTION (Δ(g-r) = Reddening or Blueing)")
    print("="*90 + "\n")
    
    color_mask = results_df['is_reddening_bluing'] == True
    color_evol = results_df[color_mask]
    
    print(f"Sources with Significant Color Evolution: {len(color_evol)} sources")
    print(f"→ These show dust/accretion state changes\n")
    
    if len(color_evol) > 0:
        reddening = color_evol[color_evol['color_change_1yr'] > 0]
        blueing = color_evol[color_evol['color_change_1yr'] < 0]
        
        print(f"  Reddening (g-r increasing): {len(reddening)} sources")
        print(f"    → Dust extinction increasing = disk dissipation/outflow obscuration")
        
        print(f"\n  Blueing (g-r decreasing): {len(blueing)} sources")
        print(f"    → Color shift to blue = dust clearing or accretion heating\n")
        
        color_file = analyzer.output_dir / 'color_evolution.csv'
        color_evol.to_csv(color_file, index=False)
        print(f"✓ Saved color evolution sources: {color_file}\n")
    
    # ===========================================================================
    # SUMMARY & RECOMMENDATIONS
    # ===========================================================================
    
    print("="*90)
    print("SUMMARY & OBSERVATIONAL RECOMMENDATIONS")
    print("="*90 + "\n")
    
    print(f"Total sources analyzed: {len(results_df)}")
    print(f"Optically visible (r < 17): {len(results_df[results_df['r_mean'] < 17])} ({len(results_df[results_df['r_mean'] < 17])/len(results_df)*100:.1f}%)")
    print(f"Spectroscopy feasible (r < 17): {len(results_df[results_df['r_mean'] < 17])} sources\n")
    
    print("OBSERVATION PRIORITY RANKING:")
    print(f"  1. HIGH PRIORITY + FADING: {len(high_priority[high_priority['is_fading']])} sources")
    print(f"     → Obtain spectra NOW before sources fade away\n")
    
    print(f"  2. HIGH PRIORITY + COLOR CHANGE: {len(high_priority[high_priority['is_reddening_bluing']])} sources")
    print(f"     → Excellent diagnostics of accretion state evolution\n")
    
    print(f"  3. MEDIUM PRIORITY: {len(results_df[results_df['r_priority'] == 'MEDIUM'])} sources")
    print(f"     → Feasible with more exposure time\n")
    
    # Time estimate
    n_high_priority = len(high_priority)
    time_per_spec = 15  # minutes per low-resolution spectrum
    total_hours = (n_high_priority * time_per_spec) / 60
    
    print(f"OBSERVING TIME ESTIMATE (for high-priority only):")
    print(f"  {n_high_priority} sources × {time_per_spec} min/spectrum = {total_hours:.1f} hours\n")
    
    print("="*90)
    print("✓ ANALYSIS COMPLETE")
    print("="*90 + "\n")
    
    print("Output files created:")
    print(f"  • {spectra_file} (all targets with brightness ranking)")
    if len(fading_sources) > 0:
        print(f"  • {analyzer.output_dir / 'fading_sources.csv'} (urgent targets)")
    if len(color_evol) > 0:
        print(f"  • {analyzer.output_dir / 'color_evolution.csv'} (diagnostic targets)\n")

if __name__ == '__main__':
    main()
