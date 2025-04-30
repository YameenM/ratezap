# helpers/utils.py

import streamlit as st


st.markdown("""
    <style>
    /* Reduce padding of main app container */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* Reduce spacing between components */
    .stContainer > div {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
    }

    /* Tighten gaps between sections */
    section.main > div {
        gap: 0.6rem !important;
    }

    /* Reduce margins under headings */
    h1, h2, h3, h4, h5 {
        margin-top: 0.4rem;
        margin-bottom: 0.6rem;
    }

    /* Reduce margin under expander */
    .stExpander > div {
        margin-bottom: 0.4rem;
    }
    </style>
""", unsafe_allow_html=True)



def hide_streamlit_ui():
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)
