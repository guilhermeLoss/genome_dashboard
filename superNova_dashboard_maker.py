import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="SuperNova Dashboard", layout="wide")

# Header with Home button
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("### 🧬 SuperNova Genome Assembler Dashboard")
with col2:
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown("""
<style>
    .big-font {
        font-size:20px !important;
    }
</style>
""", unsafe_allow_html=True)

with st.expander("ℹ️ About this Dashboard"):
    st.markdown("""
    - This dashboard helps visualize annotated bacterial genomes.
    - Genes are grouped into functional categories (PGPT).
    - The default view uses `PGPT_CATEGORY_3`, but you can change the grouping.
    - Tables and graphics can be downloaded or filtered.
    """)

uploaded_file = st.file_uploader("📤 Upload the SuperNova Genome Assembler annotation table (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Annotation")
    except Exception:
        st.error("❌ Error reading the 'Annotation' sheet. Please check your spreadsheet.")
        st.stop()

    st.markdown("### 🔎 Keyword Search")
    search_keyword = st.text_input("Enter a search term (e.g., Insecticidal, Fungicidal, Nitrogen, Iron, etc):")

    try:
        if search_keyword:
            df_filtered = df[df.apply(lambda row: row.astype(str).str.contains(search_keyword, case=False, na=False).any(), axis=1)]
            if df_filtered.empty:
                st.warning(f"No results found for: '{search_keyword}'.")
        else:
            df_filtered = df.copy()
    except Exception:
        st.error(f"Error processing search term '{search_keyword}'.")
        df_filtered = pd.DataFrame()

    if not df_filtered.empty:
        st.markdown("### 📈 Treemap Visualization")

        pgpt_options = [f"PGPT_CATEGORY_{i}" for i in range(1, 7) if f"PGPT_CATEGORY_{i}" in df.columns]
        default_index = pgpt_options.index("PGPT_CATEGORY_3") if "PGPT_CATEGORY_3" in pgpt_options else 0
        grouping_column = st.selectbox("📊 Grouping level (PGPT):", pgpt_options, index=default_index)

        def clean_gene_name(name):
            return re.sub(r'(_\d+)$', '', str(name))

        def aggregate_gene_names(sub_df):
            raw_names = []
            for col in ["Gene_Name"]:
                if col in sub_df.columns:
                    raw_names += sub_df[col].dropna().astype(str).tolist()
            clean_names = {clean_gene_name(n) for n in raw_names}
            return ", ".join(sorted(clean_names))

        grouped = df_filtered.groupby(grouping_column).agg(Count=(grouping_column, "size")).reset_index()
        gene_dict = df_filtered.groupby(grouping_column).apply(aggregate_gene_names)
        grouped["Genes"] = grouped[grouping_column].map(gene_dict)

        fig = px.treemap(
            grouped,
            path=[grouping_column],
            values="Count",
            hover_data={"Genes": True},
            color="Count",
            color_continuous_scale="Tealgrn"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 🧬 Filtered Genes Table")

        selected_value = st.selectbox(
            "📌 Select a category (optional):",
            options=["Show all"] + grouped[grouping_column].tolist()
        )

        if selected_value != "Show all":
            df_result = df_filtered[df_filtered[grouping_column] == selected_value]
            st.markdown(f"#### 🔬 Genes in selected category: `{selected_value}`")
        else:
            df_result = df_filtered

        st.dataframe(df_result, use_container_width=True)

        # Summary section
        st.markdown("### 📋 Summary Table")
        if not df_result.empty:
            summary_df = pd.DataFrame()
            summary_df["Gene_Name"] = df_result["Gene_Name"].fillna("-")

            synonyms = []
            for idx, row in df_result.iterrows():
                gene_names = []
                for col in ["GENE", "eggnog_Preferred_name"]:
                    if col in df_result.columns and pd.notna(row.get(col)):
                        gene_names.append(str(row.get(col)))
                gene_names = list(set(gene_names))  # Remove duplicates
                synonyms.append(", ".join(gene_names) if gene_names else "-")
            summary_df["Synonymous Gene Names"] = synonyms

            summary_df["Gene_Product"] = df_result["Gene_Product"].fillna("-") if "Gene_Product" in df_result.columns else "-"

            # Feature column now uses selected category value
            summary_df["Feature"] = selected_value if selected_value != "Show all" else df_result[grouping_column].fillna("-")

            st.dataframe(summary_df, use_container_width=True)
        else:
            st.info("No summary data to display.")
    else:
        st.info("⚠️ No data available to display.")
