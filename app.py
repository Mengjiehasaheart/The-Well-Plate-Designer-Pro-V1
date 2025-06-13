"""
Well Plate Designer Pro
Copyright (c) 2024 Mengjie Fan. All rights reserved.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json
import re
import random
import itertools
try:
    from plate_visualizer import PlateVisualizer
    from plate_manager import PlateManager
    from export_manager import ExportManager
except ImportError:
    from well_plate_designer_pro.plate_visualizer import PlateVisualizer
    from well_plate_designer_pro.plate_manager import PlateManager
    from well_plate_designer_pro.export_manager import ExportManager
import plotly.graph_objects as go

st.set_page_config(
    page_title="Well Plate Designer Pro",
    page_icon="⚫",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'version' not in st.session_state:
    st.session_state.version = "0.1.0-dev"
    st.session_state.plates = {}
    st.session_state.current_plate = None
    st.session_state.history = []
    st.session_state.selected_wells = []
    st.session_state.hover_well = None
    st.session_state.color_mode = 'gradient'
    st.session_state.current_gradient = 'high_contrast'
    st.session_state.visualizer = PlateVisualizer()
    st.session_state.visualizer.set_theme('nature')
    st.session_state.manager = PlateManager()
    st.session_state.exporter = ExportManager()
    st.session_state.groups = {}
    st.session_state.current_color_idx = 0
    st.session_state.theme = 'nature'
    st.session_state.show_tutorial = False
    st.session_state.workflow_step = 1
    st.session_state.assignment_mode = 'group'
    st.session_state.manual_assignment_text = ''
    st.session_state.group_colors = {}
    st.session_state.selection_mode = 'Click & Drag'
    st.session_state.quick_fill_group = None

def apply_custom_css():
    theme = st.session_state.visualizer.theme
    
    if st.session_state.theme == 'dark':
        gradient_start = '#818CF8'
        gradient_end = '#F472B6'
        text_color = '#F3F4F6'
        bg_overlay = 'rgba(0, 0, 0, 0.85)'
    elif st.session_state.theme == 'light':
        gradient_start = '#4F46E5'
        gradient_end = '#DB2777'
        text_color = '#111827'
        bg_overlay = 'rgba(255, 255, 255, 0.95)'
    else:
        gradient_start = '#10B981'
        gradient_end = '#059669'
        text_color = '#064E3B'
        bg_overlay = 'rgba(243, 244, 246, 0.95)'
    
    st.markdown(f"""
    <style>
    .stApp {{
        background: {theme['bg']};
    }}
    .main-header {{
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, {gradient_start} 0%, {gradient_end} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }}
    .workflow-step {{
        background: {bg_overlay};
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 2px solid transparent;
        transition: all 0.3s ease;
        color: {text_color};
    }}
    .workflow-step.active {{
        border-color: {theme['primary']};
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.3);
    }}
    .workflow-number {{
        display: inline-flex;
        width: 30px;
        height: 30px;
        background: {theme['primary']};
        color: white;
        border-radius: 50%;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 0.5rem;
    }}
    .help-tip {{
        background: {bg_overlay};
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid {theme['accent']};
        color: {text_color};
    }}
    .quick-action {{
        background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        cursor: pointer;
        transition: transform 0.2s;
    }}
    .quick-action:hover {{
        transform: translateY(-2px);
    }}
    .copyright {{
        position: fixed;
        bottom: 10px;
        right: 10px;
        font-size: 12px;
        color: {theme['muted']};
        opacity: 0.8;
        z-index: 999;
    }}
    .stSelectbox label, .stNumberInput label, .stTextInput label, .stTextArea label {{
        color: {text_color} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def main():
    apply_custom_css()
    
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown('<h1 class="main-header">Well Plate Designer Pro</h1>', unsafe_allow_html=True)
        st.caption(f"v{st.session_state.version}")
    
    with col2:
        theme = st.selectbox(
            "Theme",
            ["dark", "light", "nature"],
            index=["dark", "light", "nature"].index(st.session_state.theme),
            key="theme_selector",
            label_visibility="collapsed"
        )
        if theme != st.session_state.theme:
            st.session_state.theme = theme
            st.session_state.visualizer.set_theme(theme)
            st.rerun()
    
    st.markdown('<div class="copyright">© 2024 Mengjie Fan</div>', unsafe_allow_html=True)
    
    if st.session_state.show_tutorial:
        st.markdown("""
        <div class="help-tip">
        <h4>Quick Start Guide</h4>
        <ol>
        <li><b>Create a Plate</b> - Choose your plate format (24, 48, 96, or 384 wells)</li>
        <li><b>Add Groups</b> - Define your treatments, compounds, or conditions</li>
        <li><b>Assign to Wells</b> - Use smart assignment or drag-select wells</li>
        <li><b>Export</b> - Download as Excel, CSV, or JSON</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
    
    if not st.session_state.current_plate:
        show_plate_creation()
    else:
        show_workflow_sidebar()
        show_plate_workspace()

def show_plate_creation():
    st.markdown("### Step 1: Create Your Plate")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="workflow-step active">
        <div class="workflow-number">1</div>
        <h4>Choose Format</h4>
        <p>Select your plate type</p>
        </div>
        """, unsafe_allow_html=True)
        
        plate_type = st.selectbox(
            "Plate Format",
            ["24-well", "48-well", "96-well", "384-well", "Custom"],
            index=2
        )
        
        if plate_type == "Custom":
            rows = st.number_input("Rows", min_value=1, max_value=32, value=8)
            cols = st.number_input("Columns", min_value=1, max_value=48, value=12)
        else:
            plate_dims = {
                "24-well": (4, 6),
                "48-well": (6, 8),
                "96-well": (8, 12),
                "384-well": (16, 24)
            }
            rows, cols = plate_dims[plate_type]
            st.info(f"Dimensions: {rows} rows × {cols} columns")
    
    with col2:
        st.markdown("""
        <div class="workflow-step">
        <div class="workflow-number">2</div>
        <h4>Quick Templates</h4>
        <p>Start with a template (optional)</p>
        </div>
        """, unsafe_allow_html=True)
        
        template = st.selectbox(
            "Template",
            ["Blank", "Dose Response", "Time Course", "Checkerboard"],
            help="Pre-configured layouts for common experiments"
        )
    
    with col3:
        st.markdown("""
        <div class="workflow-step">
        <div class="workflow-number">3</div>
        <h4>Create Plate</h4>
        <p>Ready to design!</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        if st.button("Create Plate", type="primary", use_container_width=True):
            create_new_plate(rows, cols, plate_type)
            st.session_state.workflow_step = 2

def show_workflow_sidebar():
    st.sidebar.markdown("### Workflow")
    
    steps = [
        ("1", "Create Plate", st.session_state.current_plate is not None),
        ("2", "Add Groups", len(st.session_state.groups) > 0),
        ("3", "Assign Wells", any(w.get('treatment') for w in st.session_state.plates[st.session_state.current_plate]['wells'].values()) if st.session_state.current_plate else False),
        ("4", "Export", False)
    ]
    
    for num, step, completed in steps:
        if completed:
            st.sidebar.success(f"✓ {step}")
        else:
            st.sidebar.info(f"○ {step}")
    
    st.sidebar.divider()
    
    st.sidebar.markdown("### Groups")
    
    with st.sidebar.expander("Add New Group", expanded=len(st.session_state.groups) == 0):
        with st.form("add_group_form"):
            group_name = st.text_input("Group Name", placeholder="e.g., Control, Drug A")
            items_input = st.text_area(
                "Items (one per line)", 
                placeholder="0 µM\n1 µM\n10 µM\n100 µM",
                height=100
            )
            
            col1, col2 = st.columns(2)
            with col1:
                gradient_colors = st.session_state.visualizer.gradients[st.session_state.current_gradient]
                color_idx = st.session_state.current_color_idx % len(gradient_colors)
                auto_color = gradient_colors[color_idx]
                group_color = st.color_picker("Color", auto_color, key=f"group_color_{st.session_state.current_color_idx}")
            
            with col2:
                st.write("")  # Spacer
                if st.form_submit_button("Add Group", type="primary", use_container_width=True):
                    if group_name:
                        items = [item.strip() for item in items_input.split('\n') if item.strip()]
                        if not items:
                            items = []
                        group = st.session_state.manager.create_group(group_name, items, group_color)
                        st.session_state.groups[group_name] = group
                        st.session_state.group_colors[group_name] = group_color
                        st.session_state.current_color_idx += 1
                        st.session_state.workflow_step = 3
                        st.rerun()
    
    if st.session_state.groups:
        for group_name, group_info in st.session_state.groups.items():
            with st.sidebar.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{group_name}**")
                    st.caption(f"{len(group_info['items'])} items")
                with col2:
                    new_color = st.color_picker("", group_info['color'], key=f"gc_{group_name}", label_visibility="collapsed")
                    if new_color != group_info['color']:
                        st.session_state.groups[group_name]['color'] = new_color
                        st.session_state.group_colors[group_name] = new_color
                        plate = st.session_state.plates[st.session_state.current_plate]
                        for well_id, well in plate['wells'].items():
                            if well.get('treatment') == group_name:
                                well['color'] = new_color
                        st.rerun()
                with col3:
                    if st.button("Delete", key=f"del_{group_name}", help="Delete this group"):
                        del st.session_state.groups[group_name]
                        st.rerun()
    
    st.sidebar.divider()
    
    st.sidebar.markdown("### Quick Actions")
    
    if st.session_state.groups and st.session_state.current_plate:
        if st.sidebar.button("Smart Fill", use_container_width=True, 
                           help="Automatically assign all groups with edge-aware distribution"):
            plate = st.session_state.plates[st.session_state.current_plate]
            updated_plate = st.session_state.manager.assign_treatments(
                plate, st.session_state.groups, 'edge_aware', 3
            )
            st.session_state.plates[st.session_state.current_plate] = updated_plate
            st.rerun()
        
        if st.sidebar.button("Clear All", use_container_width=True):
            plate = st.session_state.plates[st.session_state.current_plate]
            updated_plate = st.session_state.manager.clear_assignments(plate)
            st.session_state.plates[st.session_state.current_plate] = updated_plate
            st.rerun()
    
    if st.session_state.current_plate:
        st.sidebar.divider()
        st.sidebar.markdown("### Export")
        
        export_format = st.sidebar.radio(
            "Format",
            ["Excel", "Excel (Long)", "CSV", "JSON"],
            horizontal=True
        )
        
        if st.sidebar.button("Download", type="primary", use_container_width=True):
            show_export_dialog(export_format)
    
    st.sidebar.divider()
    st.sidebar.markdown("### Unit Converter")
    
    with st.sidebar.expander("Lab Unit Converter"):
        converter_type = st.selectbox(
            "Conversion Type",
            ["Volume", "Concentration", "Mass"]
        )
        
        if converter_type == "Volume":
            col1, col2 = st.columns(2)
            with col1:
                volume_value = st.number_input("Value", min_value=0.0, format="%.6f")
                from_unit = st.selectbox("From", ["µL", "mL", "L"])
            with col2:
                to_unit = st.selectbox("To", ["µL", "mL", "L"])
                
                volume_conversions = {
                    ("µL", "mL"): 0.001,
                    ("µL", "L"): 0.000001,
                    ("mL", "µL"): 1000,
                    ("mL", "L"): 0.001,
                    ("L", "µL"): 1000000,
                    ("L", "mL"): 1000,
                    ("µL", "µL"): 1,
                    ("mL", "mL"): 1,
                    ("L", "L"): 1
                }
                
                converted = volume_value * volume_conversions.get((from_unit, to_unit), 1)
                st.info(f"{volume_value} {from_unit} = {converted:.6f} {to_unit}")
        
        elif converter_type == "Concentration":
            col1, col2 = st.columns(2)
            with col1:
                conc_value = st.number_input("Value", min_value=0.0, format="%.6f")
                from_unit = st.selectbox("From", ["nM", "µM", "mM", "M"])
            with col2:
                to_unit = st.selectbox("To", ["nM", "µM", "mM", "M"])
                
                conc_conversions = {
                    ("nM", "µM"): 0.001,
                    ("nM", "mM"): 0.000001,
                    ("nM", "M"): 0.000000001,
                    ("µM", "nM"): 1000,
                    ("µM", "mM"): 0.001,
                    ("µM", "M"): 0.000001,
                    ("mM", "nM"): 1000000,
                    ("mM", "µM"): 1000,
                    ("mM", "M"): 0.001,
                    ("M", "nM"): 1000000000,
                    ("M", "µM"): 1000000,
                    ("M", "mM"): 1000,
                    ("nM", "nM"): 1,
                    ("µM", "µM"): 1,
                    ("mM", "mM"): 1,
                    ("M", "M"): 1
                }
                
                converted = conc_value * conc_conversions.get((from_unit, to_unit), 1)
                st.info(f"{conc_value} {from_unit} = {converted:.6f} {to_unit}")
        
        elif converter_type == "Mass":
            col1, col2 = st.columns(2)
            with col1:
                mass_value = st.number_input("Value", min_value=0.0, format="%.6f")
                from_unit = st.selectbox("From", ["ng", "µg", "mg", "g"])
            with col2:
                to_unit = st.selectbox("To", ["ng", "µg", "mg", "g"])
                
                mass_conversions = {
                    ("ng", "µg"): 0.001,
                    ("ng", "mg"): 0.000001,
                    ("ng", "g"): 0.000000001,
                    ("µg", "ng"): 1000,
                    ("µg", "mg"): 0.001,
                    ("µg", "g"): 0.000001,
                    ("mg", "ng"): 1000000,
                    ("mg", "µg"): 1000,
                    ("mg", "g"): 0.001,
                    ("g", "ng"): 1000000000,
                    ("g", "µg"): 1000000,
                    ("g", "mg"): 1000,
                    ("ng", "ng"): 1,
                    ("µg", "µg"): 1,
                    ("mg", "mg"): 1,
                    ("g", "g"): 1
                }
                
                converted = mass_value * mass_conversions.get((from_unit, to_unit), 1)
                st.info(f"{mass_value} {from_unit} = {converted:.6f} {to_unit}")

def show_plate_workspace():
    plate = st.session_state.plates[st.session_state.current_plate]
    
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    with col1:
        st.markdown(f"### {plate['type']} Layout")
    with col2:
        total_wells = plate['rows'] * plate['cols']
        filled_wells = sum(1 for w in plate['wells'].values() if w.get('treatment'))
        st.metric("Progress", f"{filled_wells}/{total_wells}")
    with col3:
        utilization = (filled_wells / total_wells * 100) if total_wells > 0 else 0
        st.metric("Utilization", f"{utilization:.0f}%")
    with col4:
        st.metric("Selected", len(st.session_state.selected_wells))
    with col5:
        if st.button("New Plate", use_container_width=True, help="Create a new plate"):
            st.session_state.current_plate = None
            st.session_state.selected_wells = []
            st.rerun()
    
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            well_input = st.text_input(
                "Select wells by text",
                placeholder="e.g., A1-A12, B1, C3-D4, or click wells in the visualization",
                help="Enter well ranges or individual wells separated by commas"
            )
        with col2:
            if st.button("Apply Selection", type="primary", use_container_width=True, disabled=not well_input):
                try:
                    selected_wells = parse_well_selection(well_input, plate['rows'], plate['cols'])
                    st.session_state.selected_wells = selected_wells
                    st.rerun()
                except Exception as e:
                    st.error(f"Invalid selection: {str(e)}")
        with col3:
            if st.button("Clear Selection", use_container_width=True, disabled=not st.session_state.selected_wells):
                st.session_state.selected_wells = []
                st.rerun()
    
    tabs = st.tabs([
        "Group Assignment",
        "Serial Dilution",
        "Compound Mixtures",
        "Combinatorial",
        "Time Course",
        "Dose Response",
        "Custom Pattern"
    ])
    
    with tabs[0]:
        if st.session_state.groups:
            st.markdown("### Assign Wells to Groups")
            
            group_container = st.container()
            with group_container:
                cols = st.columns(len(st.session_state.groups) + 2)
                
                for idx, (group_name, group_info) in enumerate(st.session_state.groups.items()):
                    with cols[idx]:
                        st.markdown(
                            f"""
                            <style>
                            div[data-testid="stButton"] > button[key="grp_{group_name}"] {{
                                background-color: {group_info['color']};
                                color: white;
                            }}
                            </style>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        if st.button(
                            group_name,
                            key=f"grp_{group_name}",
                            use_container_width=True,
                            disabled=not st.session_state.selected_wells,
                            help=f"Click to assign selected wells to {group_name}"
                        ):
                            for well_id in st.session_state.selected_wells:
                                if group_info['items']:
                                    plate['wells'][well_id].update({
                                        'treatment': group_name,
                                        'compound': group_info['items'][0],
                                        'replicate': 1,
                                        'color': group_info['color']
                                    })
                                else:
                                    plate['wells'][well_id].update({
                                        'treatment': group_name,
                                        'compound': group_name,
                                        'replicate': 1,
                                        'color': group_info['color']
                                    })
                            st.session_state.selected_wells = []
                            st.rerun()
                
                with cols[-2]:
                    if st.button("Clear Wells", key="clear_wells_btn", 
                               disabled=not st.session_state.selected_wells,
                               help="Clear selected wells"):
                        for well_id in st.session_state.selected_wells:
                            plate['wells'][well_id].update({
                                'treatment': None,
                                'compound': None,
                                'subject': None,
                                'replicate': None,
                                'color': st.session_state.visualizer.theme['empty']
                            })
                        st.session_state.selected_wells = []
                        st.rerun()
                
                with cols[-1]:
                    if st.button("Deselect", key="deselect_btn",
                               disabled=not st.session_state.selected_wells):
                        st.session_state.selected_wells = []
                        st.rerun()
        else:
            st.info("Add groups in the sidebar to use group assignment")
    
    with tabs[1]:
        st.markdown("### Serial Dilution Setup")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            dilution_compound = st.text_input("Compound Name", placeholder="e.g., Drug A")
            
            col1a, col1b, col1c = st.columns(3)
            with col1a:
                start_conc = st.number_input("Starting Concentration", min_value=0.0, value=1000.0)
            with col1b:
                dilution_factor = st.number_input("Dilution Factor", min_value=1.0, value=2.0)
            with col1c:
                conc_unit = st.selectbox("Unit", ["nM", "µM", "mM", "M", "µg/mL", "mg/mL"])
            
            dilution_steps = st.number_input("Number of Dilution Steps", min_value=2, max_value=12, value=8)
            
            st.markdown("#### Dilution Series Preview:")
            dilution_preview = []
            for i in range(dilution_steps):
                conc = start_conc / (dilution_factor ** i)
                dilution_preview.append(f"{conc:.2f} {conc_unit}")
            st.info(" → ".join(dilution_preview[:5]) + (" → ..." if dilution_steps > 5 else ""))
            
        with col2:
            base_color = st.color_picker("Base Color", "#2563EB")
            include_controls = st.checkbox("Include Control Wells", value=True)
            
            if st.button("Apply Serial Dilution", type="primary", use_container_width=True,
                        disabled=not st.session_state.selected_wells or not dilution_compound):
                gradient_colors = st.session_state.visualizer.generate_dilution_gradient(base_color, dilution_steps)
                
                if len(st.session_state.selected_wells) >= dilution_steps:
                    for i, well_id in enumerate(st.session_state.selected_wells[:dilution_steps]):
                        conc = start_conc / (dilution_factor ** i)
                        plate['wells'][well_id].update({
                            'treatment': 'Serial Dilution',
                            'compound': dilution_compound,
                            'concentration': f"{conc:.2f} {conc_unit}",
                            'replicate': 1,
                            'color': gradient_colors[i]
                        })
                    st.session_state.selected_wells = []
                    st.success(f"Applied {dilution_steps}-step serial dilution")
                    st.rerun()
                else:
                    st.error(f"Please select at least {dilution_steps} wells")
    
    with tabs[2]:
        st.markdown("### Create Compound Mixtures")
        st.info("Select wells and create custom compound mixtures")
        
        if 'current_mixture' not in st.session_state:
            st.session_state.current_mixture = []
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("#### Current Mixture Components")
            
            if st.session_state.current_mixture:
                for idx, component in enumerate(st.session_state.current_mixture):
                    cols = st.columns([3, 2, 2, 1])
                    with cols[0]:
                        st.text_input("Compound", value=component['compound'], key=f"comp_{idx}", disabled=True)
                    with cols[1]:
                        st.text_input("Concentration", value=component['concentration'], key=f"conc_{idx}", disabled=True)
                    with cols[2]:
                        st.text_input("Unit", value=component['unit'], key=f"unit_{idx}", disabled=True)
                    with cols[3]:
                        if st.button("Remove", key=f"remove_{idx}"):
                            st.session_state.current_mixture.pop(idx)
                            st.rerun()
            else:
                st.caption("No components added yet")
            
            st.markdown("#### Add Component")
            with st.form("add_component_form"):
                cols = st.columns([3, 2, 2, 1])
                with cols[0]:
                    compound_name = st.text_input("Compound Name", placeholder="e.g., Drug A")
                with cols[1]:
                    concentration = st.number_input("Concentration", min_value=0.0, step=0.1)
                with cols[2]:
                    unit = st.selectbox("Unit", ["nM", "µM", "mM", "M", "µg/mL", "mg/mL", "%"])
                with cols[3]:
                    st.write("")  # Spacer
                    if st.form_submit_button("Add"):
                        if compound_name:
                            st.session_state.current_mixture.append({
                                'compound': compound_name,
                                'concentration': concentration,
                                'unit': unit
                            })
                            st.rerun()
        
        with col2:
            st.markdown("#### Actions")
            
            if st.button("Assign to Selected Wells", 
                        type="primary",
                        use_container_width=True,
                        disabled=not st.session_state.selected_wells or not st.session_state.current_mixture):
                mixture_label = " + ".join([f"{c['compound']} ({c['concentration']} {c['unit']})" 
                                          for c in st.session_state.current_mixture])
                
                num_wells = len(st.session_state.selected_wells)
                for well_id in st.session_state.selected_wells:
                    plate['wells'][well_id].update({
                        'treatment': 'Mixture',
                        'compound': mixture_label,
                        'compound_mixture': st.session_state.current_mixture.copy(),
                        'replicate': 1,
                        'color': '#9F7AEA'  # Purple color for mixtures
                    })
                
                st.session_state.selected_wells = []
                st.success(f"Mixture assigned to {num_wells} wells")
                st.rerun()
            
            if st.button("Clear Mixture", use_container_width=True, 
                        disabled=not st.session_state.current_mixture):
                st.session_state.current_mixture = []
                st.rerun()
            
            st.divider()
            st.caption("Templates coming soon...")
    
    with tabs[3]:
        st.markdown("### Combinatorial Design")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("Create combinations of multiple factors (e.g., drug combinations)")
            
            n_factors = st.number_input("Number of Factors", min_value=2, max_value=4, value=2)
            
            factors = {}
            for i in range(n_factors):
                st.markdown(f"#### Factor {i+1}")
                factor_name = st.text_input(f"Factor {i+1} Name", placeholder=f"e.g., Drug {chr(65+i)}", key=f"factor_name_{i}")
                factor_levels = st.text_area(
                    f"Levels (one per line)",
                    placeholder="0 µM\n1 µM\n10 µM",
                    key=f"factor_levels_{i}",
                    height=80
                )
                if factor_name and factor_levels:
                    factors[factor_name] = [level.strip() for level in factor_levels.split('\n') if level.strip()]
        
        with col2:
            st.markdown("#### Options")
            include_single = st.checkbox("Include single factors", value=True)
            randomize = st.checkbox("Randomize placement", value=True)
            
            if st.button("Generate Combinations", type="primary", use_container_width=True):
                if len(factors) >= 2:
                    import itertools
                    all_combinations = list(itertools.product(*factors.values()))
                    st.info(f"Generated {len(all_combinations)} combinations")
                    factor_names = list(factors.keys())
                    factor_values = list(factors.values())
                    
                    if len(st.session_state.selected_wells) > 0:
                        wells_to_assign = st.session_state.selected_wells[:]
                        if randomize:
                            random.shuffle(wells_to_assign)
                        
                        colors = st.session_state.visualizer.gradients['high_contrast']
                        
                        for idx, (well_id, combination) in enumerate(zip(wells_to_assign, itertools.cycle(all_combinations))):
                            combo_str = " + ".join([f"{name}: {val}" for name, val in zip(factor_names, combination)])
                            plate['wells'][well_id].update({
                                'treatment': 'Combination',
                                'compound': combo_str,
                                'replicate': (idx // len(all_combinations)) + 1,
                                'color': colors[idx % len(colors)]
                            })
                        
                        st.session_state.selected_wells = []
                        st.success(f"Assigned {len(all_combinations)} combinations to wells")
                        st.rerun()
                    else:
                        st.error("Please select wells first")
                else:
                    st.error("Please define at least 2 factors with levels")
    
    with tabs[4]:
        st.markdown("### Time Course Setup")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            treatment_name = st.text_input("Treatment Name", placeholder="e.g., Growth Factor")
            
            time_points = st.text_area(
                "Time Points",
                placeholder="0h\n2h\n4h\n8h\n12h\n24h",
                height=150
            )
            
            replicates_per_time = st.number_input("Replicates per Time Point", min_value=1, max_value=6, value=3)
            
        with col2:
            color_scheme = st.selectbox("Color Scheme", ["Blue Gradient", "Green Gradient", "Heat Map"])
            
            if st.button("Apply Time Course", type="primary", use_container_width=True):
                if treatment_name and time_points:
                    times = [t.strip() for t in time_points.split('\n') if t.strip()]
                    st.info(f"Setting up {len(times)} time points with {replicates_per_time} replicates each")
                    total_wells_needed = len(times) * replicates_per_time
                    
                    if len(st.session_state.selected_wells) >= total_wells_needed:
                        if color_scheme == "Blue Gradient":
                            colors = st.session_state.visualizer.generate_gradient_colors(len(times), 'blue_cyan')
                        elif color_scheme == "Green Gradient":
                            colors = st.session_state.visualizer.generate_gradient_colors(len(times), 'green_emerald')
                        else:
                            colors = st.session_state.visualizer.generate_gradient_colors(len(times), 'amber_orange')
                        
                        well_idx = 0
                        for time_idx, time_point in enumerate(times):
                            for rep in range(replicates_per_time):
                                if well_idx < len(st.session_state.selected_wells):
                                    well_id = st.session_state.selected_wells[well_idx]
                                    plate['wells'][well_id].update({
                                        'treatment': treatment_name,
                                        'compound': f"{treatment_name} @ {time_point}",
                                        'time_point': time_point,
                                        'replicate': rep + 1,
                                        'color': colors[time_idx]
                                    })
                                    well_idx += 1
                        
                        st.session_state.selected_wells = []
                        st.success(f"Applied time course with {len(times)} time points")
                        st.rerun()
                    else:
                        st.error(f"Need at least {total_wells_needed} wells selected")
                else:
                    st.error("Please fill in treatment name, time points, and select wells")
    
    with tabs[5]:
        st.markdown("### Dose Response Curve Setup")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            compound_name = st.text_input("Compound", placeholder="e.g., Inhibitor X")
            
            col1a, col1b = st.columns(2)
            with col1a:
                dose_type = st.radio("Dose Type", ["Logarithmic", "Linear"])
            with col1b:
                n_doses = st.number_input("Number of Doses", min_value=4, max_value=12, value=8)
            
            if dose_type == "Logarithmic":
                col1c, col1d = st.columns(2)
                with col1c:
                    min_dose = st.number_input("Min Dose", value=0.001, format="%.6f")
                with col1d:
                    max_dose = st.number_input("Max Dose", value=100.0)
            else:
                col1c, col1d = st.columns(2)
                with col1c:
                    min_dose = st.number_input("Min Dose", value=0.0)
                with col1d:
                    max_dose = st.number_input("Max Dose", value=100.0)
            
            dose_unit = st.selectbox("Unit", ["nM", "µM", "mM", "M", "µg/mL", "mg/mL", "%"])
            
        with col2:
            n_replicates = st.number_input("Replicates per Dose", min_value=1, max_value=6, value=3)
            include_zero = st.checkbox("Include Zero Dose", value=True)
            
            if st.button("Generate Dose Response", type="primary", use_container_width=True):
                st.info(f"Generating {n_doses} doses with {n_replicates} replicates each")
                doses = []
                if dose_type == "Logarithmic":
                    if min_dose > 0:
                        log_min = np.log10(min_dose)
                        log_max = np.log10(max_dose)
                        dose_values = np.logspace(log_min, log_max, n_doses)
                        doses = [f"{d:.3g} {dose_unit}" for d in dose_values]
                    else:
                        st.error("Min dose must be > 0 for logarithmic scale")
                        return
                else:
                    dose_values = np.linspace(min_dose, max_dose, n_doses)
                    doses = [f"{d:.3g} {dose_unit}" for d in dose_values]
                
                if include_zero:
                    doses.insert(0, f"0 {dose_unit}")
                
                total_wells_needed = len(doses) * n_replicates
                
                if compound_name and len(st.session_state.selected_wells) >= total_wells_needed:
                    colors = st.session_state.visualizer.generate_dilution_gradient('#DC2626', len(doses))
                    
                    well_idx = 0
                    for dose_idx, dose in enumerate(doses):
                        for rep in range(n_replicates):
                            if well_idx < len(st.session_state.selected_wells):
                                well_id = st.session_state.selected_wells[well_idx]
                                plate['wells'][well_id].update({
                                    'treatment': compound_name,
                                    'compound': f"{compound_name} {dose}",
                                    'concentration': dose,
                                    'replicate': rep + 1,
                                    'color': colors[dose_idx]
                                })
                                well_idx += 1
                    
                    st.session_state.selected_wells = []
                    st.success(f"Generated dose response with {len(doses)} doses")
                    st.rerun()
                else:
                    st.error(f"Please enter compound name and select at least {total_wells_needed} wells")
    
    with tabs[6]:
        st.markdown("### Custom Pattern Designer")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            pattern_type = st.selectbox(
                "Pattern Type",
                ["Checkerboard", "Gradient", "Radial", "Stripes", "Custom"]
            )
            
            if pattern_type == "Custom":
                st.text_area(
                    "Pattern Definition",
                    placeholder="Define your custom pattern here...",
                    height=200
                )
            else:
                st.info(f"{pattern_type} pattern selected")
                if pattern_type == "Stripes":
                    orientation = st.radio("Orientation", ["Horizontal", "Vertical", "Diagonal"])
                elif pattern_type == "Gradient":
                    direction = st.radio("Direction", ["Top-Bottom", "Left-Right", "Center-Out"])
        
        with col2:
            st.markdown("#### Pattern Colors")
            pattern_colors = []
            for i in range(3):
                color = st.color_picker(f"Color {i+1}", key=f"pattern_color_{i}")
                pattern_colors.append(color)
            
            if st.button("Apply Pattern", type="primary", use_container_width=True):
                st.info(f"Applying {pattern_type} pattern")
                if st.session_state.selected_wells:
                    wells = st.session_state.selected_wells[:]
                    
                    if pattern_type == "Checkerboard":
                        for idx, well_id in enumerate(wells):
                            row = ord(well_id[0]) - ord('A')
                            col = int(well_id[1:]) - 1
                            color_idx = (row + col) % 2
                            plate['wells'][well_id].update({
                                'treatment': 'Pattern',
                                'compound': f'Pattern {color_idx + 1}',
                                'color': pattern_colors[color_idx]
                            })
                    
                    elif pattern_type == "Stripes":
                        if 'orientation' in locals():
                            if orientation == "Horizontal":
                                for well_id in wells:
                                    row = ord(well_id[0]) - ord('A')
                                    color_idx = row % len(pattern_colors)
                                    plate['wells'][well_id].update({
                                        'treatment': 'Pattern',
                                        'compound': f'Stripe {color_idx + 1}',
                                        'color': pattern_colors[color_idx]
                                    })
                            elif orientation == "Vertical":
                                for well_id in wells:
                                    col = int(well_id[1:]) - 1
                                    color_idx = col % len(pattern_colors)
                                    plate['wells'][well_id].update({
                                        'treatment': 'Pattern',
                                        'compound': f'Stripe {color_idx + 1}',
                                        'color': pattern_colors[color_idx]
                                    })
                    
                    elif pattern_type == "Gradient":
                        n_wells = len(wells)
                        gradient_colors = st.session_state.visualizer.generate_gradient_colors(n_wells, 'purple_pink')
                        for idx, well_id in enumerate(wells):
                            plate['wells'][well_id].update({
                                'treatment': 'Pattern',
                                'compound': f'Gradient {idx + 1}',
                                'color': gradient_colors[idx]
                            })
                    
                    st.session_state.selected_wells = []
                    st.success(f"Applied {pattern_type} pattern")
                    st.rerun()
                else:
                    st.error("Please select wells first")
    
    st.divider()
    
    st.markdown("### Plate Visualization")
    fig = st.session_state.visualizer.create_plate_figure(
        plate['rows'], 
        plate['cols'], 
        plate['wells'],
        st.session_state.selected_wells,
        st.session_state.hover_well
    )
    st.plotly_chart(fig, use_container_width=True, key="plate_viz")
    
    st.markdown("### Interactive Well Selection")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        selection_mode = st.selectbox(
            "Selection Mode",
            ["Click Individual", "Range Selection", "Paint Mode", "Pattern"],
            help="Choose how to select wells"
        )
    
    with col2:
        if selection_mode == "Range Selection":
            range_input = st.text_input(
                "Enter range",
                placeholder="e.g., A1:D4 or A1-D4",
                help="Select a rectangular range of wells"
            )
            if st.button("Apply Range", type="primary"):
                try:
                    if ':' in range_input:
                        start, end = range_input.upper().split(':')
                    else:
                        start, end = range_input.upper().split('-')
                    
                    start_match = re.match(r"([A-Z])(\d+)", start.strip())
                    end_match = re.match(r"([A-Z])(\d+)", end.strip())
                    
                    if start_match and end_match:
                        start_row = ord(start_match.group(1)) - ord('A')
                        start_col = int(start_match.group(2)) - 1
                        end_row = ord(end_match.group(1)) - ord('A')
                        end_col = int(end_match.group(2)) - 1
                        
                        new_selections = []
                        for i in range(min(start_row, end_row), max(start_row, end_row) + 1):
                            for j in range(min(start_col, end_col), max(start_col, end_col) + 1):
                                well_id = f"{chr(65 + i)}{j + 1}"
                                if well_id not in st.session_state.selected_wells:
                                    new_selections.append(well_id)
                        
                        st.session_state.selected_wells.extend(new_selections)
                        st.success(f"Selected {len(new_selections)} wells")
                        st.rerun()
                except:
                    st.error("Invalid range format")
        
        elif selection_mode == "Pattern":
            pattern = st.selectbox(
                "Pattern",
                ["Every other well", "Diagonal", "Border wells", "Center wells"],
                help="Select wells in a pattern"
            )
            if st.button("Apply Pattern", type="primary"):
                pattern_wells = []
                if pattern == "Every other well":
                    for i in range(plate['rows']):
                        for j in range(plate['cols']):
                            if (i + j) % 2 == 0:
                                pattern_wells.append(f"{chr(65 + i)}{j + 1}")
                elif pattern == "Diagonal":
                    for i in range(min(plate['rows'], plate['cols'])):
                        pattern_wells.append(f"{chr(65 + i)}{i + 1}")
                elif pattern == "Border wells":
                    for i in range(plate['rows']):
                        for j in range(plate['cols']):
                            if i == 0 or i == plate['rows']-1 or j == 0 or j == plate['cols']-1:
                                pattern_wells.append(f"{chr(65 + i)}{j + 1}")
                elif pattern == "Center wells":
                    for i in range(1, plate['rows']-1):
                        for j in range(1, plate['cols']-1):
                            pattern_wells.append(f"{chr(65 + i)}{j + 1}")
                
                new_wells = [w for w in pattern_wells if w not in st.session_state.selected_wells]
                st.session_state.selected_wells.extend(new_wells)
                st.success(f"Selected {len(new_wells)} wells")
                st.rerun()
    
    with col3:
        if st.button("Clear All", type="secondary"):
            st.session_state.selected_wells = []
            st.rerun()
    
    if 'paint_selecting' not in st.session_state:
        st.session_state.paint_selecting = False
    
    if st.session_state.selected_wells:
        st.info(f"**{len(st.session_state.selected_wells)} wells selected**: {', '.join(sorted(st.session_state.selected_wells)[:10])}{'...' if len(st.session_state.selected_wells) > 10 else ''}")
    else:
        st.caption("No wells selected")
    
    st.markdown("---")
    
    with st.container():
        col_buttons = st.columns([1] + [1] * plate['cols'])
        col_buttons[0].markdown("")
        
        for j in range(plate['cols']):
            with col_buttons[j + 1]:
                if st.button(f"↓{j+1}", key=f"col_sel_{j}", help=f"Select column {j+1}"):
                    col_wells = [f"{chr(65 + i)}{j + 1}" for i in range(plate['rows'])]
                    new_wells = [w for w in col_wells if w not in st.session_state.selected_wells]
                    st.session_state.selected_wells.extend(new_wells)
                    st.rerun()
        
        for i in range(plate['rows']):
            row_label = chr(65 + i)
            row_cols = st.columns([1] + [1] * plate['cols'])
            
            with row_cols[0]:
                if st.button(f"{row_label}→", key=f"row_sel_{i}", help=f"Select row {row_label}"):
                    row_wells = [f"{row_label}{j + 1}" for j in range(plate['cols'])]
                    new_wells = [w for w in row_wells if w not in st.session_state.selected_wells]
                    st.session_state.selected_wells.extend(new_wells)
                    st.rerun()
            
            for j in range(plate['cols']):
                well_id = f"{row_label}{j+1}"
                well_info = plate['wells'][well_id]
                is_selected = well_id in st.session_state.selected_wells
                has_treatment = well_info.get('treatment') is not None
                
                with row_cols[j + 1]:
                    if selection_mode == "Paint Mode":
                        new_state = st.checkbox(
                            "",
                            value=is_selected,
                            key=f"check_{well_id}",
                            help=f"{well_id}: {well_info.get('treatment') or 'Empty'}"
                        )
                        if new_state != is_selected:
                            if new_state:
                                st.session_state.selected_wells.append(well_id)
                            else:
                                st.session_state.selected_wells.remove(well_id)
                            st.rerun()
                    else:
                        if has_treatment and is_selected:
                            emoji = "🔵"
                        elif has_treatment:
                            emoji = "⚫"
                        elif is_selected:
                            emoji = "🔴"
                        else:
                            emoji = "⚪"
                        
                        if st.button(
                            emoji,
                            key=f"well_{well_id}",
                            help=f"{well_id}: {well_info.get('treatment') or 'Empty'}",
                            use_container_width=True
                        ):
                            if is_selected:
                                st.session_state.selected_wells.remove(well_id)
                            else:
                                st.session_state.selected_wells.append(well_id)
                            st.rerun()
    
    st.markdown("---")
    st.markdown("#### Quick Selection Helpers")
    
    helper_cols = st.columns(6)
    
    with helper_cols[0]:
        if st.button("Toggle Selected", help="Invert current selection"):
            current = set(st.session_state.selected_wells)
            all_wells = set(plate['wells'].keys())
            st.session_state.selected_wells = list(all_wells - current)
            st.rerun()
    
    with helper_cols[1]:
        if st.button("Select Empty", help="Select all empty wells"):
            empty_wells = [w for w, info in plate['wells'].items() if not info.get('treatment')]
            st.session_state.selected_wells = empty_wells
            st.rerun()
    
    with helper_cols[2]:
        if st.button("Select Filled", help="Select all filled wells"):
            filled_wells = [w for w, info in plate['wells'].items() if info.get('treatment')]
            st.session_state.selected_wells = filled_wells
            st.rerun()
    
    with helper_cols[3]:
        if st.button("Expand Selection", help="Select adjacent wells"):
            expanded = set(st.session_state.selected_wells)
            for well_id in st.session_state.selected_wells:
                row = ord(well_id[0]) - ord('A')
                col = int(well_id[1:]) - 1
                
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        new_row = row + dr
                        new_col = col + dc
                        if 0 <= new_row < plate['rows'] and 0 <= new_col < plate['cols']:
                            expanded.add(f"{chr(65 + new_row)}{new_col + 1}")
            
            st.session_state.selected_wells = list(expanded)
            st.rerun()
    
    with helper_cols[4]:
        if st.button("First Half", help="Select first half of plate"):
            mid_col = plate['cols'] // 2
            first_half = []
            for i in range(plate['rows']):
                for j in range(mid_col):
                    first_half.append(f"{chr(65 + i)}{j + 1}")
            st.session_state.selected_wells = first_half
            st.rerun()
    
    with helper_cols[5]:
        if st.button("Second Half", help="Select second half of plate"):
            mid_col = plate['cols'] // 2
            second_half = []
            for i in range(plate['rows']):
                for j in range(mid_col, plate['cols']):
                    second_half.append(f"{chr(65 + i)}{j + 1}")
            st.session_state.selected_wells = second_half
            st.rerun()
    
    st.divider()
    with st.expander("Advanced Selection Tools", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Select All", use_container_width=True):
                st.session_state.selected_wells = list(plate['wells'].keys())
                st.rerun()
            if st.button("Select Rows", use_container_width=True):
                row_select = st.selectbox("Rows", [chr(65+i) for i in range(plate['rows'])], key="row_sel")
                if row_select:
                    st.session_state.selected_wells = [f"{row_select}{j+1}" for j in range(plate['cols'])]
                    st.rerun()
        
        with col2:
            if st.button("Select Empty", use_container_width=True):
                st.session_state.selected_wells = [w for w, info in plate['wells'].items() 
                                                  if not info.get('treatment')]
                st.rerun()
            if st.button("Select Columns", use_container_width=True):
                col_select = st.selectbox("Columns", [str(j+1) for j in range(plate['cols'])], key="col_sel")
                if col_select:
                    st.session_state.selected_wells = [f"{chr(65+i)}{col_select}" for i in range(plate['rows'])]
                    st.rerun()
        
        with col3:
            if st.button("Select Filled", use_container_width=True):
                st.session_state.selected_wells = [w for w, info in plate['wells'].items() 
                                                  if info.get('treatment')]
                st.rerun()
            if st.button("Select Pattern", use_container_width=True):
                pattern = st.selectbox("Pattern", ["Checkerboard", "Every Other Row", "Every Other Column"], key="pat_sel")
                if pattern == "Checkerboard":
                    wells_to_select = []
                    for i in range(plate['rows']):
                        for j in range(plate['cols']):
                            if (i + j) % 2 == 0:
                                wells_to_select.append(f"{chr(65 + i)}{j + 1}")
                    st.session_state.selected_wells = wells_to_select
                    st.rerun()
                elif pattern == "Every Other Row":
                    wells_to_select = []
                    for i in range(0, plate['rows'], 2):
                        for j in range(plate['cols']):
                            wells_to_select.append(f"{chr(65 + i)}{j + 1}")
                    st.session_state.selected_wells = wells_to_select
                    st.rerun()
                elif pattern == "Every Other Column":
                    wells_to_select = []
                    for i in range(plate['rows']):
                        for j in range(0, plate['cols'], 2):
                            wells_to_select.append(f"{chr(65 + i)}{j + 1}")
                    st.session_state.selected_wells = wells_to_select
                    st.rerun()
        
        with col4:
            if st.button("Invert Selection", use_container_width=True):
                all_wells = set(plate['wells'].keys())
                current = set(st.session_state.selected_wells)
                st.session_state.selected_wells = list(all_wells - current)
                st.rerun()
            if st.button("Clear All Wells", use_container_width=True, type="secondary"):
                if st.checkbox("Confirm clear all", key="confirm_clear"):
                    plate = st.session_state.manager.clear_assignments(plate)
                    st.session_state.plates[st.session_state.current_plate] = plate
                    st.rerun()
    
    

def create_new_plate(rows, cols, plate_type):
    plate_id = f"{plate_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.current_plate = plate_id
    st.session_state.plates[plate_id] = {
        'type': plate_type,
        'rows': rows,
        'cols': cols,
        'wells': initialize_wells(rows, cols),
        'created': datetime.now()
    }
    st.session_state.selected_wells = []
    st.rerun()

def initialize_wells(rows, cols):
    wells = {}
    for i in range(rows):
        row_label = chr(65 + i)
        for j in range(cols):
            well_id = f"{row_label}{j+1}"
            wells[well_id] = {
                'treatment': None,
                'compound': None,
                'subject': None,
                'replicate': None,
                'color': st.session_state.visualizer.theme['empty']
            }
    return wells

def parse_well_selection(input_str, max_rows, max_cols):
    selected_wells = []
    input_str = input_str.upper().replace(" ", "")
    
    parts = input_str.split(",")
    
    for part in parts:
        if "-" in part:
            start, end = part.split("-")
            
            start_match = re.match(r"([A-Z]+)(\d+)", start)
            end_match = re.match(r"([A-Z]+)(\d+)", end)
            
            if not start_match or not end_match:
                raise ValueError(f"Invalid well format: {part}")
            
            start_row = ord(start_match.group(1)) - ord('A')
            start_col = int(start_match.group(2)) - 1
            end_row = ord(end_match.group(1)) - ord('A')
            end_col = int(end_match.group(2)) - 1
            
            if start_row >= max_rows or end_row >= max_rows:
                raise ValueError(f"Row out of bounds: {part}")
            if start_col >= max_cols or end_col >= max_cols:
                raise ValueError(f"Column out of bounds: {part}")
            
            for i in range(start_row, end_row + 1):
                for j in range(start_col, end_col + 1):
                    well_id = f"{chr(65 + i)}{j + 1}"
                    if well_id not in selected_wells:
                        selected_wells.append(well_id)
        else:
            match = re.match(r"([A-Z]+)(\d+)", part)
            if not match:
                raise ValueError(f"Invalid well format: {part}")
            
            row = ord(match.group(1)) - ord('A')
            col = int(match.group(2)) - 1
            
            if row >= max_rows:
                raise ValueError(f"Row out of bounds: {part}")
            if col >= max_cols:
                raise ValueError(f"Column out of bounds: {part}")
            
            well_id = f"{match.group(1)}{match.group(2)}"
            if well_id not in selected_wells:
                selected_wells.append(well_id)
    
    return selected_wells

def show_export_dialog(export_format):
    plate = st.session_state.plates[st.session_state.current_plate]
    
    if export_format == "Excel":
        excel_data = st.session_state.exporter.export_to_excel(plate)
        filename = f"{plate['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        st.sidebar.download_button(
            label="Download Excel (Plate Layout)",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    elif export_format == "Excel (Long)":
        excel_long_data = st.session_state.exporter.export_to_excel_long_format(plate)
        filename = f"{plate['type']}_long_format_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        st.sidebar.download_button(
            label="Download Excel (Long Format)",
            data=excel_long_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.sidebar.info(
            "Long format includes one row per well with all metadata. "
            "Perfect for data analysis in R, Python, or other tools!"
        )
        
    elif export_format == "CSV":
        csv_data = st.session_state.exporter.export_to_csv(plate)
        filename = f"{plate['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        st.sidebar.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
        
    elif export_format == "JSON":
        json_data = st.session_state.exporter.export_to_json(plate)
        filename = f"{plate['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        st.sidebar.download_button(
            label="Download JSON",
            data=json_data,
            file_name=filename,
            mime="application/json",
            use_container_width=True
        )

def apply_group_assignment(plate, group_name, pattern):
    group_info = st.session_state.groups[group_name]
    wells = st.session_state.selected_wells
    
    if not group_info['items']:
        for well_id in wells:
            plate['wells'][well_id].update({
                'treatment': group_name,
                'compound': group_name,
                'replicate': 1,
                'color': group_info['color']
            })
    elif pattern == "Sequential":
        for idx, well_id in enumerate(wells):
            item_idx = idx % len(group_info['items'])
            plate['wells'][well_id].update({
                'treatment': group_name,
                'compound': group_info['items'][item_idx],
                'replicate': (idx // len(group_info['items'])) + 1,
                'color': group_info['color']
            })
    
    elif pattern == "Random":
        import random
        random_items = [random.choice(group_info['items']) for _ in wells]
        for well_id, item in zip(wells, random_items):
            plate['wells'][well_id].update({
                'treatment': group_name,
                'compound': item,
                'replicate': 1,
                'color': group_info['color']
            })
    
    elif pattern == "Replicate Groups":
        n_items = len(group_info['items'])
        n_wells = len(wells)
        reps_per_item = max(1, n_wells // n_items)
        
        well_idx = 0
        for item in group_info['items']:
            for rep in range(reps_per_item):
                if well_idx < n_wells:
                    plate['wells'][wells[well_idx]].update({
                        'treatment': group_name,
                        'compound': item,
                        'replicate': rep + 1,
                        'color': group_info['color']
                    })
                    well_idx += 1

if __name__ == "__main__":
    main()