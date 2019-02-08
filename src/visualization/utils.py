import pandas as pd

# https://imagecolorpicker.com/en lets you pull hex color values from AUDL website
# NOTE - first color is fill, second is outline, so second shouldn't be white
palette = {
    'Atlanta Hustle': ['#8D8D94', '#302E5F'],
    'Austin Sol': ['#B5482F', '#232D6D'],
    'Chicago Wildfire': ['#4C6787', '#EB6136'],
    'DC Breeze': ['#232D6D', '#B9272C'],
    'Dallas Roughnecks': ['#F9F9FC', '#17114C'],
    'Detroit Mechanix': ['#4D0D11', '#212219'],
    'Indianapolis AlleyCats': ['#00703C', '#151E19'],
    'Los Angeles Aviators': ['#A92C2C', '#3B3633'], #'#AA1220'
    'Madison Radicals': ['#003C6C', '#B2A92C'],
    'Minnesota Wind Chill': ['#ffffff', '#6F7E91'],
    'Montreal Royal': ['#C4682C', '#153158'],
    'Nashville NightWatch': ['#800000', '#000000'],
    'New York Empire': ['#72C54C', '#292527'],
    'Ottawa Outlaws': ['#95969A', '#A2D04B'],
    'Philadelphia Phoenix': ['#FB9109', '#A61208'],
    'Pittsburgh Thunderbirds': ['#493D41', '#FDB80A'],
    'Raleigh Flyers': ['#9A2B2C', '#0E4A68'],
    'San Diego Growlers': ['#626262', '#AA1220'],
    'San Francisco FlameThrowers': ['#ff6600', '#000000'],
    'San Jose Spiders': ['#FFC025', '#45454A'],
    'Seattle Cascades': ['#1C4986', '#0A223C'],
    'Tampa Bay Cannons': ['#CEC466', '#000000'],
    'Toronto Rush': ['#D0283A', '#3B3633'],
}

palette_df = pd.DataFrame.from_dict(palette, orient='index', columns=['color1', 'color2'])
palette_df.index.rename('team', inplace=True)
palette_df.reset_index(inplace=True)
