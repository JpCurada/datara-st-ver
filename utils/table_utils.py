# utils/table_utils.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
import uuid


class DataTable:
    """
    A reusable data table component with CRUD operations, filtering, and export functionality
    """
    
    def __init__(self, data: List[Dict[str, Any]], table_config: Dict[str, Any]):
        self.data = data
        self.config = table_config
        self.filtered_data = data.copy()
        
    def render_filters(self) -> Dict[str, Any]:
        """Render filter controls and return filter values"""
        filters = {}
        
        if not self.config.get('filters'):
            return filters
        
        st.subheader("Filters")
        filter_cols = st.columns(len(self.config['filters']))
        
        for i, filter_config in enumerate(self.config['filters']):
            with filter_cols[i]:
                filter_type = filter_config['type']
                filter_key = filter_config['key']
                filter_label = filter_config['label']
                
                if filter_type == 'selectbox':
                    options = filter_config.get('options', [])
                    default_value = filter_config.get('default', options[0] if options else None)
                    filters[filter_key] = st.selectbox(filter_label, options, index=0 if default_value else None)
                
                elif filter_type == 'text_input':
                    placeholder = filter_config.get('placeholder', '')
                    filters[filter_key] = st.text_input(filter_label, placeholder=placeholder)
                
                elif filter_type == 'date_input':
                    filters[filter_key] = st.date_input(filter_label)
                
                elif filter_type == 'multiselect':
                    options = filter_config.get('options', [])
                    filters[filter_key] = st.multiselect(filter_label, options)
        
        return filters
    
    def apply_filters(self, filters: Dict[str, Any]):
        """Apply filters to the data"""
        self.filtered_data = self.data.copy()
        
        for filter_key, filter_value in filters.items():
            if not filter_value:
                continue
                
            filter_config = next((f for f in self.config.get('filters', []) if f['key'] == filter_key), None)
            if not filter_config:
                continue
            
            field = filter_config.get('field', filter_key)
            filter_type = filter_config['type']
            
            if filter_type == 'selectbox' and filter_value != 'All':
                self.filtered_data = [item for item in self.filtered_data if item.get(field) == filter_value]
            
            elif filter_type == 'text_input':
                search_term = filter_value.lower()
                if filter_config.get('search_fields'):
                    # Search across multiple fields
                    self.filtered_data = [
                        item for item in self.filtered_data
                        if any(search_term in str(item.get(search_field, '')).lower() 
                              for search_field in filter_config['search_fields'])
                    ]
                else:
                    # Search single field
                    self.filtered_data = [
                        item for item in self.filtered_data
                        if search_term in str(item.get(field, '')).lower()
                    ]
            
            elif filter_type == 'multiselect':
                self.filtered_data = [item for item in self.filtered_data if item.get(field) in filter_value]
    
    def render_table(self) -> Optional[Dict[str, Any]]:
        """Render the data table and return selected item"""
        if not self.filtered_data:
            st.info("No data matches your filters.")
            return None
        
        # Prepare display data
        display_data = []
        for item in self.filtered_data:
            row = {}
            for col_config in self.config['columns']:
                key = col_config['key']
                label = col_config['label']
                format_func = col_config.get('format')
                
                value = item.get(key, '')
                if format_func:
                    value = format_func(value)
                
                row[label] = value
            
            # Add hidden data for operations
            row['_raw_data'] = item
            display_data.append(row)
        
        df = pd.DataFrame(display_data)
        
        # Apply styling if configured
        styled_df = df.drop(columns=['_raw_data'])
        if self.config.get('styling'):
            for style_config in self.config['styling']:
                column = style_config['column']
                style_func = style_config['function']
                styled_df = styled_df.style.applymap(style_func, subset=[column])
        
        # Display table
        st.write(f"Showing {len(self.filtered_data)} records")
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=self.config.get('height', 400)
        )
        
        # Selection for actions
        if self.config.get('enable_selection'):
            selection_options = ["None"] + [
                self.config['selection_display'](item) for item in self.filtered_data
            ]
            
            selected_display = st.selectbox(
                "Select record for actions",
                options=selection_options,
                key=f"table_selection_{self.config.get('table_id', 'default')}"
            )
            
            if selected_display != "None":
                # Find the selected item
                for item in self.filtered_data:
                    if self.config['selection_display'](item) == selected_display:
                        return item
        
        return None
    
    def render_actions(self, selected_item: Optional[Dict[str, Any]] = None):
        """Render action buttons"""
        if not self.config.get('actions'):
            return
        
        st.subheader("Actions")
        
        # Global actions (don't require selection)
        global_actions = [action for action in self.config['actions'] if action.get('global', False)]
        if global_actions:
            st.write("**Global Actions:**")
            action_cols = st.columns(len(global_actions))
            
            for i, action in enumerate(global_actions):
                with action_cols[i]:
                    if st.button(action['label'], key=f"global_{action['key']}", use_container_width=True):
                        if action.get('callback'):
                            action['callback'](self.filtered_data)
        
        # Item-specific actions (require selection)
        item_actions = [action for action in self.config['actions'] if not action.get('global', False)]
        if item_actions and selected_item:
            st.write("**Selected Item Actions:**")
            
            # Display selected item info
            if self.config.get('selection_info'):
                st.write("**Selected:**")
                for info_key, info_label in self.config['selection_info'].items():
                    st.write(f"{info_label}: {selected_item.get(info_key, 'N/A')}")
            
            # Action buttons
            action_cols = st.columns(len(item_actions))
            
            for i, action in enumerate(item_actions):
                with action_cols[i]:
                    button_type = action.get('type', 'secondary')
                    if st.button(
                        action['label'], 
                        key=f"item_{action['key']}", 
                        type=button_type,
                        use_container_width=True
                    ):
                        if action.get('callback'):
                            action['callback'](selected_item)
    
    def export_data(self, format_type: str = 'csv') -> str:
        """Export filtered data"""
        if not self.filtered_data:
            return ""
        
        # Prepare export data
        export_data = []
        for item in self.filtered_data:
            row = {}
            for col_config in self.config['columns']:
                key = col_config['key']
                label = col_config['label']
                value = item.get(key, '')
                
                # Apply export formatting if specified
                if col_config.get('export_format'):
                    value = col_config['export_format'](value)
                
                row[label] = value
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        
        if format_type == 'csv':
            return df.to_csv(index=False)
        elif format_type == 'excel':
            # For Excel export, you'd need to implement Excel writing
            return df.to_csv(index=False)  # Fallback to CSV for now
        
        return ""


def create_status_styler(status_colors: Dict[str, str]):
    """Create a status styling function for table cells"""
    def style_status(val):
        return f"background-color: {status_colors.get(val, '#f8f9fa')}"
    return style_status


def format_datetime(dt_string: str, format_string: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime string for display"""
    try:
        if not dt_string:
            return "N/A"
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime(format_string)
    except:
        return dt_string


def format_date(date_string: str) -> str:
    """Format date string for display"""
    return format_datetime(date_string, "%Y-%m-%d")


def format_days_ago(dt_string: str) -> str:
    """Calculate and format days ago"""
    try:
        if not dt_string:
            return "N/A"
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        days = (datetime.now().replace(tzinfo=dt.tzinfo) - dt).days
        
        if days == 0:
            return "Today"
        elif days == 1:
            return "Yesterday"
        else:
            return f"{days} days ago"
    except:
        return "Unknown"


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text for table display"""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text


def create_metric_card(title: str, value: Any, delta: str = None, delta_color: str = "normal"):
    """Create a metric display card"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.metric(
            label=title,
            value=value,
            delta=delta,
            delta_color=delta_color
        )


def render_chart_from_data(data: List[Dict[str, Any]], chart_config: Dict[str, Any]):
    """Render a chart from data using configuration"""
    if not data:
        st.info("No data available for chart")
        return
    
    df = pd.DataFrame(data)
    chart_type = chart_config.get('type', 'bar')
    
    if chart_type == 'bar':
        fig = px.bar(
            df,
            x=chart_config.get('x'),
            y=chart_config.get('y'),
            title=chart_config.get('title'),
            color=chart_config.get('color'),
            labels=chart_config.get('labels', {})
        )
    elif chart_type == 'pie':
        fig = px.pie(
            df,
            values=chart_config.get('values'),
            names=chart_config.get('names'),
            title=chart_config.get('title'),
            color_discrete_map=chart_config.get('color_map', {})
        )
    elif chart_type == 'line':
        fig = px.line(
            df,
            x=chart_config.get('x'),
            y=chart_config.get('y'),
            title=chart_config.get('title'),
            labels=chart_config.get('labels', {})
        )
    else:
        st.error(f"Unsupported chart type: {chart_type}")
        return
    
    fig.update_layout(height=chart_config.get('height', 400))
    st.plotly_chart(fig, use_container_width=True)


def create_confirmation_dialog(message: str, confirm_text: str = "Confirm", cancel_text: str = "Cancel") -> bool:
    """Create a confirmation dialog"""
    st.warning(message)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(confirm_text, type="primary", use_container_width=True):
            return True
    
    with col2:
        if st.button(cancel_text, use_container_width=True):
            return False
    
    return False


def paginate_data(data: List[Dict[str, Any]], page_size: int = 20, page_key: str = "page") -> List[Dict[str, Any]]:
    """Paginate data for large datasets"""
    if len(data) <= page_size:
        return data
    
    total_pages = (len(data) - 1) // page_size + 1
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        page = st.selectbox(
            f"Page (showing {page_size} records per page)",
            range(1, total_pages + 1),
            key=page_key
        )
        
        st.caption(f"Total records: {len(data)} | Page {page} of {total_pages}")
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, len(data))
    
    return data[start_idx:end_idx]


def bulk_action_selector(data: List[Dict[str, Any]], display_field: str, actions: List[Dict[str, Any]]) -> None:
    """Create bulk action interface"""
    if not data or not actions:
        return
    
    st.subheader("Bulk Actions")
    
    # Multi-select for items
    options = [item[display_field] for item in data]
    selected_options = st.multiselect("Select items for bulk action", options)
    
    if selected_options:
        # Action selector
        action_labels = [action['label'] for action in actions]
        selected_action_label = st.selectbox("Choose action", action_labels)
        
        if st.button("Execute Bulk Action", type="primary"):
            # Find selected action
            selected_action = next(action for action in actions if action['label'] == selected_action_label)
            
            # Find selected items
            selected_items = [item for item in data if item[display_field] in selected_options]
            
            # Execute action
            if selected_action.get('callback'):
                selected_action['callback'](selected_items)
            
            st.success(f"Executed {selected_action_label} on {len(selected_items)} items")


class TableBuilder:
    """Builder class for creating table configurations"""
    
    def __init__(self, table_id: str):
        self.config = {
            'table_id': table_id,
            'columns': [],
            'filters': [],
            'actions': [],
            'styling': []
        }
    
    def add_column(self, key: str, label: str, format_func: Callable = None, export_format: Callable = None):
        """Add a column to the table"""
        self.config['columns'].append({
            'key': key,
            'label': label,
            'format': format_func,
            'export_format': export_format
        })
        return self
    
    def add_filter(self, filter_type: str, key: str, label: str, **kwargs):
        """Add a filter to the table"""
        filter_config = {
            'type': filter_type,
            'key': key,
            'label': label,
            **kwargs
        }
        self.config['filters'].append(filter_config)
        return self
    
    def add_action(self, key: str, label: str, callback: Callable, button_type: str = 'secondary', global_action: bool = False):
        """Add an action to the table"""
        self.config['actions'].append({
            'key': key,
            'label': label,
            'callback': callback,
            'type': button_type,
            'global': global_action
        })
        return self
    
    def add_styling(self, column: str, style_function: Callable):
        """Add styling to a column"""
        self.config['styling'].append({
            'column': column,
            'function': style_function
        })
        return self
    
    def enable_selection(self, display_function: Callable, info_fields: Dict[str, str] = None):
        """Enable row selection"""
        self.config['enable_selection'] = True
        self.config['selection_display'] = display_function
        self.config['selection_info'] = info_fields or {}
        return self
    
    def set_height(self, height: int):
        """Set table height"""
        self.config['height'] = height
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the table configuration"""
        return self.config