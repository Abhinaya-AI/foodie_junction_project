# core/management/commands/populate_data.py
# Usage: python manage.py populate_data

from django.core.management.base import BaseCommand
from core.models import Restaurant, FoodItem
import random

RESTAURANTS = [
    # BANGALORE
    {'name':'Paradise Biryani','city':'bangalore','address':'Koramangala','rating':4.5,'num_ratings':2340,'distance_km':1.2,'is_pure_veg':False,'serves_alcohol':False,'cuisine_types':'Biryani, Hyderabadi, Mughlai','avg_cost_for_two':600,'delivery_time_min':35,'is_featured':True,'image_url':'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&q=80'},
    {'name':'Sagar Ratna','city':'bangalore','address':'Indiranagar','rating':4.3,'num_ratings':1890,'distance_km':2.4,'is_pure_veg':True,'serves_alcohol':False,'cuisine_types':'South Indian, Breakfast','avg_cost_for_two':300,'delivery_time_min':25,'is_featured':True,'image_url':'https://images.unsplash.com/photo-1630383249896-424e482df921?w=600&q=80'},
    {'name':'Barbeque Nation','city':'bangalore','address':'MG Road','rating':4.4,'num_ratings':3200,'distance_km':3.8,'is_pure_veg':False,'serves_alcohol':True,'cuisine_types':'BBQ, North Indian, Continental','avg_cost_for_two':1200,'delivery_time_min':40,'is_featured':False,'image_url':'https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80'},
    {'name':'Truffles','city':'bangalore','address':'St Marks Road','rating':4.6,'num_ratings':4100,'distance_km':2.1,'is_pure_veg':False,'serves_alcohol':True,'cuisine_types':'Burgers, American, Continental','avg_cost_for_two':700,'delivery_time_min':30,'is_featured':True,'image_url':'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&q=80'},
    # DELHI
    {'name':'Bukhara','city':'delhi','address':'Chanakyapuri','rating':4.8,'num_ratings':5600,'distance_km':4.2,'is_pure_veg':False,'serves_alcohol':True,'cuisine_types':'North Indian, Mughlai, Tandoor','avg_cost_for_two':4000,'delivery_time_min':50,'is_featured':True,'image_url':'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80'},
    {'name':'Paranthe Wali Gali','city':'delhi','address':'Chandni Chowk','rating':4.5,'num_ratings':3400,'distance_km':1.0,'is_pure_veg':True,'serves_alcohol':False,'cuisine_types':'Paratha, Street Food, North Indian','avg_cost_for_two':200,'delivery_time_min':20,'is_featured':True,'image_url':'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=600&q=80'},
    {'name':'Khan Chacha','city':'delhi','address':'Khan Market','rating':4.4,'num_ratings':1800,'distance_km':3.5,'is_pure_veg':False,'serves_alcohol':False,'cuisine_types':'Rolls, Kebabs, Street Food','avg_cost_for_two':400,'delivery_time_min':25,'is_featured':False,'image_url':'https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=600&q=80'},
    # HYDERABAD
    {'name':'Bawarchi Biryani','city':'hyderabad','address':'RTC Cross Roads','rating':4.6,'num_ratings':4800,'distance_km':1.5,'is_pure_veg':False,'serves_alcohol':False,'cuisine_types':'Biryani, Hyderabadi, Andhra','avg_cost_for_two':500,'delivery_time_min':30,'is_featured':True,'image_url':'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&q=80'},
    {'name':'Chutneys','city':'hyderabad','address':'Banjara Hills','rating':4.4,'num_ratings':2900,'distance_km':2.7,'is_pure_veg':True,'serves_alcohol':False,'cuisine_types':'South Indian, Breakfast, Andhra','avg_cost_for_two':350,'delivery_time_min':25,'is_featured':True,'image_url':'https://images.unsplash.com/photo-1630383249896-424e482df921?w=600&q=80'},
    # MUMBAI
    {'name':'Trishna','city':'mumbai','address':'Fort','rating':4.7,'num_ratings':6200,'distance_km':3.2,'is_pure_veg':False,'serves_alcohol':True,'cuisine_types':'Seafood, Coastal, Konkani','avg_cost_for_two':2500,'delivery_time_min':45,'is_featured':True,'image_url':'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=600&q=80'},
    {'name':'Sardar Pav Bhaji','city':'mumbai','address':'Tardeo','rating':4.5,'num_ratings':3800,'distance_km':1.8,'is_pure_veg':True,'serves_alcohol':False,'cuisine_types':'Street Food, Pav Bhaji, Mumbai Special','avg_cost_for_two':150,'delivery_time_min':20,'is_featured':True,'image_url':'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80'},
    # KOLKATA
    {'name':'Peter Cat','city':'kolkata','address':'Park Street','rating':4.5,'num_ratings':3500,'distance_km':2.0,'is_pure_veg':False,'serves_alcohol':True,'cuisine_types':'Continental, Chelo Kebab, European','avg_cost_for_two':1200,'delivery_time_min':40,'is_featured':True,'image_url':'https://images.unsplash.com/photo-1544025162-d76694265947?w=600&q=80'},
    {'name':'Kewpies Kitchen','city':'kolkata','address':'Elgin','rating':4.4,'num_ratings':1900,'distance_km':3.1,'is_pure_veg':False,'serves_alcohol':False,'cuisine_types':'Bengali, Traditional, Home Style','avg_cost_for_two':800,'delivery_time_min':35,'is_featured':False,'image_url':'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=600&q=80'},
]

FOOD_ITEMS = {
    'biryani': [
        {'name':'Hyderabadi Dum Biryani','price':249,'is_veg':False,'is_bestseller':True,'description':'Aromatic basmati rice with tender chicken in dum style','image_url':'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&q=80'},
        {'name':'Veg Dum Biryani','price':199,'is_veg':True,'is_bestseller':False,'description':'Fragrant rice with fresh vegetables and whole spices','image_url':'https://images.unsplash.com/photo-1596797038530-2c107229654b?w=400&q=80'},
        {'name':'Mutton Biryani','price':299,'is_veg':False,'is_bestseller':True,'description':'Slow-cooked mutton biryani with caramelized onions','image_url':'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&q=80'},
    ],
    'south_indian': [
        {'name':'Masala Dosa','price':89,'is_veg':True,'is_bestseller':True,'description':'Crispy dosa with spiced potato filling, sambar & chutneys','image_url':'https://images.unsplash.com/photo-1630383249896-424e482df921?w=400&q=80'},
        {'name':'Idli Sambar (4 pcs)','price':69,'is_veg':True,'is_bestseller':False,'description':'Steamed rice cakes with piping hot sambar','image_url':'https://images.unsplash.com/photo-1630383249896-424e482df921?w=400&q=80'},
        {'name':'Medu Vada (2 pcs)','price':75,'is_veg':True,'is_bestseller':False,'description':'Crispy lentil fritters with coconut chutney','image_url':'https://images.unsplash.com/photo-1630383249896-424e482df921?w=400&q=80'},
    ],
    'paratha': [
        {'name':'Aloo Paratha (2 pcs)','price':109,'is_veg':True,'is_bestseller':True,'description':'Whole wheat flatbread stuffed with spiced potato','image_url':'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=400&q=80'},
        {'name':'Paneer Paratha (2 pcs)','price':139,'is_veg':True,'is_bestseller':False,'description':'Flaky paratha stuffed with fresh cottage cheese','image_url':'https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=400&q=80'},
    ],
    'rolls': [
        {'name':'Chicken Kathi Roll','price':149,'is_veg':False,'is_bestseller':True,'description':'Crispy roti wrapped with spiced chicken tikka','image_url':'https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=400&q=80'},
        {'name':'Paneer Tikka Roll','price':129,'is_veg':True,'is_bestseller':True,'description':'Grilled paneer with veggies in crispy roti','image_url':'https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=400&q=80'},
        {'name':'Egg Roll','price':99,'is_veg':False,'is_bestseller':False,'description':'Classic egg roll with onions and green chutney','image_url':'https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=400&q=80'},
    ],
    'shakes': [
        {'name':'Mango Lassi','price':89,'is_veg':True,'is_bestseller':True,'description':'Thick and creamy mango yogurt drink','image_url':'https://images.unsplash.com/photo-1553361371-9b22f78e8b1d?w=400&q=80'},
        {'name':'Oreo Milkshake','price':129,'is_veg':True,'is_bestseller':True,'description':'Creamy milkshake blended with Oreo cookies','image_url':'https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400&q=80'},
        {'name':'Cold Coffee','price':99,'is_veg':True,'is_bestseller':False,'description':'Chilled blended coffee with ice cream','image_url':'https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400&q=80'},
    ],
}

class Command(BaseCommand):
    help = 'Populate sample data'
    def handle(self, *args, **kwargs):
        FoodItem.objects.all().delete()
        Restaurant.objects.all().delete()
        cats = list(FOOD_ITEMS.keys())
        for r_data in RESTAURANTS:
            r = Restaurant.objects.create(**r_data)
            cuisine = r_data['cuisine_types'].lower()
            assigned = [c for c in cats if c.replace('_',' ') in cuisine]
            if not assigned: assigned = random.sample(cats, 3)
            if 'shakes' not in assigned: assigned.append('shakes')
            for cat in assigned:
                for item in FOOD_ITEMS[cat]:
                    FoodItem.objects.create(restaurant=r, category=cat, **item)
        self.stdout.write(self.style.SUCCESS('✅ Data populated!'))