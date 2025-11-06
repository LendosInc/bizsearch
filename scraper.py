"""
BizBuySell Florida Scraper - TEST VERSION
Создаёт тестовые данные для проверки pipeline
"""

import json
import csv
from datetime import datetime

def create_test_data():
    """Создание тестовых данных"""
    print("🧪 ТЕСТОВЫЙ РЕЖИМ - Создание примерных данных")
    
    businesses = [
        {
            'id': 'test_1',
            'title': 'E-commerce Fashion Store (TEST DATA)',
            'description': 'Profitable online fashion retailer. This is test data to verify the pipeline works.',
            'price': 450000,
            'sde': 125000,
            'revenue': 850000,
            'multiplier': 6.8,
            'niche': 'E-commerce / Fashion',
            'location': 'Miami-Dade County, Florida',
            'county': 'Miami-Dade County',
            'county_id': 'miami-dade',
            'region': 'south_florida',
            'sourceUrl': 'https://www.bizbuysell.com/test-1',
            'source': 'BizBuySell',
            'foundDate': datetime.now().strftime('%Y-%m-%d'),
            'lastModified': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 'test_2',
            'title': 'SaaS Platform (TEST DATA)',
            'description': 'Cloud-based software with recurring revenue. This is test data.',
            'price': 1200000,
            'sde': 380000,
            'revenue': 720000,
            'multiplier': 1.9,
            'niche': 'SaaS / Software',
            'location': 'Orange County, Florida',
            'county': 'Orange County',
            'county_id': 'orange',
            'region': 'central_florida',
            'sourceUrl': 'https://www.bizbuysell.com/test-2',
            'source': 'BizBuySell',
            'foundDate': datetime.now().strftime('%Y-%m-%d'),
            'lastModified': datetime.now().strftime('%Y-%m-%d')
        },
        {
            'id': 'test_3',
            'title': 'Amazon FBA Business (TEST DATA)',
            'description': 'Profitable FBA business. This is test data.',
            'price': 280000,
            'sde': 150000,
            'revenue': 450000,
            'multiplier': 3.0,
            'niche': 'FBA / Amazon Business',
            'location': 'Broward County, Florida',
            'county': 'Broward County',
            'county_id': 'broward',
            'region': 'south_florida',
            'sourceUrl': 'https://www.bizbuysell.com/test-3',
            'source': 'BizBuySell',
            'foundDate': datetime.now().strftime('%Y-%m-%d'),
            'lastModified': datetime.now().strftime('%Y-%m-%d')
        }
    ]
    
    return businesses

def save_to_json(businesses, filename='bizbuysell_florida_data.json'):
    """Сохранение в JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(businesses, f, ensure_ascii=False, indent=2)
    print(f"✅ Сохранено в {filename}")

def save_to_csv(businesses, filename='bizbuysell_florida_data.csv'):
    """Сохранение в CSV"""
    keys = ['id', 'title', 'description', 'price', 'sde', 'revenue', 'multiplier',
            'niche', 'location', 'county', 'region', 'sourceUrl', 'source',
            'foundDate', 'lastModified']
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for business in businesses:
            row = {k: business.get(k, '') for k in keys}
            writer.writerow(row)
    
    print(f"✅ Сохранено в {filename}")

def main():
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║     BizBuySell Florida Scraper - TEST MODE            ║
    ║     Creating sample data to verify pipeline           ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    businesses = create_test_data()
    
    print(f"\n📊 Создано тестовых записей: {len(businesses)}")
    
    save_to_json(businesses)
    save_to_csv(businesses)
    
    print("\n✅ ГОТОВО!")
    print("📄 bizbuysell_florida_data.json")
    print("📄 bizbuysell_florida_data.csv")
    print("\n⚠️  Это тестовые данные!")
    print("   После проверки замените на реальный scraper.py")

if __name__ == "__main__":
    main()
