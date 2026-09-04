import json
import sqlite3
import os

DB_PATH = "airbnb.db"
JSON_PATH = "airbnb-listings.json"

def create_schema(conn):
    cursor = conn.cursor()
    
    # 1. HOST
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS HOST (
        id TEXT PRIMARY KEY,
        name TEXT,
        profile_image_url TEXT,
        is_superhost BOOLEAN,
        is_verified BOOLEAN,
        about TEXT,
        rating_average REAL,
        rating_count INTEGER,
        time_as_host_years INTEGER,
        time_as_host_months INTEGER
    )
    """)
    
    # 2. HOST_HIGHLIGHT
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS HOST_HIGHLIGHT (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host_id TEXT,
        highlight TEXT,
        FOREIGN KEY(host_id) REFERENCES HOST(id)
    )
    """)
    
    # 3. HOST_DETAIL
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS HOST_DETAIL (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        host_id TEXT,
        detail TEXT,
        FOREIGN KEY(host_id) REFERENCES HOST(id)
    )
    """)
    
    # 4. CO_HOST
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CO_HOST (
        id TEXT PRIMARY KEY,
        name TEXT,
        profile_picture_url TEXT
    )
    """)
    
    # 5. LISTING_CO_HOST
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_CO_HOST (
        listing_id TEXT,
        co_host_id TEXT,
        PRIMARY KEY(listing_id, co_host_id),
        FOREIGN KEY(listing_id) REFERENCES LISTING(id),
        FOREIGN KEY(co_host_id) REFERENCES CO_HOST(id)
    )
    """)
    
    # 6. LISTING
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING (
        id TEXT PRIMARY KEY,
        host_id TEXT,
        title TEXT,
        description TEXT,
        html_description TEXT,
        description_original_language TEXT,
        meta_description TEXT,
        seo_title TEXT,
        sharing_config_title TEXT,
        property_type TEXT,
        room_type TEXT,
        home_tier INTEGER,
        person_capacity INTEGER,
        thumbnail_url TEXT,
        url TEXT,
        android_link TEXT,
        ios_link TEXT,
        is_available BOOLEAN,
        language TEXT,
        sub_description_title TEXT,
        latitude REAL,
        longitude REAL,
        location_name TEXT,
        location_subtitle TEXT,
        brand_subtitle TEXT,
        has_golden_laurel BOOLEAN,
        check_in_date DATE,
        check_out_date DATE,
        crawled_at TIMESTAMP,
        FOREIGN KEY(host_id) REFERENCES HOST(id)
    )
    """)

    # 7. LISTING_SUB_DESCRIPTION
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_SUB_DESCRIPTION (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id TEXT,
        item_text TEXT,
        sort_order INTEGER,
        FOREIGN KEY(listing_id) REFERENCES LISTING(id)
    )
    """)

    # 8. LISTING_RATING
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_RATING (
        listing_id TEXT PRIMARY KEY,
        guest_satisfaction REAL,
        accuracy REAL,
        cleanliness REAL,
        checking REAL,
        communication REAL,
        location REAL,
        value REAL,
        reviews_count INTEGER,
        FOREIGN KEY(listing_id) REFERENCES LISTING(id)
    )
    """)

    # 9. LISTING_PRICE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_PRICE (
        listing_id TEXT PRIMARY KEY,
        label TEXT,
        qualifier TEXT,
        price_amount TEXT,
        original_price TEXT,
        discounted_price TEXT,
        base_price_description TEXT,
        base_price_amount TEXT,
        service_fee TEXT,
        cleaning_fee TEXT,
        taxes_description TEXT,
        taxes_amount TEXT,
        special_offer_description TEXT,
        special_offer_amount TEXT,
        total_price_description TEXT,
        total_price_amount TEXT,
        total_before_taxes TEXT,
        early_bird_discount TEXT,
        FOREIGN KEY(listing_id) REFERENCES LISTING(id)
    )
    """)

    # 10. LISTING_IMAGE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_IMAGE (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id TEXT,
        image_url TEXT,
        caption TEXT,
        orientation TEXT,
        sort_order INTEGER,
        FOREIGN KEY(listing_id) REFERENCES LISTING(id)
    )
    """)

    # 11. LISTING_LOCATION_DESCRIPTION
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_LOCATION_DESCRIPTION (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id TEXT,
        title TEXT,
        content TEXT,
        FOREIGN KEY(listing_id) REFERENCES LISTING(id)
    )
    """)

    # 12. LISTING_BREADCRUMB
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_BREADCRUMB (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id TEXT,
        step_order INTEGER,
        link_route TEXT,
        link_text TEXT,
        search_text TEXT,
        FOREIGN KEY(listing_id) REFERENCES LISTING(id)
    )
    """)

    # 13. LISTING_HIGHLIGHT
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_HIGHLIGHT (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id TEXT,
        title TEXT,
        subtitle TEXT,
        icon TEXT,
        highlight_type TEXT,
        FOREIGN KEY(listing_id) REFERENCES LISTING(id)
    )
    """)

    # 14. LISTING_HOUSE_RULE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_HOUSE_RULE (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id TEXT,
        category TEXT,
        title TEXT,
        icon TEXT,
        additional_info TEXT,
        FOREIGN KEY(listing_id) REFERENCES LISTING(id)
    )
    """)

    # 15. CANCELLATION_POLICY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CANCELLATION_POLICY (
        id INTEGER PRIMARY KEY,
        policy_name TEXT
    )
    """)

    # 16. LISTING_CANCELLATION_POLICY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_CANCELLATION_POLICY (
        listing_id TEXT,
        cancellation_policy_id INTEGER,
        PRIMARY KEY(listing_id, cancellation_policy_id),
        FOREIGN KEY(listing_id) REFERENCES LISTING(id),
        FOREIGN KEY(cancellation_policy_id) REFERENCES CANCELLATION_POLICY(id)
    )
    """)

    # 17. AMENITY_CATEGORY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AMENITY_CATEGORY (
        id INTEGER PRIMARY KEY,
        name TEXT
    )
    """)

    # 18. AMENITY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AMENITY (
        id INTEGER PRIMARY KEY,
        category_id INTEGER,
        title TEXT,
        icon TEXT,
        FOREIGN KEY(category_id) REFERENCES AMENITY_CATEGORY(id)
    )
    """)

    # 19. LISTING_AMENITY
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LISTING_AMENITY (
        listing_id TEXT,
        amenity_id INTEGER,
        subtitle TEXT,
        is_available BOOLEAN,
        PRIMARY KEY(listing_id, amenity_id),
        FOREIGN KEY(listing_id) REFERENCES LISTING(id),
        FOREIGN KEY(amenity_id) REFERENCES AMENITY(id)
    )
    """)

    conn.commit()


def process_json(conn, json_path=JSON_PATH):
    if not os.path.exists(json_path):
        print(f"{json_path} not found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    cursor = conn.cursor()
    
    # We will use sets to avoid duplicate inserts for master tables
    hosts_seen = set()
    cohosts_seen = set()
    amenity_categories_seen = set()
    amenities_seen = set()
    cancellation_policies_seen = set()

    for item in data:
        listing_id = item.get('id')
        if not listing_id:
            continue
            
        host = item.get('host') or {}
        host_id = host.get('id')

        # 1. HOST
        if host_id and host_id not in hosts_seen:
            hosts_seen.add(host_id)
            time_as_host = host.get('timeAsHost') or {}
            cursor.execute("""
                INSERT OR IGNORE INTO HOST (id, name, profile_image_url, is_superhost, is_verified, about, rating_average, rating_count, time_as_host_years, time_as_host_months)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                host_id,
                host.get('name'),
                host.get('profileImage'),
                host.get('isSuperHost'),
                host.get('isVerified'),
                host.get('about'),
                host.get('ratingAverage'),
                host.get('ratingCount'),
                time_as_host.get('years'),
                time_as_host.get('months')
            ))
            
            # HOST_HIGHLIGHT
            for h in (host.get('highlights') or []):
                if h:
                    cursor.execute("INSERT INTO HOST_HIGHLIGHT (host_id, highlight) VALUES (?, ?)", (host_id, h))
            
            # HOST_DETAIL
            for d in (host.get('hostDetails') or []):
                if d:
                    cursor.execute("INSERT INTO HOST_DETAIL (host_id, detail) VALUES (?, ?)", (host_id, d))

        # 4 & 5. CO_HOST & LISTING_CO_HOST
        for ch in (item.get('coHosts') or []):
            ch_id = ch.get('id')
            if ch_id:
                if ch_id not in cohosts_seen:
                    cohosts_seen.add(ch_id)
                    cursor.execute("""
                        INSERT OR IGNORE INTO CO_HOST (id, name, profile_picture_url)
                        VALUES (?, ?, ?)
                    """, (ch_id, ch.get('name'), ch.get('profilePictureUrl')))
                
                cursor.execute("""
                    INSERT OR IGNORE INTO LISTING_CO_HOST (listing_id, co_host_id)
                    VALUES (?, ?)
                """, (listing_id, ch_id))

        # 6. LISTING
        coords = item.get('coordinates') or {}
        html_desc = (item.get('htmlDescription') or {}).get('htmlText')
        cursor.execute("""
            INSERT OR REPLACE INTO LISTING (
                id, host_id, title, description, html_description, description_original_language,
                meta_description, seo_title, sharing_config_title, property_type, room_type,
                home_tier, person_capacity, thumbnail_url, url, android_link, ios_link,
                is_available, location_name, location_subtitle, latitude, longitude
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            listing_id,
            host_id,
            item.get('title'),
            item.get('description'),
            html_desc,
            item.get('descriptionOriginalLanguage'),
            item.get('metaDescription'),
            item.get('seoTitle'),
            item.get('sharingConfigTitle'),
            item.get('propertyType'),
            item.get('roomType'),
            item.get('homeTier'),
            item.get('personCapacity'),
            item.get('thumbnail'),
            item.get('url'),
            item.get('androidLink'),
            item.get('iosLink'),
            item.get('isAvailable'),
            item.get('location'),
            item.get('locationSubtitle'),
            coords.get('latitude'),
            coords.get('longitude')
        ))

        # 7. LISTING_SUB_DESCRIPTION
        sub_desc = item.get('subDescription') or {}
        for i, text in enumerate(sub_desc.get('items') or []):
            cursor.execute("""
                INSERT INTO LISTING_SUB_DESCRIPTION (listing_id, item_text, sort_order)
                VALUES (?, ?, ?)
            """, (listing_id, text, i))

        # 8. LISTING_RATING
        rating = item.get('rating') or {}
        if rating:
            cursor.execute("""
                INSERT OR REPLACE INTO LISTING_RATING (
                    listing_id, guest_satisfaction, accuracy, cleanliness, checking,
                    communication, location, value, reviews_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                listing_id,
                rating.get('guestSatisfaction'),
                rating.get('accuracy'),
                rating.get('cleanliness'),
                rating.get('checking'),
                rating.get('communication'),
                rating.get('location'),
                rating.get('value'),
                rating.get('reviewsCount')
            ))

        # 9. LISTING_PRICE
        price = item.get('price') or {}
        if price:
            breakdown = price.get('breakDown') or {}
            base_price = breakdown.get('basePrice') or {}
            total = breakdown.get('total') or {}
            cursor.execute("""
                INSERT OR REPLACE INTO LISTING_PRICE (
                    listing_id, label, qualifier, price_amount, original_price,
                    discounted_price, base_price_description, base_price_amount, total_price_description, total_price_amount
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                listing_id,
                price.get('label'),
                price.get('qualifier'),
                price.get('price'),
                price.get('originalPrice'),
                price.get('discountedPrice'),
                base_price.get('description'),
                base_price.get('price'),
                total.get('description'),
                total.get('price')
            ))

        # 11. LISTING_LOCATION_DESCRIPTION
        for ld in (item.get('locationDescriptions') or []):
            cursor.execute("""
                INSERT INTO LISTING_LOCATION_DESCRIPTION (listing_id, title, content)
                VALUES (?, ?, ?)
            """, (listing_id, ld.get('title'), ld.get('content')))
            
        # The other fields (images, amenities, highlights, breadcrumb, rules, cancellation policies) 
        # might exist in the data structure, we map them similarly if they exist.
        for am_group in (item.get('amenities') or []):
            group_name = am_group.get('title')
            cat_id = abs(hash(group_name)) % (10 ** 8) if group_name else None # simple hash for id if missing
            
            if group_name and group_name not in amenity_categories_seen:
                amenity_categories_seen.add(group_name)
                cursor.execute("INSERT OR IGNORE INTO AMENITY_CATEGORY (id, name) VALUES (?, ?)", (cat_id, group_name))
                
            for am in (am_group.get('values') or []):
                am_title = am.get('title')
                if not am_title: continue
                am_id = abs(hash(am_title)) % (10 ** 8)
                if am_id not in amenities_seen:
                    amenities_seen.add(am_id)
                    cursor.execute("INSERT OR IGNORE INTO AMENITY (id, category_id, title, icon) VALUES (?, ?, ?, ?)", 
                                   (am_id, cat_id, am_title, am.get('icon')))
                cursor.execute("INSERT OR IGNORE INTO LISTING_AMENITY (listing_id, amenity_id, subtitle, is_available) VALUES (?, ?, ?, ?)",
                               (listing_id, am_id, am.get('subtitle'), am.get('available')))
                                   
        for hr in (item.get('houseRules') or []):
            if isinstance(hr, dict):
                cursor.execute("INSERT INTO LISTING_HOUSE_RULE (listing_id, category, title) VALUES (?, ?, ?)", 
                               (listing_id, hr.get('category'), hr.get('title')))
            else:
                cursor.execute("INSERT INTO LISTING_HOUSE_RULE (listing_id, title) VALUES (?, ?)", 
                               (listing_id, str(hr)))
                               
        for step_idx, bc in enumerate(item.get('breadcrumbs') or []):
            cursor.execute("""
                INSERT INTO LISTING_BREADCRUMB (listing_id, step_order, link_route, link_text, search_text)
                VALUES (?, ?, ?, ?, ?)
            """, (listing_id, step_idx + 1, bc.get('linkRoute'), bc.get('linkText'), bc.get('searchText')))
                           
        for img in (item.get('images') or []):
            cursor.execute("INSERT INTO LISTING_IMAGE (listing_id, image_url, caption, sort_order) VALUES (?, ?, ?, ?)",
                           (listing_id, img.get('url'), img.get('caption'), img.get('sortOrder')))
                           
        for hl in (item.get('highlights') or []):
            cursor.execute("INSERT INTO LISTING_HIGHLIGHT (listing_id, title, subtitle, icon) VALUES (?, ?, ?, ?)",
                           (listing_id, hl.get('title'), hl.get('subtitle'), hl.get('icon')))

        for pol in (item.get('cancellationPolicies') or []):
            pol_id = pol.get('policyId')
            if pol_id:
                if pol_id not in cancellation_policies_seen:
                    cancellation_policies_seen.add(pol_id)
                    cursor.execute("INSERT OR IGNORE INTO CANCELLATION_POLICY (id, policy_name) VALUES (?, ?)", (pol_id, pol.get('policyName')))
                cursor.execute("INSERT OR IGNORE INTO LISTING_CANCELLATION_POLICY (listing_id, cancellation_policy_id) VALUES (?, ?)", (listing_id, pol_id))
                
    conn.commit()

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    process_json(conn)
    conn.close()
    print("Database built successfully.")
