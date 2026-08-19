"""
Heatmap implementation.
"""
import numpy as np
from typing import Optional, List, Union, Dict, Any
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Make seaborn optional
try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    sns = None

from src.infrastructure.charting.matplotlib_engine import MatplotlibEngine


class Heatmap:
    """
    Heatmap generator for correlation matrices and 2D data.
    """
    
    def __init__(self, engine: Optional[MatplotlibEngine] = None):
        self.engine = engine or MatplotlibEngine()
    
    def render(
        self,
        data: Union[List[List], np.ndarray],
        x_labels: Optional[List] = None,
        y_labels: Optional[List] = None,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        cmap: str = "viridis",
        annotate: bool = True,
        annotate_fmt: str = ".2f",
        vmin: Optional[float] = None,
        vmax: Optional[float] = None,
        center: Optional[float] = None,
        square: bool = True,
        **kwargs,
    ) -> Figure:
        """
        Render a heatmap.
        """
        fig, ax = self.engine.create_figure(**kwargs)
        
        data_array = np.array(data)
        
        # Create heatmap
        im = ax.imshow(
            data_array,
            cmap=cmap,
            aspect='auto' if not square else 'equal',
            vmin=vmin,
            vmax=vmax,
        )
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        
        # Set labels
        if x_labels:
            ax.set_xticks(np.arange(len(x_labels)))
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
        
        if y_labels:
            ax.set_yticks(np.arange(len(y_labels)))
            ax.set_yticklabels(y_labels)
        
        # Add annotations
        if annotate:
            for i in range(data_array.shape[0]):
                for j in range(data_array.shape[1]):
                    value = data_array[i, j]
                    text_color = 'white' if abs(value) > (vmax or data_array.max()) / 2 else 'black'
                    ax.text(
                        j, i,
                        format(value, annotate_fmt),
                        ha="center", va="center",
                        color=text_color,
                        fontsize=9,
                    )
        
        self._apply_labels(ax, title, xlabel, ylabel)
        
        fig.tight_layout()
        
        return fig
    
    def render_correlation_matrix(
        self,
        data: Union[List[List], np.ndarray],
        columns: Optional[List[str]] = None,
        title: str = "Correlation Matrix",
        method: str = "pearson",
        **kwargs,
    ) -> Figure:
        """
        Render a correlation matrix heatmap.
        """
        import pandas as pd
        
        df = pd.DataFrame(data, columns=columns)
        
        if method == 'spearman':
            corr = df.corr(method='spearman')
        elif method == 'kendall':
            corr = df.corr(method='kendall')
        else:
            corr = df.corr(method='pearson')
        
        return self.render(
            data=corr.values,
            x_labels=corr.columns.tolist(),
            y_labels=corr.index.tolist(),
            title=title,
            cmap='RdBu_r',
            center=0,
            vmin=-1,
            vmax=1,
            annotate_fmt=".2f",
            **kwargs,
        )
    
    def render_confusion_matrix(
        self,
        cm: Union[List[List], np.ndarray],
        classes: Optional[List[str]] = None,
        title: str = "Confusion Matrix",
        normalize: bool = False,
        **kwargs,
    ) -> Figure:
        """
        Render a confusion matrix heatmap.
        """
        cm_array = np.array(cm)
        
        if normalize:
            cm_array = cm_array.astype('float') / cm_array.sum(axis=1)[:, np.newaxis]
            annotate_fmt = ".1%"
        else:
            annotate_fmt = "d"
        
        if classes is None:
            classes = [str(i) for i in range(len(cm_array))]
        
        fig, ax = self.engine.create_figure(**kwargs)
        
        im = ax.imshow(cm_array, cmap='Blues')
        plt.colorbar(im, ax=ax)
        
        ax.set_xticks(np.arange(len(classes)))
        ax.set_xticklabels(classes)
        ax.set_yticks(np.arange(len(classes)))
        ax.set_yticklabels(classes)
        
        # Add annotations
        for i in range(cm_array.shape[0]):
            for j in range(cm_array.shape[1]):
                value = cm_array[i, j]
                if normalize:
                    text = f"{value:.1%}"
                else:
                    text = str(int(value))
                
                ax.text(
                    j, i, text,
                    ha="center", va="center",
                    color='white' if value > cm_array.max() / 2 else 'black',
                )
        
        ax.set_xlabel('Predicted', fontsize=12)
        ax.set_ylabel('Actual', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        fig.tight_layout()
        
        return fig
    
    def _apply_labels(self, ax, title: str, xlabel: str, ylabel: str) -> None:
        """Apply labels to axes."""
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)