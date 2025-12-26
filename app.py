from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import re
from io import BytesIO

app = Flask(__name__)
CORS(app)  # Allow Bubble to call this API

def normalize_address(address, city, state, zip_code):
    """Create normalized match key for property matching"""
    parts = [str(x).lower() if pd.notna(x) else '' for x in [address, city, state, zip_code]]
    combined = ''.join(parts)
    normalized = re.sub(r'[^a-z0-9]', '', combined)
    return normalized

def clean_value(value):
    """Clean pandas values for JSON serialization"""
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
        return value.isoformat()
    if isinstance(value, (int, float)):
        return float(value) if not pd.isna(value) else None
    return str(value)

@app.route('/', methods=['GET'])
def home():
    """Welcome page"""
    return jsonify({
        'message': 'CRE Excel Parser API',
        'status': 'running',
        'endpoints': {
            '/health': 'Health check',
            '/parse-costar': 'Parse CoStar Excel files (POST)',
            '/parse-crexi': 'Parse CREXi Excel files (POST)'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'CRE Parser API'})

@app.route('/parse-costar', methods=['POST'])
def parse_costar():
    """Parse CoStar Excel export"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        df = pd.read_excel(BytesIO(file.read()))
        
        records = []
        for idx, row in df.iterrows():
            match_key = normalize_address(
                row.get('Address'),
                row.get('City'),
                row.get('State'),
                row.get('Zip')
            )
            
            record = {
                'match_key': match_key,
                'source': 'CoStar',
                'costar_property_id': clean_value(row.get('PropertyID')),
                'address': clean_value(row.get('Address')),
                'city': clean_value(row.get('City')),
                'state': clean_value(row.get('State')),
                'zip': clean_value(row.get('Zip')),
                'county': clean_value(row.get('County')),
                'latitude': clean_value(row.get('Latitude')),
                'longitude': clean_value(row.get('Longitude')),
                'property_name': clean_value(row.get('Name')),
                'property_type': clean_value(row.get('Property Type')),
                'property_status': clean_value(row.get('Sale Status')),
                'building_sf': clean_value(row.get('Size (SF)')),
                'land_sf': clean_value(row.get('Land Area (SF)')),
                'land_ac': clean_value(row.get('Land Area (AC)')),
                'number_of_units': clean_value(row.get('Number Of Units')),
                'year_built': clean_value(row.get('Built')),
                'building_class': clean_value(row.get('Building Class')),
                'sale_price': clean_value(row.get('Sale Price')),
                'price_per_sf': clean_value(row.get('Price/SF')),
                'price_per_unit': clean_value(row.get('Price Per Unit')),
                'price_per_ac': clean_value(row.get('Price Per AC Land')),
                'cap_rate': clean_value(row.get('Cap Rate')),
                'noi': clean_value(row.get('Net Income')),
                'listing_broker_company': clean_value(row.get('Listing Broker Company')),
                'listing_broker_agent_first': clean_value(row.get('Listing Broker Agent First Name')),
                'listing_broker_agent_last': clean_value(row.get('Listing Broker Agent Last Name')),
                'listing_broker_phone': clean_value(row.get('Listing Broker Phone')),
                'listing_broker_address': clean_value(row.get('Listing Broker Address')),
                'market': clean_value(row.get('Market')),
                'submarket': clean_value(row.get('Submarket')),
                'tenancy': clean_value(row.get('Tenancy')),
                'percent_leased': clean_value(row.get('Percent Leased')),
                'zoning': clean_value(row.get('Zoning')),
                'days_on_market': clean_value(row.get('Days On Market')),
            }
            
            records.append(record)
        
        return jsonify({
            'success': True,
            'record_count': len(records),
            'records': records
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/parse-crexi', methods=['POST'])
def parse_crexi():
    """Parse CREXi Excel export"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        df = pd.read_excel(BytesIO(file.read()), skiprows=1)
        
        # Fix column names
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
        
        records = []
        for idx, row in df.iterrows():
            match_key = normalize_address(
                row.get('Address'),
                row.get('City'),
                row.get('State'),
                row.get('Zip')
            )
            
            record = {
                'match_key': match_key,
                'source': 'CREXi',
                'crexi_property_link': clean_value(row.get('Property Link')),
                'address': clean_value(row.get('Address')),
                'city': clean_value(row.get('City')),
                'state': clean_value(row.get('State')),
                'zip': clean_value(row.get('Zip')),
                'latitude': clean_value(row.get('Latitude')),
                'longitude': clean_value(row.get('Longitude')),
                'property_name': clean_value(row.get('Property Name')),
                'property_type': clean_value(row.get('Type')),
                'property_status': clean_value(row.get('Property Status')),
                'building_sf': clean_value(row.get('SqFt')),
                'lot_size': clean_value(row.get('Lot Size')),
                'number_of_units': clean_value(row.get('Units')),
                'asking_price': clean_value(row.get('Asking Price')),
                'price_per_sf': clean_value(row.get('Price/SqFt')),
                'price_per_unit': clean_value(row.get('Price/Unit')),
                'price_per_ac': clean_value(row.get('Price/Acre')),
                'cap_rate': clean_value(row.get('Cap Rate')),
                'noi': clean_value(row.get('NOI')),
                'tenants': clean_value(row.get('Tenant(s)')),
                'opportunity_zone': clean_value(row.get('Opportunity Zone')) == 'Yes',
                'days_on_market': clean_value(row.get('Days on Market')),
            }
            
            records.append(record)
        
        return jsonify({
            'success': True,
            'record_count': len(records),
            'records': records
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
