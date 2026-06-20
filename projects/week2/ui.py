import streamlit as st
import asyncio
from day18_main import NewsExtractor, NewsProcessor

st.set_page_config(page_title="OmniFeed AI", page_icon="📡", layout="wide")

st.title("📡 OmniFeed: Real-Time Tech Intelligence")
st.markdown("Fetching live news, applying guardrails, and generating AI insights with semantic caching.")

with st.sidebar:
    st.header("Settings")
    threshold = st.slider("Cache Sensitivity (Threshold)", 0.1, 1.0, 0.3, 0.05)
    st.info("Lower threshold = stricter matching. Higher = more loose matches.")
    
    st.divider()
    st.subheader("Cache Management")
    if st.button("Clear Cache"):
        processor = NewsProcessor()
        processor.clear_cache()
        st.success("Cache cleared successfully!")

if st.button("Start Intelligence Engine"):
    
    status_placeholder = st.empty()
    results_container = st.container()

    async def run_pipeline():
        status_placeholder.info("Phase 1: Fetching live RSS feeds asynchronously...")
        
        extractor = NewsExtractor()
        ingestion_result = await extractor.initiate_fetch()
        
        if not ingestion_result.articles:
            status_placeholder.error("Failed to fetch any articles. Check your internet connection.")
            return

        status_placeholder.success(f"Fetched {ingestion_result.total_fetched} articles. Starting AI Processing...")
        
        processor = NewsProcessor()
        processor.threshold = threshold 
        
        insights = []
        progress_bar = st.progress(0)
        
        for i, article in enumerate(ingestion_result.articles):
            progress_bar.progress((i + 1) / len(ingestion_result.articles))
            
            with results_container:
                with st.expander(f" [{article.source}] {article.title}", expanded=False):
                    st.write(f"**Original Summary:** {article.summary}")
                    
                    result = await processor.process_article(article)
                    
                    if result:
                        st.success(f"**AI Insight:** {result}")
                        insights.append(result)
                    else:
                        st.warning("Skipped (Guardrail or Cache Hit)")

        progress_bar.empty()
        status_placeholder.success(f"Pipeline Complete! Generated {len(insights)} unique insights.")

    asyncio.run(run_pipeline())

else:
    st.info("Click the button above to start the live data pipeline.")