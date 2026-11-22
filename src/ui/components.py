import streamlit as st
def metric_card(label,value,delta=None): st.metric(label,value,delta)
def quality_warning(elections):
    bad=elections[elections.verified==False]
    if not bad.empty: st.warning(f"{len(bad)} election dates are unverified. Verify them against official sources before analysis.")
