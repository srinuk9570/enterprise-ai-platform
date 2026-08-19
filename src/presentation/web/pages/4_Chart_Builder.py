"""
Streamlit Chart Builder Page.
"""
import streamlit as st
from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.presentation.web.state.session_store import SessionStore


def main():
    """Chart Builder page."""
    
    st.set_page_config(
        page_title="Chart Builder - Enterprise AI Platform",
        page_icon="📈",
        layout="wide",
    )
    
    SessionStore.initialize()
    
    if not st.session_state.get("authenticated"):
        st.warning("⚠️ Please login to access this page.")
        st.stop()
    
    st.title("📈 Chart Builder")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📍 Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("Home.py")
        if st.button("💬 Chat", use_container_width=True):
            st.switch_page("pages/1_Chat.py")
        if st.button("🎨 Image Studio", use_container_width=True):
            st.switch_page("pages/3_Image_Studio.py")
        st.markdown("---")
        
        st.subheader("📊 Chart Settings")
        chart_type = st.selectbox("Chart Type", ["Line Chart", "Bar Chart", "Area Chart"])
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.switch_page("Home.py")
    
    st.markdown("---")
    
    # Data source
    tab1, tab2 = st.tabs(["📁 Upload Data", "📊 Sample Data"])
    
    df = None
    
    with tab1:
        uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx", "xls"])
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.success(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns")
                st.dataframe(df.head(10), use_container_width=True)
            except Exception as e:
                st.error(f"Error loading file: {e}")
    
    with tab2:
        st.info("Sample data ready to use!")
        
        if st.button("Load Sample Sales Data"):
            import numpy as np
            from datetime import datetime, timedelta
            
            dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30, 0, -1)]
            
            df = pd.DataFrame({
                "Date": dates,
                "Sales": np.random.randint(100, 500, 30),
                "Revenue": np.random.randint(1000, 5000, 30),
                "Customers": np.random.randint(10, 50, 30),
            })
            
            st.success("✅ Sample data loaded!")
            st.dataframe(df.head(10), use_container_width=True)
    
    if df is not None:
        st.markdown("---")
        st.subheader("📊 Chart Preview")
        
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        all_cols = df.columns.tolist()
        
        col1, col2 = st.columns(2)
        
        with col1:
            x_axis = st.selectbox("X-Axis", all_cols)
            y_axis = st.selectbox("Y-Axis", numeric_cols)
        
        with col2:
            title = st.text_input("Chart Title", "My Chart")
            color = st.color_picker("Color", "#00d2ff")
        
        if st.button("Generate Chart", type="primary"):
            if chart_type == "Line Chart":
                st.line_chart(df.set_index(x_axis)[y_axis])
            elif chart_type == "Bar Chart":
                st.bar_chart(df.set_index(x_axis)[y_axis])
            else:
                st.area_chart(df.set_index(x_axis)[y_axis])
    else:
        st.info("👆 Please upload a file or load sample data to get started!")


if __name__ == "__main__":
    main()