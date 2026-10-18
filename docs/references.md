# Implementation references

Official documentation consulted for the local implementation:

- Polars Parquet I/O: https://docs.pola.rs/user-guide/io/parquet/
- Streamlit application testing: https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest

The project uses Polars for data preparation and SQL for mart construction. SciPy and Statsmodels receive NumPy arrays. No project code imports pandas; dependencies may use it internally.
