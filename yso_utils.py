import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, List

def parse_mrt_file(filepath: str) -> pd.DataFrame:
    """
    Parse MRT table format for different paper sources.
    Handles Papers B & C format (Tab-separated with J/L prefixed objects).
    """
    data = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        if line.startswith('J') or line.startswith('L'):
            parts = line.split()
            if len(parts) >= 16:
                try:
                    data.append({
                        'Objname': parts[0],
                        'RAdeg': float(parts[1]),
                        'DEdeg': float(parts[2]),
                        'SED_SLOPE': float(parts[3]) if parts[3] != '?' else np.nan,
                        'YSO_CLASS': parts[4],
                        'Number': int(parts[5]),
                        'W2magMean': float(parts[6]),
                        'W2magMed': float(parts[7]),
                        'sig_W2Flux': float(parts[8]),
                        'err_W2Flux': float(parts[9]),
                        'delW2mag': float(parts[10]),
                        'Period': float(parts[11]),
                        'FLP_LSP_BOOT': float(parts[12]),
                        'slope': float(parts[13]),
                        'e_slope': float(parts[14]),
                        'r_value': float(parts[15]),
                        'LCType': parts[-1] if len(parts) > 21 else 'Unknown'
                    })
                except (ValueError, IndexError):
                    continue
    
    return pd.DataFrame(data)

def compute_correlation_matrix(df: pd.DataFrame, columns: List[str] = None) -> pd.DataFrame:
    """
    Compute Pearson correlation matrix for specified columns.
    Handles NaN values by dropping rows with missing data.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    subset = df[columns].dropna()
    return subset.corr()

def categorize_variability(df: pd.DataFrame, col: str = 'delW2mag') -> pd.Series:
    """
    Categorize sources by variability amplitude.
    Low: < 0.2 mag, Medium: 0.2-0.5 mag, High: > 0.5 mag
    """
    categories = []
    for val in df[col]:
        if pd.isna(val):
            categories.append('Unknown')
        elif val < 0.2:
            categories.append('Low')
        elif val < 0.5:
            categories.append('Medium')
        else:
            categories.append('High')
    return pd.Series(categories, index=df.index)

def create_contingency_table(df: pd.DataFrame, col1: str, col2: str) -> pd.DataFrame:
    """
    Create contingency table for two categorical variables.
    """
    return pd.crosstab(df[col1], df[col2])

def normalize_for_chord(matrix: pd.DataFrame) -> np.ndarray:
    """
    Normalize contingency/correlation matrix for chord diagram visualization.
    Converts to symmetric matrix compatible with Cachai chord diagrams.
    """
    n1, n2 = matrix.shape
    matrix_size = n1 + n2
    normalized = np.zeros((matrix_size, matrix_size))
    
    matrix_norm = matrix.astype(float) / matrix.max().max()
    
    for i in range(n1):
        for j in range(n2):
            normalized[i, n1 + j] = matrix_norm.iloc[i, j]
            normalized[n1 + j, i] = matrix_norm.iloc[i, j]
    
    return normalized

def get_summary_statistics(df: pd.DataFrame) -> Dict:
    """
    Generate summary statistics for the dataset.
    """
    stats = {
        'total_objects': len(df),
        'yso_classes': df['YSO_CLASS'].value_counts().to_dict() if 'YSO_CLASS' in df.columns else {},
        'lc_types': df['LCType'].value_counts().to_dict() if 'LCType' in df.columns else {},
        'mean_w2_mag': df['W2magMean'].mean() if 'W2magMean' in df.columns else np.nan,
        'std_w2_mag': df['W2magMean'].std() if 'W2magMean' in df.columns else np.nan,
        'mean_variability': df['delW2mag'].mean() if 'delW2mag' in df.columns else np.nan,
        'std_variability': df['delW2mag'].std() if 'delW2mag' in df.columns else np.nan,
    }
    return stats
