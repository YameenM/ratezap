import streamlit as st

def hide_streamlit_ui():
    user = st.session_state.get("user", {})
    is_admin = user.get("email") == "admin@ratezap.com"

    if not is_admin:
        # Hide UI for regular users
        st.markdown("""
        <style>
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
        }
        header {
            display: none !important;
            visibility: hidden !important;
        }
        .main .block-container {
            padding-top: 1rem !important;
        }
        [title="View fullscreen"] {
            display: none !important;
        }
        </style>

        <script>
        const hideUI = () => {
            const header = window.parent.document.querySelector('header');
            if (header) header.style.display = 'none';

            const toggle = window.parent.document.querySelector('[data-testid="collapsedControl"]');
            if (toggle) toggle.style.display = 'none';
        };
        hideUI();
        setTimeout(hideUI, 1000);
        setInterval(hideUI, 3000);
        </script>
        """, unsafe_allow_html=True)
    else:
        # Admin: ensure toggle is visible (in case it was hidden)
        st.markdown("""
        <script>
        const showAdminUI = () => {
            const toggle = window.parent.document.querySelector('[data-testid="collapsedControl"]');
            if (toggle) toggle.style.display = 'block';
        };
        showAdminUI();
        setTimeout(showAdminUI, 1000);
        </script>
        """, unsafe_allow_html=True)
