"""
BizBuySell Florida Scraper
Автоматический сбор объявлений о продаже бизнесов в Florida
"""

import asyncio
import json
import csv
from datetime import datetime
from playwright.async_api import async_playwright
import random

class BizBuySellFloridaScraper:
    def __init__(self):
        self.base_url = "https://www.bizbuysell.com"
        self.businesses = []
        
        # Список округов Florida по регионам (топ-20 по населению)
        self.counties = {
            "south_florida": [
                {"id": "miami-dade", "name": "Miami-Dade County", "population": 2716940},
                {"id": "broward", "name": "Broward County", "population": 1944375},
                {"id": "palm-beach", "name": "Palm Beach County", "population": 1496770},
                {"id": "collier", "name": "Collier County", "population": 384902},
                {"id": "lee", "name": "Lee County", "population": 760822},
                {"id": "monroe", "name": "Monroe County", "population": 82874}
            ],
            "central_florida": [
                {"id": "hillsborough", "name": "Hillsborough County", "population": 1459762},
                {"id": "orange", "name": "Orange County", "population": 1429908},
                {"id": "pinellas", "name": "Pinellas County", "population": 959107},
                {"id": "polk", "name": "Polk County", "population": 725046},
                {"id": "brevard", "name": "Brevard County", "population": 606612},
                {"id": "volusia", "name": "Volusia County", "population": 553543},
                {"id": "seminole", "name": "Seminole County", "population": 471826},
                {"id": "osceola", "name": "Osceola County", "population": 388656},
                {"id": "pasco", "name": "Pasco County", "population": 561891},
                {"id": "manatee", "name": "Manatee County", "population": 403253},
                {"id": "sarasota", "name": "Sarasota County", "population": 434006}
            ],
            "north_florida": [
                {"id": "duval", "name": "Duval County", "population": 995567},
                {"id": "leon", "name": "Leon County", "population": 293582},
                {"id": "st-johns", "name": "St. Johns County", "population": 273425}
            ]
        }
        
        # Конфигурация (загружается из config.json или используются defaults)
        self.config = {
            "selected_counties": [],
            "excluded_categories": [],
            "max_pages_per_county": 5
        }
        
    def load_config(self, config_file='scraper_config.json'):
        """Загрузка конфигурации из файла"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)
                print(f"✅ Конфигурация загружена из {config_file}")
                print(f"   Выбрано округов: {len(self.config['selected_counties'])}")
                print(f"   Исключено категорий: {len(self.config['excluded_categories'])}")
        except FileNotFoundError:
            print(f"⚠️  Файл {config_file} не найден, используются настройки по умолчанию")
    
    def save_config(self, config_file='scraper_config.json'):
        """Сохранение конфигурации"""
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        print(f"💾 Конфигурация сохранена в {config_file}")
    
    def get_all_counties(self):
        """Получить список всех округов"""
        all_counties = []
        for region, counties in self.counties.items():
            for county in counties:
                county['region'] = region
                all_counties.append(county)
        return all_counties
    
    async def scrape(self, headless=True):
        """
        Основная функция сбора данных
        
        Args:
            headless: True - браузер невидимый, False - видимый
        """
        if not self.config['selected_counties']:
            print("❌ Не выбраны округа для сканирования!")
            print("   Используйте метод set_counties() или создайте файл scraper_config.json")
            return []
        
        print(f"\n🚀 Запуск сбора данных с BizBuySell.com (Florida)")
        print(f"📍 Округов для сканирования: {len(self.config['selected_counties'])}")
        print(f"🎯 Исключено категорий: {len(self.config['excluded_categories'])}")
        print(f"🎭 Режим браузера: {'Невидимый' if headless else 'Видимый'}")
        print("-" * 70)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Сканирование каждого выбранного округа
            for county_id in self.config['selected_counties']:
                county_info = self.get_county_info(county_id)
                if not county_info:
                    print(f"⚠️  Округ {county_id} не найден в базе")
                    continue
                
                print(f"\n📖 Сканирование: {county_info['name']}")
                
                url = f"{self.base_url}/florida/{county_id}-county-businesses-for-sale/"
                
                try:
                    businesses = await self.scrape_county(page, url, county_info)
                    print(f"✅ Найдено объявлений: {len(businesses)}")
                    self.businesses.extend(businesses)
                    
                except Exception as e:
                    print(f"❌ Ошибка при сканировании {county_info['name']}: {str(e)}")
                    continue
            
            await browser.close()
        
        # Фильтрация по категориям
        if self.config['excluded_categories']:
            original_count = len(self.businesses)
            self.businesses = [
                b for b in self.businesses 
                if b.get('niche') not in self.config['excluded_categories']
            ]
            print(f"\n🔍 Отфильтровано: {original_count - len(self.businesses)} объявлений")
        
        # Вычисление множителя x для каждого бизнеса
        for business in self.businesses:
            business['multiplier'] = self.calculate_multiplier(
                business.get('revenue'), 
                business.get('sde')
            )
        
        print(f"\n✨ Сбор завершен! Всего собрано: {len(self.businesses)} объявлений")
        return self.businesses
    
    async def scrape_county(self, page, url, county_info):
        """Сканирование одного округа"""
        businesses = []
        
        for page_num in range(1, self.config['max_pages_per_county'] + 1):
            page_url = url if page_num == 1 else f"{url}?page={page_num}"
            
            try:
                await page.goto(page_url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))
                
                # Извлечение данных со страницы
                page_businesses = await self.extract_listings(page, county_info)
                
                if not page_businesses:
                    print(f"   📄 Страница {page_num}: объявления не найдены, останавливаемся")
                    break
                
                print(f"   📄 Страница {page_num}: {len(page_businesses)} объявлений")
                businesses.extend(page_businesses)
                
                # Проверка наличия следующей страницы
                has_next = await page.query_selector('a[rel="next"]')
                if not has_next:
                    break
                    
            except Exception as e:
                print(f"   ⚠️  Ошибка на странице {page_num}: {str(e)}")
                break
        
        return businesses
    
    async def extract_listings(self, page, county_info):
        """Извлечение списка объявлений со страницы"""
        businesses = []
        
        try:
            # Ждем загрузки контента
            await page.wait_for_selector('[class*="BusinessProfileCard"], [class*="listing"], article', timeout=10000)
            
            # Получаем все карточки объявлений
            listings = await page.query_selector_all('[class*="BusinessProfileCard"], article[class*="listing"]')
            
            for listing in listings:
                try:
                    business = await self.extract_business_data(listing, county_info)
                    if business and business.get('title'):
                        businesses.append(business)
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"   ⚠️  Не удалось найти объявления на странице: {str(e)}")
        
        return businesses
    
    async def extract_business_data(self, listing, county_info):
        """Извлечение данных из одной карточки объявления"""
        business = {
            'id': None,
            'title': None,
            'description': None,
            'price': None,
            'sde': None,
            'revenue': None,
            'niche': None,
            'location': f"{county_info['name']}, Florida",
            'county': county_info['name'],
            'county_id': county_info['id'],
            'region': county_info['region'],
            'sourceUrl': None,
            'source': 'BizBuySell',
            'foundDate': datetime.now().strftime('%Y-%m-%d'),
            'lastModified': datetime.now().strftime('%Y-%m-%d')
        }
        
        try:
            # Заголовок
            title_elem = await listing.query_selector('h2, h3, [class*="title"]')
            if title_elem:
                business['title'] = (await title_elem.text_content()).strip()
            
            # Описание
            desc_elem = await listing.query_selector('[class*="description"], [class*="summary"], p')
            if desc_elem:
                business['description'] = (await desc_elem.text_content()).strip()[:500]
            
            # Цена (Asking Price)
            price_elem = await listing.query_selector('[class*="price"], [class*="asking"]')
            if price_elem:
                price_text = await price_elem.text_content()
                business['price'] = self.extract_number(price_text)
            
            # Cash Flow / SDE
            sde_elem = await listing.query_selector('[class*="cash"], [class*="sde"], [class*="cashflow"]')
            if sde_elem:
                sde_text = await sde_elem.text_content()
                business['sde'] = self.extract_number(sde_text)
            
            # Revenue / Gross
            revenue_elem = await listing.query_selector('[class*="revenue"], [class*="gross"], [class*="sales"]')
            if revenue_elem:
                revenue_text = await revenue_elem.text_content()
                business['revenue'] = self.extract_number(revenue_text)
            
            # Категория
            category_elem = await listing.query_selector('[class*="category"], [class*="industry"], [class*="type"]')
            if category_elem:
                business['niche'] = (await category_elem.text_content()).strip()
            
            # Ссылка
            link_elem = await listing.query_selector('a[href]')
            if link_elem:
                href = await link_elem.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        business['sourceUrl'] = f"{self.base_url}{href}"
                    elif href.startswith('http'):
                        business['sourceUrl'] = href
            
            # ID из URL
            if business['sourceUrl']:
                business['id'] = business['sourceUrl'].split('/')[-1] or business['sourceUrl'].split('/')[-2]
            else:
                business['id'] = f"biz_{datetime.now().timestamp()}"
                
        except Exception as e:
            print(f"   ⚠️  Ошибка извлечения данных: {str(e)}")
        
        return business
    
    def extract_number(self, text):
        """Извлечение числа из текста"""
        if not text:
            return None
        
        import re
        # Удаляем $, запятые
        cleaned = text.replace('$', '').replace(',', '').strip()
        
        # Ищем число (может быть с K, M)
        match = re.search(r'(\d+(?:\.\d+)?)\s*([KM])?', cleaned, re.IGNORECASE)
        if match:
            number = float(match.group(1))
            suffix = match.group(2)
            
            if suffix:
                suffix = suffix.upper()
                if suffix == 'K':
                    number *= 1000
                elif suffix == 'M':
                    number *= 1000000
            
            return int(number)
        
        return None
    
    def calculate_multiplier(self, revenue, sde):
        """Вычисление множителя Revenue/SDE"""
        if revenue and sde and sde > 0:
            multiplier = revenue / sde
            return round(multiplier, 1)
        return None
    
    def get_county_info(self, county_id):
        """Получить информацию об округе по ID"""
        for region, counties in self.counties.items():
            for county in counties:
                if county['id'] == county_id:
                    return {**county, 'region': region}
        return None
    
    def set_counties(self, county_ids):
        """Установить список округов для сканирования"""
        self.config['selected_counties'] = county_ids
        print(f"✅ Выбрано округов: {len(county_ids)}")
    
    def set_excluded_categories(self, categories):
        """Установить список исключаемых категорий"""
        self.config['excluded_categories'] = categories
        print(f"✅ Исключено категорий: {len(categories)}")
    
    def save_to_json(self, filename='bizbuysell_florida_data.json'):
        """Сохранение в JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.businesses, f, ensure_ascii=False, indent=2)
        print(f"💾 Данные сохранены в {filename}")
    
    def save_to_csv(self, filename='bizbuysell_florida_data.csv'):
        """Сохранение в CSV"""
        if not self.businesses:
            print("⚠️  Нет данных для сохранения")
            return
        
        keys = ['id', 'title', 'description', 'price', 'sde', 'revenue', 'multiplier', 
                'niche', 'location', 'county', 'region', 'sourceUrl', 'source', 
                'foundDate', 'lastModified']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for business in self.businesses:
                row = {k: business.get(k, '') for k in keys}
                writer.writerow(row)
        
        print(f"💾 Данные сохранены в {filename}")
    
    def print_summary(self):
        """Вывод статистики"""
        if not self.businesses:
            print("📊 Нет данных для отображения")
            return
        
        print("\n" + "="*70)
        print("📊 СТАТИСТИКА СОБРАННЫХ ДАННЫХ")
        print("="*70)
        
        print(f"\n📈 Всего объявлений: {len(self.businesses)}")
        
        # По округам
        counties_stat = {}
        for b in self.businesses:
            county = b.get('county', 'Unknown')
            counties_stat[county] = counties_stat.get(county, 0) + 1
        
        print(f"\n📍 По округам:")
        for county, count in sorted(counties_stat.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {county}: {count} объявлений")
        
        # Средние показатели
        prices = [b['price'] for b in self.businesses if b['price']]
        if prices:
            avg_price = sum(prices) / len(prices)
            print(f"\n💰 Средняя цена: ${avg_price:,.0f}")
        
        sdes = [b['sde'] for b in self.businesses if b['sde']]
        if sdes:
            avg_sde = sum(sdes) / len(sdes)
            print(f"📊 Средний SDE: ${avg_sde:,.0f}")
        
        revenues = [b['revenue'] for b in self.businesses if b['revenue']]
        if revenues:
            avg_revenue = sum(revenues) / len(revenues)
            print(f"💵 Средний Revenue: ${avg_revenue:,.0f}")
        
        # Множители
        multipliers = [b['multiplier'] for b in self.businesses if b['multiplier']]
        if multipliers:
            avg_mult = sum(multipliers) / len(multipliers)
            print(f"📈 Средний множитель: x{avg_mult:.1f}")
        
        # Категории
        niches = {}
        for b in self.businesses:
            if b['niche']:
                niches[b['niche']] = niches.get(b['niche'], 0) + 1
        
        if niches:
            print(f"\n🏷️  Топ-5 категорий:")
            sorted_niches = sorted(niches.items(), key=lambda x: x[1], reverse=True)[:5]
            for niche, count in sorted_niches:
                print(f"   • {niche}: {count} объявлений")
        
        print("\n" + "="*70)


async def main():
    """Главная функция"""
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║     BizBuySell Florida - Автоматический Сборщик Данных    ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    scraper = BizBuySellFloridaScraper()
    
    # Попытка загрузить конфигурацию
    scraper.load_config()
    
    # Если конфигурация не загружена, используем пример
    if not scraper.config['selected_counties']:
        print("\n⚙️  Настройка по умолчанию:")
        print("   Используем топ-5 округов Florida\n")
        
        # Топ-5 округов по населению
        scraper.set_counties([
            'miami-dade',
            'broward', 
            'palm-beach',
            'hillsborough',
            'orange'
        ])
        
        # Пример исключаемых категорий
        scraper.set_excluded_categories([
            'Restaurant',
            'Retail'
        ])
        
        # Сохранение конфигурации для следующего раза
        scraper.save_config()
    
    # НАСТРОЙКИ
    MAX_PAGES_PER_COUNTY = 3  # Страниц на каждый округ
    HEADLESS = False  # True = невидимый, False = видимый браузер
    
    scraper.config['max_pages_per_county'] = MAX_PAGES_PER_COUNTY
    
    try:
        # Запуск сбора данных
        await scraper.scrape(headless=HEADLESS)
        
        # Вывод статистики
        scraper.print_summary()
        
        # Сохранение данных
        scraper.save_to_json()
        scraper.save_to_csv()
        
        print("\n✅ Готово! Проверьте файлы:")
        print("   📄 bizbuysell_florida_data.json")
        print("   📄 bizbuysell_florida_data.csv")
        print("   📄 scraper_config.json")
        
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
