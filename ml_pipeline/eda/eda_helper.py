import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from typing import List, Optional
import warnings

from ml_config import MLConfig

warnings.filterwarnings("ignore")

class EdaHelper:
    """Herramientas para análisis exploratorio de datos de propiedades en Amsterdam"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
    
    def plot_distribution(self, column: str, figsize: tuple = (12, 5)) -> None:
        """
        Graficar histograma con KDE y QQ-plot para evaluar normalidad.
        
        Args:
            column: Nombre de la columna a analizar
            figsize: Tamaño de la figura (ancho, alto)
        """
        
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        # Histograma con KDE
        sns.histplot(self.data[column], bins=30, kde=True, ax=axes[0])
        axes[0].set_title(f'Distribución de {column}')
        axes[0].set_xlabel(column)
        axes[0].set_ylabel('Frecuencia')
        
        # Gráfico QQ
        stats.probplot(self.data[column].dropna(), dist="norm", plot=axes[1])
        axes[1].set_title(f'Gráfico QQ de {column}')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_counts(self, column: str, top_n: int = 10) -> None:
        """
        Graficar gráfico de barras de los N valores más frecuentes.
        
        Args:
            column: Nombre de la columna categórica
            top_n: Número de valores más frecuentes a mostrar
        """
        
        counts = self.data[column].value_counts().head(top_n)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x=counts.index, y=counts.values, palette='viridis')
        plt.title(f'Top {top_n} {column} por Frecuencia')
        plt.xlabel(column)
        plt.ylabel('Count')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
    
    def plot_boxplot_by_category(self, categorical_col: str, numerical_col: str, top_n: int = 10) -> None:
        """
        Graficar boxplot de variable numérica agrupada por categorías.
        
        Args:
            categorical_col: Columna categórica para agrupar
            numerical_col: Columna numérica a analizar
            top_n: Número de categorías principales a mostrar
        """
        
        data_clean = self.data.dropna(subset=[categorical_col, numerical_col])
        
        if data_clean.empty:
            print(f"No hay datos válidos para '{categorical_col}' o '{numerical_col}'")
            return
        
        top_categories = data_clean[categorical_col].value_counts().head(top_n).index
        filtered_data = data_clean[data_clean[categorical_col].isin(top_categories)]
        
        category_order = (filtered_data.groupby(categorical_col)[numerical_col]
                         .median()
                         .sort_values(ascending=False)
                         .index)
        
        plt.figure(figsize=(12, 6))
        sns.boxplot(x=categorical_col, y=numerical_col, 
                   data=filtered_data, order=category_order, palette='Set2')
        plt.title(f'{numerical_col} por {categorical_col}')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
    
    def plot_correlation_heatmap(self, columns: List[str], figsize: tuple = (12, 8)) -> None:
        """
        Graficar mapa de calor de correlación para variables numéricas.
        
        Args:
            columns: Lista de columnas numéricas a correlacionar
            figsize: Tamaño de la figura (ancho, alto)
        """
        
        corr_matrix = self.data[columns].corr().round(2)
        
        plt.figure(figsize=figsize)
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
        plt.title('Matriz de Correlación')
        plt.tight_layout()
        plt.show()
    
    def calculate_vif(self, columns: List[str]) -> pd.DataFrame:
        """
        Calcular Factor de Inflación de Varianza para detectar multicolinealidad.
        Donde:
            VIF > 10: Multicolinealidad alta
            VIF > 5: Multicolinealidad moderada
            VIF < 5: Multicolinealidad baja
        
        Args:
            columns: Lista de columnas numéricas para calcular VIF
            
        Returns:
            DataFrame con columnas ['Variable', 'VIF']
        """
        
        data_clean = self.data[columns].dropna()
        
        vif_data = pd.DataFrame()
        vif_data["Variable"] = columns
        vif_data["VIF"] = [variance_inflation_factor(data_clean.values, i) 
                           for i in range(len(columns))]
        
        vif_sorted = vif_data.sort_values('VIF', ascending=False)
        
        print("Factor de Inflación de Varianza (VIF)")
        for idx, row in vif_sorted.iterrows():
            vif_value = row['VIF']
            warning = ""
            if vif_value > 10:
                warning = " -> ALTA multicolinealidad"
            elif vif_value > 5:
                warning = " -> MODERADA multicolinealidad"
            print(f"{row['Variable']:30s}: {vif_value:8.2f}{warning}")
        
        return vif_sorted
    
    def summary_statistics(self, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Generar estadísticas resumidas para columnas numéricas.
        
        Args:
            columns: Lista de columnas a resumir (None para todas las numéricas)
            
        Returns:
            DataFrame con estadísticas descriptivas
        """
        
        if columns is None:
            columns = self.data.select_dtypes(include=[np.number]).columns.tolist()
        
        summary = self.data[columns].describe().T
        summary['missing'] = self.data[columns].isnull().sum()
        summary['missing_pct'] = (summary['missing'] / len(self.data) * 100).round(2)
        
        return summary
    
    def plot_price_per_sqm_by_neighborhood(self) -> None:
        """
        Graficar precio por metro cuadrado por barrio.
        Crea la columna price_per_sqm si no existe.
        """
        
        if 'price_per_sqm' not in self.data.columns:
            if 'price' in self.data.columns and 'living_area' in self.data.columns:
                self.data['price_per_sqm'] = self.data['price'] / self.data['living_area']
        
        data_clean = self.data.dropna(subset=['neighborhood', 'price_per_sqm'])
        
        neighborhood_stats = (data_clean.groupby('neighborhood')['price_per_sqm']
                             .agg(['median', 'count'])
                             .sort_values('median', ascending=False)
                             .head(15))
        
        plt.figure(figsize=(12, 6))
        plt.barh(neighborhood_stats.index, neighborhood_stats['median'], color='steelblue')
        plt.xlabel('Precio Medio por m² (€)')
        plt.ylabel('Barrio')
        plt.title('Top 15 Barrios por Precio por Metro Cuadrado')
        plt.tight_layout()
        plt.show()
    
    def plot_scatter_matrix(self, columns: List[str], figsize: tuple = (12, 12)) -> None:
        """
        Pair plot (scatter matrix) para explorar relaciones entre múltiples variables.
        Útil para detectar relaciones lineales/no lineales, outliers multivariados
        y visualizar distribuciones bivariadas.
        
        Args:
            columns: Lista de columnas numéricas a incluir
            figsize: Tamaño de la figura (ancho, alto)
        """
        import seaborn as sns
        
        data_subset = self.data[columns].dropna()
        
        sns.pairplot(data_subset, diag_kind='kde', corner=True, 
                     plot_kws={'alpha': 0.6}, diag_kws={'linewidth': 2})
        plt.suptitle('Matriz de Dispersión - Relaciones entre Variables', y=1.02)
        plt.tight_layout()
        plt.show()
    
    def plot_boolean_boxplots(self, bool_columns: List[str], target: str = 'price', 
                              figsize: tuple = None) -> None:
        """
        Boxplots de variable target por cada feature booleana.
        Útil para comparar distribución de precio según presencia/ausencia de amenidades.
        
        Args:
            bool_columns: Columnas booleanas (ej: has_garden, has_balcony)
            target: Variable objetivo a comparar
            figsize: Tamaño de la figura (None para automático)
        """
        # Filtrar solo columnas que existen
        available_cols = [col for col in bool_columns if col in self.data.columns]
        
        if not available_cols:
            print(f"Las columnas booleanas no están disponibles: {bool_columns}")
            return
        
        n_cols = len(available_cols)
        
        if figsize is None:
            figsize = (5 * min(n_cols, 3), 5 * ((n_cols + 2) // 3))
        
        # Crear grid de subplots
        n_filas = (n_cols + 2) // 3
        n_subplot_cols = min(n_cols, 3)
        
        fig, axes = plt.subplots(n_filas, n_subplot_cols, figsize=figsize)
        axes = axes.flatten() if n_cols > 1 else [axes]
        
        for i, col in enumerate(available_cols):
            data_plot = self.data[[col, target]].dropna()
            sns.boxplot(data=data_plot, x=col, y=target, ax=axes[i], palette='Set2')
            axes[i].set_title(f'{target} por {col}')
            axes[i].set_xlabel(col.replace('_', ' ').title())
            axes[i].set_ylabel(target.title())
        
        # Ocultar ejes sobrantes
        for j in range(i + 1, len(axes)):
            axes[j].set_visible(False)
        
        plt.suptitle(f'Impacto de Features Booleanas en {target.title()}', y=1.02, fontsize=14)
        plt.tight_layout()
        plt.show()
    
    def plot_scatter(self, x: str, y: str, hue: Optional[str] = None, 
                     figsize: tuple = (10, 6), alpha: float = 0.6) -> None:
        """
        Scatter plot con categorización opcional.
        
        Args:
            x: Variable eje X
            y: Variable eje Y
            hue: Variable categórica para colorear puntos (opcional)
            figsize: Tamaño de la figura (ancho, alto)
            alpha: Transparencia de puntos (0-1)
        """
        plt.figure(figsize=figsize)
        
        if hue and hue in self.data.columns:
            sns.scatterplot(data=self.data, x=x, y=y, hue=hue, alpha=alpha, s=50)
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            sns.scatterplot(data=self.data, x=x, y=y, alpha=alpha, s=50, color='steelblue')
        
        plt.title(f'{y} vs {x}' + (f' por {hue}' if hue else ''))
        plt.xlabel(x)
        plt.ylabel(y)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    def plot_outliers_analysis(self, column: str, method: str = 'IQR', 
                               threshold: float = 1.5, visualize: bool = True) -> dict:
        """
        Detectar y visualizar outliers en una variable numérica.
        
        Args:
            column: Nombre de la columna a analizar
            method: Método de detección ('IQR' o 'zscore')
            threshold: Para IQR: multiplicador (default 1.5). Para zscore: num desviaciones
            visualize: Si True, muestra gráficos de outliers
            
        Returns:
            Diccionario con estadísticas de outliers
        """
        if column not in self.data.columns:
            print(f"ERROR: Columna '{column}' no existe")
            return {}
        
        data_clean = self.data[column].dropna()
        
        if method.lower() == 'iqr':
            Q1 = data_clean.quantile(0.25)
            Q3 = data_clean.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            
            outliers_mask = (data_clean < lower_bound) | (data_clean > upper_bound)
            
        elif method.lower() == 'zscore':
            from scipy import stats as sp_stats
            z_scores = np.abs(sp_stats.zscore(data_clean))
            outliers_mask = z_scores > threshold
            lower_bound = data_clean.mean() - threshold * data_clean.std()
            upper_bound = data_clean.mean() + threshold * data_clean.std()
        else:
            print(f"ERROR: Método '{method}' no válido.")
            return {}
        
        outliers = data_clean[outliers_mask]
        n_outliers = len(outliers)
        pct_outliers = (n_outliers / len(data_clean) * 100)
        
        # Estadísticas
        stats_dict = {
            'column': column,
            'method': method,
            'total_values': len(data_clean),
            'n_outliers': n_outliers,
            'pct_outliers': pct_outliers,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'outlier_values': outliers.tolist()
        }
        
        print(f"ANÁLISIS DE OUTLIERS - {column.upper()} (Método {method.upper()})")
        if method.lower() == 'iqr':
            print(f"Q1: {Q1:.2f}")
            print(f"Q3: {Q3:.2f}")
            print(f"IQR: {IQR:.2f}")
        print(f"Límite inferior: {lower_bound:.2f}")
        print(f"Límite superior: {upper_bound:.2f}")
        print(f"\nOutliers detectados: {n_outliers} ({pct_outliers:.1f}%)")
        
        # Visualización
        if visualize and n_outliers > 0:
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            
            # Boxplot
            axes[0].boxplot(data_clean, vert=False)
            axes[0].axvline(lower_bound, color='red', linestyle='--', label='Bounds')
            axes[0].axvline(upper_bound, color='red', linestyle='--')
            axes[0].scatter(outliers, [1]*len(outliers), color='red', s=50, 
                          alpha=0.6, label=f'Outliers ({n_outliers})')
            axes[0].set_xlabel(column)
            axes[0].set_title(f'Diagrama de Caja - {column}')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # Scatter plot con outliers destacados
            indices = data_clean.index
            colors = ['red' if outlier else 'steelblue' 
                     for outlier in outliers_mask]
            axes[1].scatter(range(len(data_clean)), data_clean, 
                          c=colors, alpha=0.6, s=30)
            axes[1].axhline(lower_bound, color='red', linestyle='--', 
                          linewidth=2, label='Bounds')
            axes[1].axhline(upper_bound, color='red', linestyle='--', linewidth=2)
            axes[1].set_xlabel('Indice')
            axes[1].set_ylabel(column)
            axes[1].set_title(f'Outliers Destacados - {column}')
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
        
        return stats_dict
    
    
    def plot_missing_data(self, figsize: tuple = (12, 6)) -> pd.DataFrame:
        """
        Visualizar y analizar datos faltantes.
        
        Args:
            figsize: Tamaño de la figura (ancho, alto)
            
        Returns:
            DataFrame con estadísticas de missing data
        """
        missing_count = self.data.isnull().sum()
        missing_pct = (missing_count / len(self.data) * 100).round(2)
        
        missing_df = pd.DataFrame({
            'Column': missing_count.index,
            'Missing_Count': missing_count.values,
            'Missing_Pct': missing_pct.values
        })
        
        missing_df = missing_df[missing_df['Missing_Count'] > 0].sort_values(
            'Missing_Count', ascending=False
        )
        
        if len(missing_df) == 0:
            print("No hay Missing Data.")
            return missing_df
        
        print("Análisis de Missing Data:")
        print(missing_df.to_string(index=False))
        
        # Visualización
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        
        # Gráfico de barras
        colors = ['red' if pct > 50 else 'orange' if pct > 20 else 'gold' 
                 for pct in missing_df['Missing_Pct']]
        axes[0].barh(missing_df['Column'], missing_df['Missing_Pct'], color=colors)
        axes[0].set_xlabel('Porcentaje de Missing Data (%)')
        axes[0].set_title('Missing Data por Columna')
        axes[0].grid(True, alpha=0.3, axis='x')
        
        # Matriz de Missing (muestra)
        sample_size = min(100, len(self.data))
        missing_matrix = self.data.isnull().iloc[:sample_size]
        
        axes[1].imshow(missing_matrix.T, cmap='RdYlGn_r', aspect='auto', interpolation='nearest')
        axes[1].set_yticks(range(len(missing_matrix.columns)))
        axes[1].set_yticklabels(missing_matrix.columns, fontsize=8)
        axes[1].set_xlabel('Índice de Muestra')
        axes[1].set_title(f'Matriz de Missing Data (primeras {sample_size} filas)')
        
        plt.tight_layout()
        plt.show()
        
        return missing_df
    
    def create_derived_features(self, return_df: bool = True) -> pd.DataFrame:
        """
        Crear features derivadas comunes para análisis inmobiliario.
        Features creadas: price_per_sqm, rooms_per_sqm, year_built_category,
        living_area_category, property_age.
        
        Args:
            return_df: Si True, retorna DataFrame con nuevas columnas
            
        Returns:
            DataFrame con features derivadas
        """
        df = self.data.copy()
        features_created = []
        
        print("CREACIÓN DE FEATURES DERIVADAS")
        
        # Precio por m²
        if 'price' in df.columns and 'living_area' in df.columns:
            df['price_per_sqm'] = df['price'] / df['living_area']
            features_created.append('price_per_sqm')
            print("Creado: price_per_sqm")
        
        # Rooms per m²
        if 'rooms' in df.columns and 'living_area' in df.columns:
            df['rooms_per_sqm'] = df['rooms'] / df['living_area']
            features_created.append('rooms_per_sqm')
            print("Creado: rooms_per_sqm")
        
        # Year built categories
        if 'year_built' in df.columns:
            bins = [0, 1945, 1975, 2000, 2024]
            labels = ['Pre-1945', '1945-1975', '1975-2000', 'Post-2000']
            df['year_built_category'] = pd.cut(df['year_built'], bins=bins, labels=labels)
            features_created.append('year_built_category')
            print("Creado: year_built_category")
        
        # Living area categories
        if 'living_area' in df.columns:
            bins = [0, 50, 100, 150, 1000]
            labels = ['Small (<50m²)', 'Medium (50-100m²)', 'Large (100-150m²)', 'Very Large (>150m²)']
            df['living_area_category'] = pd.cut(df['living_area'], bins=bins, labels=labels)
            features_created.append('living_area_category')
            print("Creado: living_area_category")
        
        # Property age
        if 'year_built' in df.columns:
            current_year = MLConfig.CURRENT_YEAR
            df['property_age'] = current_year - df['year_built']
            features_created.append('property_age')
            print("Creado: property_age")
        
        print(f"Total features creadas: {len(features_created)}")
        
        if return_df:
            return df
        else:
            self.data = df
            return df
    
    def plot_feature_comparison(self, features: List[str], target: str = 'price',
                               figsize: tuple = None) -> None:
        """
        Comparar impacto de múltiples features categóricas en variable objetivo.
        
        Args:
            features: Lista de columnas categóricas a comparar
            target: Variable objetivo
            figsize: Tamaño de la figura (None para automático)
        """
        available_features = [f for f in features if f in self.data.columns]
        
        if not available_features:
            print(f"ERROR: Ninguna feature disponible: {features}")
            return
        
        n_features = len(available_features)
        
        if figsize is None:
            n_cols = min(3, n_features)
            n_filas = (n_features + n_cols - 1) // n_cols
            figsize = (6 * n_cols, 5 * n_filas)
        
        fig, axes = plt.subplots(n_filas, n_cols, figsize=figsize)
        axes = axes.flatten() if n_features > 1 else [axes]
        
        for i, feature in enumerate(available_features):
            data_clean = self.data[[feature, target]].dropna()
            
            # Calcular medianas y ordenar
            medians = data_clean.groupby(feature)[target].median().sort_values(ascending=False)
            
            sns.boxplot(data=data_clean, x=feature, y=target, 
                       order=medians.index, ax=axes[i], palette='Set2')
            axes[i].set_title(f'{target.title()} por {feature}')
            axes[i].set_xlabel(feature.replace('_', ' ').title())
            axes[i].set_ylabel(target.title())
            axes[i].tick_params(axis='x', rotation=45)
        
        # Ocultar ejes sobrantes
        for j in range(i + 1, len(axes)):
            axes[j].set_visible(False)
        
        plt.suptitle(f'Comparación de Impacto de Features en {target.title()}', 
                    y=1.02, fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show()
