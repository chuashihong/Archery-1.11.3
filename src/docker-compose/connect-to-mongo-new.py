import pymongo

class MongoDBConnection:
    def __init__(self, host='localhost', port=27018, user=None, password=None, instance=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.instance = instance  # This can hold the instance details like db_name if needed
        self.conn = None
        self.db_name = None

    def get_connection(self, db_name=None):
        # Set the database name (use provided db_name, instance's db_name, or default to 'admin')
        self.db_name = db_name or (self.instance.db_name if self.instance and hasattr(self.instance, 'db_name') else "admin")
        auth_db = self.db_name or "admin"

        # Establish connection to MongoDB with authentication directly in MongoClient
        self.conn = pymongo.MongoClient(
            self.host,
            self.port,
            username=self.user,
            password=self.password,
            authSource=auth_db,
            connect=True,
            connectTimeoutMS=10000,
        )

        return self.conn

# Example usage
if __name__ == "__main__":
    # Initialize MongoDBConnection (replace with your actual credentials and details)
    mongo_instance = MongoDBConnection(
        host='localhost',
        port=27018,
        user='admin',
        password='password123'
    )

    # Get connection to a specific database (or default to 'admin')
    connection = mongo_instance.get_connection('your_database')

    # Access a collection in the database
    db = connection['your_database']
    collection = db['your_collection']

    # Fetch a document as a test
    document = collection.find_one()

    print("Connected to MongoDB successfully!")
    print("Sample document:", document)
