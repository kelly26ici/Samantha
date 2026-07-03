from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from src.configs.settings import QDRANT_URL, QDRANT_API_KEY

client=QdrantClient(
  url=QDRANT_URL,
  api_key=QDRANT_API_KEY
  )
  
def check_if_collection_exists(collection_name) -> bool:
  collections=client.get_collections().collections
  
  return any(collection.name == collection_name for collection in collections)
  
def make_collection(collection_name):
  if not check_if_collection_exists(collection_name):
    client.create_collection(
      collection_name=collection_name,
      vectors_config=VectorParams(
      size=1024,
      distance=Distance.COSINE,))
  
  return True
 
