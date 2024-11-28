import pymongo
from pymongo.errors import ConnectionFailure
from collections import defaultdict
from bson import ObjectId
import json
class MongoDBConnection:
    def __init__(self, host='localhost', port=27018, user=None, password=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.conn = None

    def get_connection(self, db_name='admin'):
        """Establish a connection to MongoDB and authenticate."""
        try:
            print("Connecting to MongoDB with the following details:")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"User: {self.user}")
            print(f"Password: {'*' * len(self.password)}")
            print(f"Database: {db_name}")
            
            # Establish connection to MongoDB with authentication
            self.conn = pymongo.MongoClient(
                self.host,
                self.port,
                username=self.user,
                password=self.password,
                authSource=db_name,  # Authentication source
                connect=True,
                serverSelectionTimeoutMS=5000  # Timeout if unable to connect
            )

            # Attempt to list databases to ensure connection
            self.conn.server_info()  # Force a call to check if server is available
            print("Connected to MongoDB successfully!")

        except ConnectionFailure as e:
            print("Connection to MongoDB failed:", e)

        return self.conn
    def get_database_list(self):
        """Retrieve and print the list of databases, excluding system ones like 'config'."""
        if not self.conn:
            print("No connection found. Please connect first.")
            return []
        databases = [db for db in self.conn.list_database_names() if db not in ["admin", "config", "local"]]
        print("Databases available:", databases)
        return databases


    def get_collection_info(self, db_name):
        """Collect and display metadata information about collections in the given database."""
        if not self.conn:
            print("No connection found. Please connect first.")
            return None

        db = self.conn[db_name]
        collections_info = {}

        for collection_name in db.list_collection_names():
            print(f"\nCollecting info for collection: {collection_name} | {db_name}")
            collection = db[collection_name]

            # Get collection statistics
            stats = db.command("collStats", collection_name)
            print("collection:", collection, collection_name)
            storage_size = stats.get("storageSize")
            document_count = stats.get("count")
            avg_document_size = stats.get("avgObjSize")
            total_index_size = stats.get("totalIndexSize")

            # Index information
            indexes = list(collection.list_indexes())
            index_count = len(indexes)

            # Field metadata extraction
            field_metadata = defaultdict(set)  # Dictionary to collect field names and data types

            # Analyze a sample of documents for field metadata
            sample_documents = list(collection.find().limit(5))  # Limit to 5 documents for metadata analysis
            for doc in sample_documents:
                for field, value in doc.items():
                    field_metadata[field].add(type(value).__name__)  # Store the data type of each field

            # Format field metadata into a readable structure
            field_metadata_summary = {field: list(types) for field, types in field_metadata.items()}

            # Collection info dictionary
            collections_info[collection_name] = {
                "storage_size": storage_size,
                "document_count": document_count,
                "avg_document_size": avg_document_size,
                "index_count": index_count,
                "total_index_size": total_index_size,
                "field_metadata": field_metadata_summary,  # Store field metadata instead of raw documents
                "indexes": indexes
            }

            # Print collection insights
            print(f"Collection: {collection_name}")
            print(f"  Storage Size: {storage_size} bytes")
            print(f"  Document Count: {document_count}")
            print(f"  Average Document Size: {avg_document_size} bytes")
            print(f"  Index Count: {index_count}")
            print(f"  Total Index Size: {total_index_size} bytes")
            print(f"  Field Metadata: {json.dumps(field_metadata_summary, indent=2)}")
            print(f"  Indexes: {indexes}")

        return collections_info

    def close_connection(self):
        """Close the MongoDB connection."""
        if self.conn:
            self.conn.close()
            print("Connection closed.")
        else:
            print("No connection to close.")

# Example usage
if __name__ == "__main__":
    # Replace with your actual credentials and connection details
    mongo_instance = MongoDBConnection(
        host='127.0.0.1',
        port=27018,
        user='admin',
        password='password123'  # Replace with your actual password
    )

    # Attempt to connect to the MongoDB instance
    connection = mongo_instance.get_connection('admin')

    # Get database list if connected
    if connection:
        databases = mongo_instance.get_database_list()
        
        # Get collection information for each database
        for db_name in databases:
            print(f"\n--- Database: {db_name} ---")
            collection_info = mongo_instance.get_collection_info(db_name)

    # Close the connection when done
    mongo_instance.close_connection()
