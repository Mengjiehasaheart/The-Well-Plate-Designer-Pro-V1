"""
Copyright (c) 2024 Mengjie Fan. All rights reserved.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
import random
import itertools

class PlateManager:
    def __init__(self):
        self.assignment_strategies = {
            'random': self._random_assignment,
            'serpentine': self._serpentine_assignment,
            'block': self._block_assignment,
            'checkerboard': self._checkerboard_assignment,
            'edge_aware': self._edge_aware_assignment
        }
    
    def create_group(self, name: str, items: List[str], color: str = None) -> Dict:
        return {
            'id': f"grp_{datetime.now().strftime('%H%M%S%f')}",
            'name': name,
            'items': items,
            'color': color,
            'created': datetime.now()
        }
    
    def assign_treatments(self, plate: Dict, groups: Dict[str, Dict], 
                         strategy: str = 'edge_aware', 
                         replicates: int = 3) -> Dict:
        if strategy not in self.assignment_strategies:
            strategy = 'edge_aware'
        
        return self.assignment_strategies[strategy](plate, groups, replicates)
    
    def _get_available_wells(self, plate: Dict) -> List[str]:
        available = []
        for well_id, well_info in plate['wells'].items():
            if not well_info.get('treatment'):
                available.append(well_id)
        return available
    
    def _random_assignment(self, plate: Dict, groups: Dict[str, Dict], 
                          replicates: int) -> Dict:
        available = self._get_available_wells(plate)
        random.shuffle(available)
        
        assignments = {}
        well_idx = 0
        
        for group_name, group_info in groups.items():
            for item in group_info['items']:
                for rep in range(replicates):
                    if well_idx < len(available):
                        well_id = available[well_idx]
                        assignments[well_id] = {
                            'treatment': group_name,
                            'item': item,
                            'replicate': rep + 1,
                            'color': group_info.get('color', '#6366F1')
                        }
                        well_idx += 1
        
        return self._apply_assignments(plate, assignments)
    
    def _serpentine_assignment(self, plate: Dict, groups: Dict[str, Dict], 
                              replicates: int) -> Dict:
        rows, cols = plate['rows'], plate['cols']
        path = []
        
        for i in range(rows):
            row_label = chr(65 + i)
            if i % 2 == 0:
                for j in range(cols):
                    path.append(f"{row_label}{j+1}")
            else:
                for j in range(cols-1, -1, -1):
                    path.append(f"{row_label}{j+1}")
        
        available = [w for w in path if not plate['wells'][w].get('treatment')]
        
        assignments = {}
        well_idx = 0
        
        for group_name, group_info in groups.items():
            if not group_info['items']:
                # Handle empty groups
                for rep in range(replicates):
                    if well_idx < len(available):
                        well_id = available[well_idx]
                        assignments[well_id] = {
                            'treatment': group_name,
                            'item': group_name,
                            'replicate': rep + 1,
                            'color': group_info.get('color', '#6366F1')
                        }
                        well_idx += 1
            else:
                for item in group_info['items']:
                    for rep in range(replicates):
                        if well_idx < len(available):
                            well_id = available[well_idx]
                            assignments[well_id] = {
                                'treatment': group_name,
                                'item': item,
                                'replicate': rep + 1,
                                'color': group_info.get('color', '#6366F1')
                            }
                            well_idx += 1
        
        return self._apply_assignments(plate, assignments)
    
    def _block_assignment(self, plate: Dict, groups: Dict[str, Dict], 
                         replicates: int) -> Dict:
        rows, cols = plate['rows'], plate['cols']
        n_groups = len(groups)
        
        if n_groups == 0:
            return plate
        
        block_size = max(2, min(4, rows // 2, cols // 2))
        assignments = {}
        
        group_cycle = itertools.cycle(groups.items())
        
        for block_row in range(0, rows, block_size):
            for block_col in range(0, cols, block_size):
                group_name, group_info = next(group_cycle)
                item_cycle = itertools.cycle(group_info['items'])
                
                for i in range(block_row, min(block_row + block_size, rows)):
                    for j in range(block_col, min(block_col + block_size, cols)):
                        well_id = f"{chr(65 + i)}{j + 1}"
                        if not plate['wells'][well_id].get('treatment'):
                            item = next(item_cycle)
                            assignments[well_id] = {
                                'treatment': group_name,
                                'item': item,
                                'replicate': 1,
                                'color': group_info.get('color', '#6366F1')
                            }
        
        return self._apply_assignments(plate, assignments)
    
    def _checkerboard_assignment(self, plate: Dict, groups: Dict[str, Dict], 
                                replicates: int) -> Dict:
        rows, cols = plate['rows'], plate['cols']
        assignments = {}
        
        if len(groups) < 2:
            return self._random_assignment(plate, groups, replicates)
        
        group_list = list(groups.items())
        
        for i in range(rows):
            for j in range(cols):
                well_id = f"{chr(65 + i)}{j + 1}"
                if not plate['wells'][well_id].get('treatment'):
                    group_idx = (i + j) % len(group_list)
                    group_name, group_info = group_list[group_idx]
                    if group_info['items']:
                        item = random.choice(group_info['items'])
                    else:
                        item = group_name
                    
                    assignments[well_id] = {
                        'treatment': group_name,
                        'item': item,
                        'replicate': 1,
                        'color': group_info.get('color', '#6366F1')
                    }
        
        return self._apply_assignments(plate, assignments)
    
    def _edge_aware_assignment(self, plate: Dict, groups: Dict[str, Dict], 
                              replicates: int) -> Dict:
        rows, cols = plate['rows'], plate['cols']
        
        center_wells = []
        edge_wells = []
        corner_wells = []
        
        for i in range(rows):
            for j in range(cols):
                well_id = f"{chr(65 + i)}{j + 1}"
                if not plate['wells'][well_id].get('treatment'):
                    if (i == 0 or i == rows-1) and (j == 0 or j == cols-1):
                        corner_wells.append(well_id)
                    elif i == 0 or i == rows-1 or j == 0 or j == cols-1:
                        edge_wells.append(well_id)
                    else:
                        center_wells.append(well_id)
        
        random.shuffle(center_wells)
        random.shuffle(edge_wells)
        random.shuffle(corner_wells)
        
        available = center_wells + edge_wells + corner_wells
        
        assignments = {}
        well_idx = 0
        
        all_treatments = []
        for group_name, group_info in groups.items():
            if not group_info['items']:
                # Handle empty groups
                for rep in range(replicates):
                    all_treatments.append({
                        'treatment': group_name,
                        'item': group_name,
                        'replicate': rep + 1,
                        'color': group_info.get('color', '#6366F1')
                    })
            else:
                for item in group_info['items']:
                    for rep in range(replicates):
                        all_treatments.append({
                            'treatment': group_name,
                            'item': item,
                            'replicate': rep + 1,
                            'color': group_info.get('color', '#6366F1')
                        })
        
        random.shuffle(all_treatments)
        
        for treatment_info in all_treatments:
            if well_idx < len(available):
                assignments[available[well_idx]] = treatment_info
                well_idx += 1
        
        return self._apply_assignments(plate, assignments)
    
    def _apply_assignments(self, plate: Dict, assignments: Dict) -> Dict:
        for well_id, assignment_info in assignments.items():
            plate['wells'][well_id].update({
                'treatment': assignment_info['treatment'],
                'compound': assignment_info.get('item'),
                'replicate': assignment_info.get('replicate'),
                'color': assignment_info.get('color', '#6366F1')
            })
        return plate
    
    def clear_assignments(self, plate: Dict, well_ids: List[str] = None) -> Dict:
        if well_ids is None:
            well_ids = list(plate['wells'].keys())
        
        for well_id in well_ids:
            if well_id in plate['wells']:
                plate['wells'][well_id].update({
                    'treatment': None,
                    'compound': None,
                    'subject': None,
                    'replicate': None,
                    'color': '#2D3748'
                })
        
        return plate
    
    def get_plate_summary(self, plate: Dict) -> Dict:
        summary = {
            'total_wells': len(plate['wells']),
            'assigned_wells': 0,
            'empty_wells': 0,
            'treatments': {},
            'replicates': {}
        }
        
        for well_id, well_info in plate['wells'].items():
            if well_info.get('treatment'):
                summary['assigned_wells'] += 1
                treatment = well_info['treatment']
                
                if treatment not in summary['treatments']:
                    summary['treatments'][treatment] = []
                summary['treatments'][treatment].append(well_id)
                
                rep_key = f"{treatment}_{well_info.get('compound', 'unknown')}"
                if rep_key not in summary['replicates']:
                    summary['replicates'][rep_key] = 0
                summary['replicates'][rep_key] += 1
            else:
                summary['empty_wells'] += 1
        
        return summary