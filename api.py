import googlemaps
import pandas as pd
from datetime import datetime
import os

API_KEY = "Your Key"
gmaps = googlemaps.Client(key=API_KEY)

locations = [
    "Kaspar Schmauser Nürnberg",
    "Kaspar Schmauser Fürth",
    "Kaspar Schmauser Erlangen",
    "Kaspar Schmauser Leipzig",
    "Kaspar Schmauser Essen",
    "Kaspar Schmauser Berlin"
]

all_reviews = []

for place_name in locations:
    try:
        places_result = gmaps.places(query=place_name)
        if not places_result.get('results'):
            print(f"Keine Ergebnisse für {place_name}")
            continue

        place_id = places_result['results'][0]['place_id']
        place_details = gmaps.place(place_id=place_id, fields=['name', 'rating', 'reviews'])

        reviews = place_details['result'].get('reviews', [])
        for review in reviews:
            all_reviews.append({
                'location': place_name,
                'text': review['text'],
                'rating': review['rating'],
                'timestamp': datetime.fromtimestamp(review['time']),
                'author': review.get('author_name', 'Anonym')
            })
    except Exception as e:
        print(f"Fehler bei {place_name}: {str(e)}")

df_reviews = pd.DataFrame(all_reviews)
output_path = os.path.expanduser('/Users/andy/Develop/kasper-schmauser-poc/kaspar_schmauser_all_reviews.csv')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_reviews.to_csv(output_path, index=False)
print(f"Datei gespeichert unter: {output_path}")
print(df_reviews.head())
print(f"Gesamtanzahl der Bewertungen: {len(df_reviews)}")