import os
import sys
from pymongo import MongoClient

MONGODB_URL = "mongodb+srv://parthpatil1234p_db_user:yY1gc2ePEj9PVvcc@cluster0.splvogw.mongodb.net/?retryWrites=true&w=majority"
DATABASES = ["dermascan_ai", "dermascan"]

def delete_demo_products():
    client = MongoClient(MONGODB_URL)
    
    for db_name in DATABASES:
        db = client[db_name]
        products_col = db["products"]
        
        total_before = products_col.count_documents({})
        demo_count = products_col.count_documents({
            "$or": [
                {"is_demo_product": True},
                {"data_type": "demo_synthetic"},
                {"brand_id": {"$in": ["BRD-DEMO", "BRD-CLEARKIND", "BRD-BARRIERWORKS", "BRD-SUNWISE"]}}
            ]
        })
        
        print(f"[{db_name}] Total products before: {total_before}, Demo products found: {demo_count}")
        
        if demo_count > 0:
            result = products_col.delete_many({
                "$or": [
                    {"is_demo_product": True},
                    {"data_type": "demo_synthetic"},
                    {"brand_id": {"$in": ["BRD-DEMO", "BRD-CLEARKIND", "BRD-BARRIERWORKS", "BRD-SUNWISE"]}}
                ]
            })
            print(f"[{db_name}] Successfully deleted {result.deleted_count} demo products.")
        else:
            print(f"[{db_name}] No demo products found to delete.")
            
        total_after = products_col.count_documents({})
        real_count = products_col.count_documents({"is_demo_product": False})
        print(f"[{db_name}] Total products remaining: {total_after} (Real verified: {real_count})\n")

    client.close()

if __name__ == "__main__":
    delete_demo_products()
