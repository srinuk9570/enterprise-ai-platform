"""
Chart canvas component for rendering and interacting with charts.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import json


@dataclass
class ChartConfig:
    """Chart configuration."""
    chart_type: str = "line"
    title: str = ""
    x_axis: str = ""
    y_axis: List[str] = None
    color_scheme: str = "default"
    show_legend: bool = True
    show_grid: bool = True
    height: int = 400
    width: Optional[int] = None
    
    def __post_init__(self):
        if self.y_axis is None:
            self.y_axis = []


class ChartCanvas:
    """
    Interactive chart canvas component with Plotly.
    """
    
    def __init__(self, key: str = "chart_canvas"):
        self.key = key
        self._fig: Optional[go.Figure] = None
    
    def render(
        self,
        data: pd.DataFrame,
        config: Optional[ChartConfig] = None,
        on_select: Optional[Callable] = None,
    ) -> None:
        """
        Render the chart canvas.
        """
        config = config or ChartConfig()
        
        # Create figure based on chart type
        if config.chart_type == "line":
            self._fig = self._create_line_chart(data, config)
        elif config.chart_type == "bar":
            self._fig = self._create_bar_chart(data, config)
        elif config.chart_type == "scatter":
            self._fig = self._create_scatter_chart(data, config)
        elif config.chart_type == "area":
            self._fig = self._create_area_chart(data, config)
        elif config.chart_type == "pie":
            self._fig = self._create_pie_chart(data, config)
        elif config.chart_type == "heatmap":
            self._fig = self._create_heatmap(data, config)
        else:
            self._fig = self._create_line_chart(data, config)
        
        # Apply layout
        self._apply_layout(config)
        
        # Render chart
        st.plotly_chart(
            self._fig,
            use_container_width=True,
            key=self.key,
            on_select=on_select,
        )
    
    def _create_line_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create line chart."""
        fig = go.Figure()
        
        x_col = config.x_axis or data.columns[0]
        y_cols = config.y_axis or data.select_dtypes(include=["number"]).columns[:3].tolist()
        
        for col in y_cols:
            if col in data.columns:
                fig.add_trace(go.Scatter(
                    x=data[x_col],
                    y=data[col],
                    mode="lines+markers",
                    name=col,
                ))
        
        return fig
    
    def _create_bar_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create bar chart."""
        fig = go.Figure()
        
        x_col = config.x_axis or data.columns[0]
        y_cols = config.y_axis or data.select_dtypes(include=["number"]).columns[:3].tolist()
        
        for col in y_cols:
            if col in data.columns:
                fig.add_trace(go.Bar(
                    x=data[x_col],
                    y=data[col],
                    name=col,
                ))
        
        return fig
    
    def _create_scatter_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create scatter chart."""
        fig = go.Figure()
        
        x_col = config.x_axis or data.columns[0]
        y_cols = config.y_axis or data.select_dtypes(include=["number"]).columns[:1].tolist()
        
        if y_cols:
            fig.add_trace(go.Scatter(
                x=data[x_col],
                y=data[y_cols[0]],
                mode="markers",
                name=y_cols[0],
                marker=dict(size=10),
            ))
        
        return fig
    
    def _create_area_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create area chart."""
        fig = go.Figure()
        
        x_col = config.x_axis or data.columns[0]
        y_cols = config.y_axis or data.select_dtypes(include=["number"]).columns[:3].tolist()
        
        for col in y_cols:
            if col in data.columns:
                fig.add_trace(go.Scatter(
                    x=data[x_col],
                    y=data[col],
                    mode="lines",
                    fill="tozeroy",
                    name=col,
                ))
        
        return fig
    
    def _create_pie_chart(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create pie chart."""
        fig = go.Figure()
        
        names_col = config.x_axis or data.columns[0]
        values_col = config.y_axis[0] if config.y_axis else data.select_dtypes(include=["number"]).columns[0]
        
        fig.add_trace(go.Pie(
            labels=data[names_col],
            values=data[values_col],
            hole=0.3,
        ))
        
        return fig
    
    def _create_heatmap(self, data: pd.DataFrame, config: ChartConfig) -> go.Figure:
        """Create heatmap."""
        numeric_data = data.select_dtypes(include=["number"])
        
        fig = go.Figure(data=go.Heatmap(
            z=numeric_data.corr().values,
            x=numeric_data.columns,
            y=numeric_data.columns,
            colorscale=config.color_scheme if config.color_scheme != "default" else "RdBu",
        ))
        
        return fig
    
    def _apply_layout(self, config: ChartConfig) -> None:
        """Apply layout configuration."""
        if self._fig is None:
            return
        
        self._fig.update_layout(
            title=config.title if config.title else None,
            height=config.height,
            width=config.width,
            showlegend=config.show_legend,
            template="plotly_dark",
            hovermode="x unified",
        )
        
        self._fig.update_xaxes(showgrid=config.show_grid, title=config.x_axis if config.x_axis else None)
        self._fig.update_yaxes(showgrid=config.show_grid)
    
    def render_from_config(
        self,
        config: Dict[str, Any],
        data_source: Optional[pd.DataFrame] = None,
    ) -> None:
        """
        Render chart from saved configuration.
        """
        if data_source is None:
            # Try to load from session
            data_source = st.session_state.get("chart_data")
            if data_source:
                data_source = pd.DataFrame(data_source)
        
        if data_source is None:
            st.warning("No data available for chart")
            return
        
        chart_config = ChartConfig(
            chart_type=config.get("chart_type", "line"),
            title=config.get("title", ""),
            x_axis=config.get("x_axis", ""),
            y_axis=config.get("y_axis", []),
            color_scheme=config.get("color_scheme", "default"),
            show_legend=config.get("show_legend", True),
            show_grid=config.get("show_grid", True),
            height=config.get("height", 400),
            width=config.get("width"),
        )
        
        self.render(data_source, chart_config)
    
    def export_image(self, format: str = "png") -> Optional[bytes]:
        """
        Export chart as image.
        """
        if self._fig is None:
            return None
        
        return self._fig.to_image(format=format)
    
    def export_html(self) -> Optional[str]:
        """
        Export chart as HTML.
        """
        if self._fig is None:
            return None
        
        return self._fig.to_html()
    
    def to_dict(self) -> Optional[Dict[str, Any]]:
        """
        Convert figure to dictionary.
        """
        if self._fig is None:
            return None
        
        return self._fig.to_dict()
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> go.Figure:
        """
        Create figure from dictionary.
        """
        return go.Figure(data)
    
    @staticmethod
    def create_empty_figure(message: str = "No data to display") -> go.Figure:
        """
        Create an empty figure with a message.
        """
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20),
        )
        fig.update_layout(
            height=400,
            template="plotly_dark",
        )
        return fig


class ChartControls:
    """Chart control panel component."""
    
    @staticmethod
    def render(data: pd.DataFrame, key_prefix: str = "chart") -> ChartConfig:
        """
        Render chart controls and return configuration.
        """
        st.markdown("**Chart Controls**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            chart_type = st.selectbox(
                "Chart Type",
                ["line", "bar", "scatter", "area", "pie", "heatmap"],
                key=f"{key_prefix}_type",
            )
        
        with col2:
            color_scheme = st.selectbox(
                "Color Scheme",
                ["default", "viridis", "plasma", "inferno", "blues", "reds"],
                key=f"{key_prefix}_color",
            )
        
        # Column selection
        all_cols = data.columns.tolist()
        numeric_cols = data.select_dtypes(include=["number"]).columns.tolist()
        
        col1, col2 = st.columns(2)
        
        with col1:
            x_axis = st.selectbox(
                "X-Axis",
                all_cols,
                key=f"{key_prefix}_x",
            )
        
        with col2:
            if chart_type != "pie":
                y_axis = st.multiselect(
                    "Y-Axis",
                    numeric_cols,
                    default=numeric_cols[:1] if numeric_cols else [],
                    key=f"{key_prefix}_y",
                )
            else:
                y_axis = [st.selectbox(
                    "Values",
                    numeric_cols,
                    key=f"{key_prefix}_y",
                )] if numeric_cols else []
        
        title = st.text_input("Title", key=f"{key_prefix}_title")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            show_legend = st.checkbox("Legend", value=True, key=f"{key_prefix}_legend")
        with col2:
            show_grid = st.checkbox("Grid", value=True, key=f"{key_prefix}_grid")
        with col3:
            height = st.number_input("Height", 300, 800, 400, key=f"{key_prefix}_height")
        
        return ChartConfig(
            chart_type=chart_type,
            title=title,
            x_axis=x_axis,
            y_axis=y_axis,
            color_scheme=color_scheme,
            show_legend=show_legend,
            show_grid=show_grid,
            height=height,
        )