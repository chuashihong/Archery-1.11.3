import pymongo
from pymongo.errors import ConnectionFailure

class MongoDBConnection:
    def __init__(self, host='localhost', port=27018, user=None, password=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.conn = None

    def get_connection(self, db_name='admin'):
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

            # List databases
            databases = self.conn.list_database_names()
            print("Databases available:", databases)

        except ConnectionFailure as e:
            print("Connection to MongoDB failed:", e)

        return self.conn

# Example usage
if __name__ == "__main__":
    # Replace with your actual credentials and connection details
    mongo_instance = MongoDBConnection(
        host='127.0.0.1',
        port=27018,
        user='admin',
        password='chuashihong3'  # Replace with your actual password
    )

    # Attempt to connect to the MongoDB instance
    connection = mongo_instance.get_connection('admin')

    # Close the connection when done
    if connection:
        connection.close()
