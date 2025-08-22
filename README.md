# 🌀 Tropical Cyclone Track Plotter

An interactive web application for visualizing historical tropical cyclone tracks from the International Best Track Archive for Climate Stewardship (IBTrACS). Plot any storm from 1842 to present with detailed intensity analysis and beautiful shaded relief backgrounds.

![Tropical Cyclone Track Plotter](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c?style=for-the-badge&logo=python&logoColor=white)

## ✨ Features

### 🌍 Comprehensive Basin Coverage
- **Atlantic (NATL)** - Hurricanes affecting North America and Europe
- **East/Central Pacific (EPAC/CPAC)** - Eastern and Central Pacific hurricanes
- **West Pacific (WPAC)** - Western Pacific typhoons
- **Northern Indian Ocean (NIO)** - Bay of Bengal and Arabian Sea cyclones
- **Southern Indian Ocean (SIO)** - Southwest Indian Ocean cyclones
- **Australian Region (AUSW/AUSE)** - Australian and Southwest Pacific cyclones

### 📊 Detailed Storm Analysis
- **Saffir-Simpson Scale Visualization** - Color-coded intensity markers
- **6-Hour Interval Tracking** - Precise storm position plotting
- **ACE (Accumulated Cyclone Energy)** - Storm energy calculations
- **Peak Intensity Metrics** - Maximum winds and minimum pressure
- **Duration Analysis** - Complete storm lifecycle tracking
- **Geographic Extent** - Latitude/longitude boundaries

### 🗺️ Professional Cartography
- **High-Resolution Shaded Relief** - Detailed topographic backgrounds
- **Smart Annotation Positioning** - Non-overlapping start/end markers
- **Proper Map Projections** - Accurate geographic representation
- **Political Boundaries** - Country and coastline overlays
- **Coordinate Grids** - Latitude/longitude reference lines

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tropical-cyclone-tracker.git
   cd tropical-cyclone-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser**
   - Navigate to `http://localhost:8501`
   - The application will open automatically

## 🎯 How to Use

### Step 1: Select Basin
Choose from six major tropical cyclone basins worldwide:
- Atlantic (NATL)
- East/Central Pacific (EPAC/CPAC)
- West Pacific (WPAC)
- Northern Indian Ocean (NIO)
- Southern Indian Ocean (SIO)
- Australian Region (AUSW/AUSE)

### Step 2: Choose Year
Select any year from 1842 to present. The application supports the complete IBTrACS historical record.

### Step 3: Pick Storm
After selecting basin and year, the application automatically loads all available storms for that combination. Choose from the dropdown menu.

### Step 4: Generate Plot
Click "Generate Storm Track Plot" to create your visualization. The application will:
- Fetch storm data from IBTrACS
- Process track coordinates and intensity data
- Generate a professional-quality map
- Display comprehensive statistics

## 📈 Understanding the Visualizations

### Storm Track Elements
- **🟢 Green Square**: Storm formation location with start date/time
- **🔴 Red Square**: Storm dissipation location with end date/time
- **⚫ Black Line**: Storm track path
- **🎨 Colored Dots**: 6-hour position markers colored by intensity

### Intensity Color Scheme
- **⚪ White**: Tropical Depression (TD) - <34 kt
- **🟤 Beige**: Tropical Storm (TS) - 34-63 kt
- **🟡 Mango**: Category 1 - 64-82 kt
- **🟠 Orange**: Category 2 - 83-95 kt
- **🔴 Red**: Category 3 - 96-112 kt
- **🟣 Purple**: Category 4 - 113-136 kt
- **⚫ Black**: Category 5 - 137+ kt

### Statistics Panel
- **Duration**: Total storm lifetime in days
- **Track Points**: Number of 6-hour observations
- **Peak Winds**: Maximum sustained winds (knots and mph)
- **Min Pressure**: Lowest recorded pressure (millibars)
- **ACE Value**: Accumulated Cyclone Energy
- **Geographic Extent**: Latitude/longitude boundaries

## 🔧 Technical Details

### Data Source
The application uses the **International Best Track Archive for Climate Stewardship (IBTrACS)**, which provides:
- Standardized tropical cyclone data
- Global coverage from 1842 to present
- 6-hour interval observations
- Wind speeds, pressures, and positions
- Multiple agency best tracks

### Map Projections
- **Cylindrical Equidistant Projection** for global compatibility
- **Automatic bounds calculation** based on storm extent
- **Intelligent padding** for optimal visualization
- **High-resolution shaded relief** backgrounds

### Performance Optimizations
- **Streamlit caching** for storm lists and data
- **Efficient data processing** with pandas
- **Memory management** for large datasets
- **Error handling** for network requests

## 🌟 Example Storms to Try

### Legendary Atlantic Hurricanes
- **1992 Andrew** - Devastating Florida hurricane
- **2005 Katrina** - New Orleans catastrophe
- **2017 Harvey** - Houston flooding disaster
- **1935 Labor Day** - Strongest US landfall

### Powerful Pacific Typhoons
- **1979 Tip** - Largest tropical cyclone on record
- **2013 Haiyan** - Devastating Philippines typhoon
- **1961 Nancy** - Strongest typhoon on record
- **2019 Hagibis** - Japan Rugby World Cup typhoon

### Notable Indian Ocean Cyclones
- **1999 Orissa** - Deadliest Indian cyclone
- **2007 Gonu** - Strongest Arabian Sea cyclone
- **2019 Idai** - Mozambique disaster
- **2020 Amphan** - Recent Bay of Bengal super cyclone

## 🛠️ Development

### Project Structure
```
tropical-cyclone-tracker/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .gitignore         # Git ignore patterns
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Local Development
```bash
# Install in development mode
pip install -e .

# Run with debug mode
streamlit run app.py --logger.level=debug

# Clear cache
streamlit cache clear
```

## 📋 System Requirements

### Minimum Requirements
- **Python**: 3.8+
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB for dependencies
- **Internet**: Required for IBTrACS data access

### Recommended Setup
- **Python**: 3.10+
- **RAM**: 16GB for optimal performance
- **CPU**: Multi-core for faster processing
- **Browser**: Chrome, Firefox, or Safari (latest versions)

## 🐛 Troubleshooting

### Common Issues

**"No storms found for basin/year"**
- Check if the selected year has recorded storms in that basin
- Some early years may have limited data coverage

**Basemap installation problems**
- Try: `conda install -c conda-forge basemap`
- Alternative: `pip install basemap-data-hires`

**Slow loading times**
- First-time loads are slower due to data fetching
- Subsequent requests use Streamlit's caching system

**Plot display issues**
- Refresh the page if plots don't appear
- Check browser console for JavaScript errors

### Getting Help
- 📧 Open an issue on GitHub
- 📖 Check the IBTrACS documentation
- 🌐 Visit the Streamlit community forum

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **IBTrACS Team** - For maintaining the comprehensive storm database
- **NOAA/NCEI** - For hosting and providing access to the data
- **Streamlit Team** - For the excellent web application framework
- **Basemap Contributors** - For geographic visualization tools
- **Matplotlib Community** - For plotting capabilities

## 📊 Data Attribution

*Storm track data provided by the International Best Track Archive for Climate Stewardship (IBTrACS). Knapp, K. R., M. C. Kruk, D. H. Levinson, H. J. Diamond, and C. J. Neumann, 2010: The International Best Track Archive for Climate Stewardship (IBTrACS): Unifying tropical cyclone best track data. Bulletin of the American Meteorological Society, 91, 363-376.*

---

**Made with ❤️ by tropical cyclone enthusiasts**

*Visualizing nature's most powerful storms since 1842* 🌀