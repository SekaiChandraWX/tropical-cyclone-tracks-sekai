#!/usr/bin/env python3
"""
Streamlit Tropical Cyclone Track Plotter
Interactive web application for visualizing historical tropical cyclone tracks from IBTrACS
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from urllib.parse import urljoin
import warnings
import io

warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Tropical Cyclone Track Plotter",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Basin configuration
BASINS = {
    "Atlantic (NATL)": {"code": "NATL", "search_terms": ["NATL", "AL"]},
    "East/Central Pacific (EPAC/CPAC)": {"code": "EPAC", "search_terms": ["EPAC", "CPAC", "EP", "CP"]},
    "West Pacific (WPAC)": {"code": "WPAC", "search_terms": ["WPAC", "WP"]},
    "Northern Indian Ocean (NIO)": {"code": "NIO", "search_terms": ["NIO", "IO", "BB", "AS"]},
    "Southern Indian Ocean (SIO)": {"code": "SIO", "search_terms": ["SIO", "SI"]},
    "Australian Region (AUSW/AUSE)": {"code": "AUS", "search_terms": ["AUSW", "AUSE", "AU", "SP"]}
}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_intensity_color(wind_speed):
    """Return color and category for wind speed using Saffir-Simpson scale."""
    if pd.isna(wind_speed) or wind_speed < 34:
        return 'white', 'TD'
    elif wind_speed < 64:
        return '#F5F5DC', 'TS'
    elif wind_speed < 83:
        return '#FFCC5C', 'Cat1'
    elif wind_speed < 96:
        return '#FF8C00', 'Cat2'
    elif wind_speed < 113:
        return '#FF0000', 'Cat3'
    elif wind_speed < 137:
        return '#8B008B', 'Cat4'
    else:
        return '#000000', 'Cat5'

def determine_storm_type(lat_center, lon_center):
    """Determine storm type based on geographic basin."""
    if lat_center < 0:
        return "Cyclone"
    if lon_center < -30:
        return "Hurricane"
    elif lon_center > 100:
        return "Typhoon"
    else:
        return "Cyclone"

def calculate_ace_value(wind_speeds):
    """Calculate Accumulated Cyclone Energy (ACE)."""
    ace = 0.0
    for wind in wind_speeds:
        if not pd.isna(wind) and wind >= 34:
            ace += (wind ** 2) / 10000
    return ace

def convert_knots_to_mph(knots):
    """Convert wind speed from knots to mph."""
    if pd.isna(knots):
        return "N/A"
    return int(knots * 1.15078)

def format_datetime(datetime_str):
    """Convert IBTrACS datetime to readable format."""
    if not datetime_str or datetime_str == '-' or pd.isna(datetime_str):
        return "N/A"
    
    try:
        months = {
            '01': 'January', '02': 'February', '03': 'March', '04': 'April',
            '05': 'May', '06': 'June', '07': 'July', '08': 'August',
            '09': 'September', '10': 'October', '11': 'November', '12': 'December'
        }
        
        def add_ordinal_suffix(day):
            day_int = int(day)
            if 10 <= day_int <= 13:
                return f"{day_int}th"
            elif day_int % 10 == 1:
                return f"{day_int}st"
            elif day_int % 10 == 2:
                return f"{day_int}nd"
            elif day_int % 10 == 3:
                return f"{day_int}rd"
            else:
                return f"{day_int}th"
        
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2}):(\d{2})', datetime_str)
        if match:
            year, month, day, hour, minute, second = match.groups()
            month_name = months.get(month, f"Month{month}")
            day_ordinal = add_ordinal_suffix(int(day))
            return f"{month_name} {day_ordinal} at {hour}:{minute} UTC"
        
        return datetime_str[:25]
    except:
        return "N/A"

@st.cache_data(ttl=7200)  # Cache for 2 hours
def get_storms_for_basin_year(basin_name, year):
    """Get list of storms for a specific basin and year."""
    try:
        year_page_url = f"https://ncics.org/ibtracs/index.php?name=YearBasin-{year}"
        
        response = requests.get(year_page_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        basin_config = BASINS[basin_name]
        search_terms = basin_config["search_terms"]
        
        storms = []
        
        # Find all storm links
        for link in soup.find_all('a', href=True):
            if 'name=v04r01-' in link['href']:
                storm_text = link.text.strip()
                link_url = urljoin(year_page_url, link['href'])
                
                # Check if storm belongs to the selected basin
                # This is a simplified check - in reality, we'd need to parse the storm data
                # For now, we'll include all storms and let users filter
                if storm_text and len(storm_text) > 0:
                    # Extract storm name (usually after the basin code)
                    storm_name = storm_text.split()[-1] if ' ' in storm_text else storm_text
                    storms.append({
                        'display_name': storm_text,
                        'storm_name': storm_name,
                        'url': link_url
                    })
        
        return storms
        
    except Exception as e:
        st.error(f"Error fetching storms for {basin_name} {year}: {e}")
        return []

@st.cache_data(ttl=3600)
def extract_storm_data(storm_url):
    """Extract and process storm track data from IBTrACS."""
    try:
        response = requests.get(storm_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Locate the data table
        data_table = None
        for table in soup.find_all('table'):
            header_row = table.find('tr')
            if header_row:
                header_text = header_row.get_text().lower()
                if all(x in header_text for x in ['lat', 'lon', 'wind']):
                    data_table = table
                    break
        
        if not data_table:
            raise ValueError("Could not find storm data table")
        
        # Parse table headers
        headers = [th.get_text().strip() for th in data_table.find('tr').find_all(['th', 'td'])]
        
        # Find column indices
        column_indices = {}
        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'lat' in header_lower and 'lat' not in column_indices:
                column_indices['lat'] = i
            elif 'lon' in header_lower and 'lon' not in column_indices:
                column_indices['lon'] = i
            elif 'usa wind' in header_lower:
                column_indices['wind'] = i
            elif any(p in header_lower for p in ['pressure', 'pres', 'slp', 'mslp']):
                column_indices['pressure'] = i
            elif 'iso_time' in header_lower or 'time' in header_lower:
                column_indices['time'] = i
        
        if 'lat' not in column_indices or 'lon' not in column_indices:
            raise ValueError("Required LAT/LON columns not found")
        
        # Extract data rows
        storm_data = []
        current_date = None
        
        for row in data_table.find_all('tr')[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            max_col = max(column_indices.values())
            
            if len(cells) > max_col:
                try:
                    lat = float(cells[column_indices['lat']].get_text().strip())
                    lon = float(cells[column_indices['lon']].get_text().strip())
                    
                    wind = np.nan
                    if 'wind' in column_indices:
                        wind_text = cells[column_indices['wind']].get_text().strip()
                        if wind_text and wind_text not in ['-', '']:
                            try:
                                wind = float(wind_text)
                            except:
                                wind = np.nan
                    
                    pressure = np.nan
                    if 'pressure' in column_indices:
                        pressure_text = cells[column_indices['pressure']].get_text().strip()
                        if pressure_text and pressure_text not in ['-', '']:
                            try:
                                pressure = float(pressure_text)
                            except:
                                pressure = np.nan
                    
                    full_datetime = None
                    if 'time' in column_indices:
                        time_text = cells[column_indices['time']].get_text().strip()
                        
                        if re.match(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}', time_text):
                            current_date = time_text[:10]
                            full_datetime = time_text
                        elif re.match(r'\d{2}:\d{2}:\d{2}', time_text) and current_date:
                            full_datetime = f"{current_date} {time_text}"
                        else:
                            full_datetime = time_text
                    
                    # Filter for 6-hour intervals
                    is_6hour_interval = True
                    if full_datetime:
                        hour_match = re.search(r'(\d{2}):\d{2}:\d{2}', full_datetime)
                        if hour_match:
                            hour = int(hour_match.group(1))
                            is_6hour_interval = hour in [0, 6, 12, 18]
                    
                    if is_6hour_interval:
                        storm_data.append({
                            'lat': lat,
                            'lon': lon,
                            'wind': wind,
                            'pressure': pressure,
                            'datetime': full_datetime
                        })
                        
                except (ValueError, IndexError):
                    continue
        
        if not storm_data:
            raise ValueError("No valid storm data found")
        
        return pd.DataFrame(storm_data)
        
    except Exception as e:
        raise ValueError(f"Error extracting storm data: {e}")

def create_storm_plot(storm_data, storm_name, year, basin_name):
    """Create the storm track visualization for Streamlit."""
    
    # Calculate geographic bounds
    lat_min, lat_max = storm_data['lat'].min(), storm_data['lat'].max()
    lon_min, lon_max = storm_data['lon'].min(), storm_data['lon'].max()
    
    # Add padding
    lat_range = lat_max - lat_min
    lon_range = lon_max - lon_min
    padding = max(lat_range, lon_range) * 0.25
    
    map_bounds = {
        'llcrnrlon': lon_min - padding,
        'llcrnrlat': lat_min - padding,
        'urcrnrlon': lon_max + padding,
        'urcrnrlat': lat_max + padding
    }
    
    # Determine storm type
    lat_center = (lat_min + lat_max) / 2
    lon_center = (lon_min + lon_max) / 2
    storm_type = determine_storm_type(lat_center, lon_center)
    
    # Create figure and basemap
    fig, ax = plt.subplots(figsize=(16, 11))
    
    basemap = Basemap(
        projection='cyl',
        resolution='i',
        **map_bounds,
        ax=ax
    )
    
    # Add shaded relief background
    basemap.shadedrelief(scale=0.5)
    
    # Add geographic features
    basemap.drawcoastlines(linewidth=1.5, color='white')
    basemap.drawcountries(linewidth=1.0, color='white')
    
    # Add coordinate grid
    parallels = np.arange(-90, 90, 5)
    meridians = np.arange(-180, 180, 5)
    basemap.drawparallels(parallels, labels=[1,0,0,0], fontsize=9, color='white')
    basemap.drawmeridians(meridians, labels=[0,0,0,1], fontsize=9, color='white')
    
    # Convert coordinates to map projection
    track_x, track_y = basemap(storm_data['lon'].values, storm_data['lat'].values)
    
    # Plot storm track line
    basemap.plot(track_x, track_y, color='white', linewidth=5, alpha=0.9, zorder=10)
    basemap.plot(track_x, track_y, color='black', linewidth=3, alpha=0.9, zorder=11)
    
    # Plot intensity points
    has_wind_data = not storm_data['wind'].isna().all()
    categories_list = []
    
    for idx, point in storm_data.iterrows():
        if has_wind_data and not pd.isna(point['wind']):
            color, category = get_intensity_color(point['wind'])
        else:
            color, category = 'No Data'
        categories_list.append(category)
        
        x, y = basemap(point['lon'], point['lat'])
        ax.scatter(x, y, c=color, s=70, edgecolors='black', 
                   linewidth=1.8, zorder=12, alpha=0.95)
    
    # Add start and end markers
    start_x, start_y = basemap(storm_data.iloc[0]['lon'], storm_data.iloc[0]['lat'])
    end_x, end_y = basemap(storm_data.iloc[-1]['lon'], storm_data.iloc[-1]['lat'])
    
    ax.scatter(start_x, start_y, marker='s', s=180, c='lime', 
               edgecolors='black', linewidth=2.5, zorder=15)
    ax.scatter(end_x, end_y, marker='s', s=180, c='red', 
               edgecolors='black', linewidth=2.5, zorder=15)
    
    # Smart positioning for annotations
    start_time = format_datetime(storm_data.iloc[0]['datetime'])
    end_time = format_datetime(storm_data.iloc[-1]['datetime'])
    
    # Calculate safe positioning for annotations
    if len(storm_data) > 1:
        start_dx = track_x[1] - track_x[0]
        start_dy = track_y[1] - track_y[0]
        track_length = np.sqrt(start_dx**2 + start_dy**2)
        if track_length > 0:
            perp_x = -start_dy / track_length * 60
            perp_y = start_dx / track_length * 60
            start_offset = (perp_x + 50, perp_y + 20)
        else:
            start_offset = (60, 30)
        
        end_dx = track_x[-1] - track_x[-2]
        end_dy = track_y[-1] - track_y[-2]
        track_length = np.sqrt(end_dx**2 + end_dy**2)
        if track_length > 0:
            perp_x = -end_dy / track_length * 60
            perp_y = end_dx / track_length * 60
            end_offset = (perp_x + 50, perp_y - 20)
        else:
            end_offset = (60, -30)
    else:
        start_offset = (60, 30)
        end_offset = (60, -30)
    
    # Add annotations
    ax.annotate(f'Start: {start_time}', xy=(start_x, start_y), xytext=start_offset,
                textcoords='offset points', 
                bbox=dict(boxstyle='round,pad=0.4', facecolor='lime', alpha=0.85),
                fontsize=10, weight='bold', zorder=20,
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.1', 
                              color='darkgreen', lw=2))
    
    ax.annotate(f'End: {end_time}', xy=(end_x, end_y), xytext=end_offset,
                textcoords='offset points',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='red', alpha=0.85),
                fontsize=10, weight='bold', zorder=20,
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.1', 
                              color='darkred', lw=2))
    
    # Create intensity legend
    if has_wind_data:
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='white', markersize=8, 
                      markeredgecolor='black', label='TD (<34 kt)', linewidth=0),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#F5F5DC', markersize=8, 
                      markeredgecolor='black', label='TS (34-63 kt)', linewidth=0),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FFCC5C', markersize=8, 
                      markeredgecolor='black', label='Cat 1 (64-82 kt)', linewidth=0),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF8C00', markersize=8, 
                      markeredgecolor='black', label='Cat 2 (83-95 kt)', linewidth=0),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF0000', markersize=8, 
                      markeredgecolor='black', label='Cat 3 (96-112 kt)', linewidth=0),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#8B008B', markersize=8, 
                      markeredgecolor='black', label='Cat 4 (113-136 kt)', linewidth=0),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#000000', markersize=8, 
                      markeredgecolor='black', label='Cat 5 (137+ kt)', linewidth=0),
        ]
    else:
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='white', markersize=8, 
                      markeredgecolor='black', label='No Wind Data', linewidth=0),
        ]
    
    legend = ax.legend(handles=legend_elements, loc='upper left', 
                      bbox_to_anchor=(0.02, 0.97), fontsize=9,
                      fancybox=True, shadow=True, framealpha=0.92)
    legend.get_frame().set_facecolor('white')
    
    # Calculate statistics
    max_wind = storm_data['wind'].max() if has_wind_data else np.nan
    max_wind_mph = convert_knots_to_mph(max_wind)
    min_pressure = storm_data['pressure'].min() if not storm_data['pressure'].isna().all() else np.nan
    ace_value = calculate_ace_value(storm_data['wind']) if has_wind_data else 0
    
    # Add info boxes
    intensity_info = ""
    if not pd.isna(max_wind):
        intensity_info += f"Max Winds: {max_wind:.0f}kt ({max_wind_mph}mph)\n"
    else:
        intensity_info += "Max Winds: N/A\n"
    
    if not pd.isna(min_pressure):
        intensity_info += f"Min Pressure: {min_pressure:.0f}mb"
    else:
        intensity_info += "Min Pressure: N/A"
    
    ax.text(0.98, 0.02, intensity_info, transform=ax.transAxes,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.9),
            fontsize=10, weight='bold', ha='right', va='bottom')
    
    ace_info = f"ACE: {ace_value:.1f}" if ace_value > 0 else "ACE: N/A"
    ax.text(0.98, 0.98, ace_info, transform=ax.transAxes,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.9),
            fontsize=10, weight='bold', ha='right', va='top')
    
    # Set title
    ax.set_title(f'{storm_type} {storm_name} ({year})', 
                fontsize=20, fontweight='bold', pad=25)
    
    plt.tight_layout()
    
    return fig, {
        'storm_type': storm_type,
        'max_wind': max_wind,
        'max_wind_mph': max_wind_mph,
        'min_pressure': min_pressure,
        'ace_value': ace_value,
        'track_points': len(storm_data),
        'duration_hours': len(storm_data) * 6,
        'duration_days': len(storm_data) * 6 / 24,
        'lat_extent': (lat_min, lat_max),
        'lon_extent': (lon_min, lon_max),
        'categories': categories_list
    }

def main():
    """Main Streamlit application."""
    
    # Title and description
    st.title("🌀 Tropical Cyclone Track Plotter")
    st.markdown("*Interactive visualization of historical tropical cyclone tracks from IBTrACS*")
    
    # Sidebar for controls
    st.sidebar.header("Select Storm Parameters")
    
    # Basin selection
    selected_basin = st.sidebar.selectbox(
        "🌊 Select Basin:",
        list(BASINS.keys()),
        help="Choose the oceanic basin where the storm occurred"
    )
    
    # Year selection
    current_year = 2024
    selected_year = st.sidebar.selectbox(
        "📅 Select Year:",
        range(current_year, 1841, -1),  # IBTrACS goes back to 1842
        help="Choose the year when the storm occurred"
    )
    
    # Storm selection (only show after basin and year are selected)
    if selected_basin and selected_year:
        with st.spinner(f"Loading storms for {selected_basin} {selected_year}..."):
            storms = get_storms_for_basin_year(selected_basin, selected_year)
        
        if storms:
            storm_options = {storm['display_name']: storm for storm in storms}
            
            selected_storm_display = st.sidebar.selectbox(
                "🌀 Select Storm:",
                [""] + list(storm_options.keys()),
                help="Choose the specific storm to visualize"
            )
            
            # Generate plot button
            if selected_storm_display and st.sidebar.button("🚀 Generate Storm Track Plot", type="primary"):
                selected_storm = storm_options[selected_storm_display]
                
                try:
                    with st.spinner(f"Generating plot for {selected_storm['storm_name']}..."):
                        # Extract storm data
                        storm_data = extract_storm_data(selected_storm['url'])
                        
                        # Create plot
                        fig, stats = create_storm_plot(
                            storm_data, 
                            selected_storm['storm_name'], 
                            selected_year, 
                            selected_basin
                        )
                        
                        # Display plot
                        st.pyplot(fig)
                        plt.close(fig)  # Prevent memory leaks
                        
                        # Display statistics
                        st.subheader(f"📊 {stats['storm_type']} {selected_storm['storm_name']} ({selected_year}) Statistics")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Duration", f"{stats['duration_days']:.1f} days")
                            st.metric("Track Points", f"{stats['track_points']}")
                        
                        with col2:
                            if not pd.isna(stats['max_wind']):
                                st.metric("Peak Winds", f"{stats['max_wind']:.0f} kt")
                                st.metric("Peak Winds (mph)", f"{stats['max_wind_mph']} mph")
                            else:
                                st.metric("Peak Winds", "N/A")
                        
                        with col3:
                            if not pd.isna(stats['min_pressure']):
                                st.metric("Min Pressure", f"{stats['min_pressure']:.0f} mb")
                            else:
                                st.metric("Min Pressure", "N/A")
                            
                            if stats['ace_value'] > 0:
                                st.metric("ACE Value", f"{stats['ace_value']:.1f}")
                            else:
                                st.metric("ACE Value", "N/A")
                        
                        with col4:
                            lat_min, lat_max = stats['lat_extent']
                            lon_min, lon_max = stats['lon_extent']
                            st.metric("Latitude Range", f"{lat_min:.1f}°N to {lat_max:.1f}°N")
                            st.metric("Longitude Range", f"{lon_min:.1f}°E to {lon_max:.1f}°E")
                        
                        # Intensity breakdown
                        if stats['categories']:
                            st.subheader("🎯 Intensity Distribution")
                            cat_counts = pd.Series(stats['categories']).value_counts()
                            
                            intensity_data = []
                            for cat in ['TD', 'TS', 'Cat1', 'Cat2', 'Cat3', 'Cat4', 'Cat5']:
                                if cat in cat_counts:
                                    intensity_data.append({
                                        'Category': cat,
                                        'Points': cat_counts[cat],
                                        'Hours': cat_counts[cat] * 6
                                    })
                            
                            if intensity_data:
                                st.dataframe(pd.DataFrame(intensity_data), use_container_width=True)
                        
                except Exception as e:
                    st.error(f"Error generating plot: {e}")
                    st.info("Please try a different storm or check your internet connection.")
        
        else:
            st.sidebar.warning(f"No storms found for {selected_basin} in {selected_year}")
    
    # Information section
    st.markdown("---")
    st.subheader("ℹ️ About This Application")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Features:**
        - 🌍 Interactive basin and year selection
        - 🌀 Comprehensive storm database from IBTrACS
        - 🗺️ High-resolution shaded relief backgrounds
        - 📊 Detailed storm statistics and intensity analysis
        - 🎨 Color-coded intensity visualization using Saffir-Simpson scale
        """)
    
    with col2:
        st.markdown("""
        **Data Source:**
        - International Best Track Archive for Climate Stewardship (IBTrACS)
        - 6-hour interval storm positions
        - Wind speeds, pressures, and track coordinates
        - Historical data from 1842 to present
        """)
    
    st.markdown("""
    **Basin Coverage:**
    - 🌊 Atlantic (NATL) - Hurricanes
    - 🌊 East/Central Pacific (EPAC/CPAC) - Hurricanes  
    - 🌊 West Pacific (WPAC) - Typhoons
    - 🌊 Northern Indian Ocean (NIO) - Cyclones
    - 🌊 Southern Indian Ocean (SIO) - Cyclones
    - 🌊 Australian Region (AUSW/AUSE) - Cyclones
    """)

if __name__ == "__main__":
    main()