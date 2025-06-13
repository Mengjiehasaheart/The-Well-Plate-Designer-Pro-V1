"""
Copyright (c) 2024 Mengjie Fan. All rights reserved.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import colorsys

class PlateVisualizer:
    def __init__(self):
        self.themes = {
            'dark': {
                'bg': '#1A1A1A',
                'surface': '#2D2D2D',
                'primary': '#818CF8',
                'secondary': '#A78BFA',
                'accent': '#F472B6',
                'success': '#34D399',
                'warning': '#FBBF24',
                'danger': '#F87171',
                'empty': '#404040',
                'hover': '#525252',
                'text': '#F9FAFB',
                'muted': '#D1D5DB',
                'well_border': '#525252',
                'plate_bg': 'rgba(45, 45, 45, 0.8)'
            },
            'light': {
                'bg': '#FFFFFF',
                'surface': '#F9FAFB',
                'primary': '#4F46E5',
                'secondary': '#7C3AED',
                'accent': '#DB2777',
                'success': '#059669',
                'warning': '#D97706',
                'danger': '#DC2626',
                'empty': '#D1D5DB',
                'hover': '#9CA3AF',
                'text': '#111827',
                'muted': '#4B5563',
                'well_border': '#9CA3AF',
                'plate_bg': 'rgba(209, 213, 219, 0.5)'
            },
            'nature': {
                'bg': '#F3F4F6',
                'surface': '#ECFDF5',
                'primary': '#059669',
                'secondary': '#14B8A6',
                'accent': '#F59E0B',
                'success': '#84CC16',
                'warning': '#EAB308',
                'danger': '#F87171',
                'empty': '#D1FAE5',
                'hover': '#A7F3D0',
                'text': '#064E3B',
                'muted': '#047857',
                'well_border': '#6EE7B7',
                'plate_bg': 'rgba(209, 250, 229, 0.3)'
            }
        }
        self.current_theme = 'dark'
        self.theme = self.themes[self.current_theme]
        
        self.gradients = {
            'purple_pink': ['#6366F1', '#8B5CF6', '#A78BFA', '#C084FC', '#E879F9', '#EC4899'],
            'blue_cyan': ['#3B82F6', '#60A5FA', '#93C5FD', '#06B6D4', '#22D3EE', '#67E8F9'],
            'green_emerald': ['#10B981', '#34D399', '#6EE7B7', '#059669', '#10B981', '#34D399'],
            'amber_orange': ['#F59E0B', '#FCD34D', '#FDE68A', '#FB923C', '#FDBA74', '#FED7AA'],
            'high_contrast': [
                '#DC2626', '#059669', '#2563EB', '#D97706', '#7C3AED', '#0891B2',
                '#BE185D', '#16A34A', '#1D4ED8', '#EA580C', '#6D28D9', '#0E7490',
                '#881337', '#15803D', '#1E3A8A', '#C2410C', '#581C87', '#155E75',
                '#991B1B', '#047857', '#1E40AF', '#B45309', '#6B21A8', '#0C7180'
            ],
            'custom': []
        }
    
    def set_theme(self, theme_name: str):
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.theme = self.themes[theme_name]
    
    def create_plate_figure(self, rows: int, cols: int, wells: Dict, 
                          selected_wells: List[str] = None,
                          hover_well: str = None) -> go.Figure:
        
        fig = go.Figure()
        
        # Calculate proper spacing to prevent overlap
        well_spacing = 1.2  # Increased spacing between wells
        well_size = 0.45    # Relative size of wells
        
        # Calculate figure dimensions based on plate size
        plate_width = cols * well_spacing + 2
        plate_height = rows * well_spacing + 2
        
        annotations = []
        shapes = []
        
        # Row labels (A, B, C, etc.)
        for i in range(rows):
            row_label = chr(65 + i)
            y_pos = (rows - i - 0.5) * well_spacing
            annotations.append(dict(
                x=-0.8,
                y=y_pos,
                text=f"<b>{row_label}</b>",
                showarrow=False,
                font=dict(size=20, color=self.theme['text']),
                xanchor='center',
                yanchor='middle'
            ))
        
        # Column labels (1, 2, 3, etc.)
        for j in range(cols):
            x_pos = (j + 0.5) * well_spacing
            annotations.append(dict(
                x=x_pos,
                y=rows * well_spacing + 0.5,
                text=f"<b>{j + 1}</b>",
                showarrow=False,
                font=dict(size=20, color=self.theme['text']),
                xanchor='center',
                yanchor='middle'
            ))
        
        # Prepare data for wells
        hover_texts = []
        colors = []
        x_positions = []
        y_positions = []
        sizes = []
        border_widths = []
        border_colors = []
        well_labels = []
        
        for i in range(rows):
            row_label = chr(65 + i)
            for j in range(cols):
                well_id = f"{row_label}{j+1}"
                well_info = wells.get(well_id, {})
                
                # Calculate well position with proper spacing
                x = (j + 0.5) * well_spacing
                y = (rows - i - 0.5) * well_spacing
                
                x_positions.append(x)
                y_positions.append(y)
                
                is_selected = selected_wells and well_id in selected_wells
                is_hover = hover_well == well_id
                
                # Determine well color
                if well_info.get('color') and well_info['color'] != '#FFFFFF':
                    color = well_info['color']
                elif is_hover:
                    color = self.theme['hover']
                elif is_selected and not well_info.get('treatment'):
                    color = self.theme['primary']
                else:
                    color = self.theme['empty']
                
                colors.append(color)
                
                # Determine well size and border
                if is_selected:
                    size = 36
                    border_widths.append(3)
                    border_colors.append(self.theme['accent'])
                elif is_hover:
                    size = 34
                    border_widths.append(2)
                    border_colors.append(self.theme['primary'])
                else:
                    size = 32
                    border_widths.append(1)
                    border_colors.append(self.theme['well_border'])
                sizes.append(size)
                
                # Create hover text
                hover_text = f"<b>{well_id}</b>"
                if well_info.get('treatment'):
                    hover_text += f"<br>Treatment: {well_info['treatment']}"
                if well_info.get('compound'):
                    hover_text += f"<br>Compound: {well_info['compound']}"
                if well_info.get('concentration'):
                    hover_text += f"<br>Concentration: {well_info['concentration']}"
                if well_info.get('subject'):
                    hover_text += f"<br>Subject: {well_info['subject']}"
                if well_info.get('replicate'):
                    hover_text += f"<br>Replicate: {well_info['replicate']}"
                
                hover_texts.append(hover_text)
                well_labels.append(well_id)
        
        # Add wells as scatter plot
        fig.add_trace(go.Scatter(
            x=x_positions,
            y=y_positions,
            mode='markers+text',
            marker=dict(
                size=sizes,
                color=colors,
                line=dict(color=border_colors, width=border_widths),
                sizemode='diameter',
                sizeref=1
            ),
            text=[''] * len(well_labels),  # Remove text labels from visualization
            textfont=dict(size=8, color=self.theme['text']),
            textposition='middle center',
            customdata=well_labels,
            hovertext=hover_texts,
            hoverinfo='text',
            showlegend=False
        ))
        
        # Add plate background
        plate_padding = 0.6
        shapes.append(dict(
            type='rect',
            x0=-plate_padding,
            y0=-plate_padding,
            x1=cols * well_spacing + plate_padding,
            y1=rows * well_spacing + plate_padding,
            line=dict(color=self.theme['surface'], width=3),
            fillcolor=self.theme['plate_bg'],
            layer='below'
        ))
        
        # Calculate proper figure size - more compact
        fig_width = max(800, int(plate_width * 80))
        fig_height = max(500, int(plate_height * 80))
        
        fig.update_layout(
            plot_bgcolor=self.theme['bg'],
            paper_bgcolor=self.theme['bg'],
            width=fig_width,
            height=fig_height,
            xaxis=dict(
                range=[-1.5, cols * well_spacing + 1],
                showgrid=False,
                zeroline=False,
                visible=False,
                fixedrange=True
            ),
            yaxis=dict(
                range=[-1, rows * well_spacing + 1.5],
                showgrid=False,
                zeroline=False,
                visible=False,
                scaleanchor='x',
                scaleratio=1,
                fixedrange=True
            ),
            annotations=annotations,
            shapes=shapes,
            margin=dict(l=60, r=60, t=60, b=60),
            hovermode='closest',
            dragmode=False,  # Disable drag to prevent accidental moves
            clickmode='event'
        )
        
        return fig
    
    def generate_gradient_colors(self, n_colors: int, gradient_name: str = 'purple_pink') -> List[str]:
        if gradient_name in self.gradients and n_colors <= len(self.gradients[gradient_name]):
            return self.gradients[gradient_name][:n_colors]
        
        colors = []
        for i in range(n_colors):
            hue = (i / n_colors) * 0.8
            saturation = 0.7 + (i / n_colors) * 0.3
            lightness = 0.5 + (i / n_colors) * 0.2
            rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            colors.append(hex_color)
        
        return colors
    
    def generate_dilution_gradient(self, base_color: str, steps: int) -> List[str]:
        """Generate a gradient of colors for serial dilution visualization"""
        # Convert hex to RGB
        hex_color = base_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Convert to HSL for better gradient
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        
        colors = []
        for i in range(steps):
            # Adjust lightness from dark to light for dilution
            lightness = 0.3 + (i / (steps - 1)) * 0.5 if steps > 1 else l
            rgb = colorsys.hls_to_rgb(h, lightness, s)
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            colors.append(hex_color)
        
        return colors
    
    def create_legend(self, groups: Dict[str, str]) -> go.Figure:
        fig = go.Figure()
        
        y_pos = len(groups) - 1
        for label, color in groups.items():
            fig.add_trace(go.Scatter(
                x=[0],
                y=[y_pos],
                mode='markers+text',
                marker=dict(size=20, color=color),
                text=[label],
                textposition='middle right',
                textfont=dict(size=12, color=self.theme['text']),
                showlegend=False,
                hoverinfo='skip'
            ))
            y_pos -= 1
        
        fig.update_layout(
            plot_bgcolor=self.theme['bg'],
            paper_bgcolor=self.theme['bg'],
            height=max(150, len(groups) * 30),
            xaxis=dict(visible=False, range=[-0.5, 5]),
            yaxis=dict(visible=False, range=[-1, len(groups)]),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        return fig